from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional, Union
from uuid import UUID
import logging

from database import get_db
from models.message import Message
from models.history import History
from services.agent_api import agent_api_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["agent"])

class AgentRequest(BaseModel):
    user_id: str
    content: str
    request_type: Optional[str] = None  # "summarize" | "question" | None (자동 판단)
    temperature: Optional[float] = None  # summarize용 temperature (0.0 ~ 1.0)
    record_date: Optional[date] = None
    tags: Optional[list[str]] = None
    s3_key: Optional[str] = None

class AgentResponse(BaseModel):
    type: str  # "data" | "answer" | "diary"
    content: str
    message: str
    history_id: Optional[Union[int, str]] = None

@router.post("/process", response_model=AgentResponse)
def process_with_agent(request: AgentRequest, db: Session = Depends(get_db)):
    """
    Agent API를 사용하여 입력을 처리합니다.
    - 데이터인 경우: Messages 테이블에 저장
    - 질문인 경우: 답변만 반환 (저장하지 않음)
    - 일기 생성인 경우: History 테이블에 저장
    
    Args:
        user_id: 사용자 ID
        content: 사용자 입력 내용
        request_type: 요청 타입 ("summarize", "question", None)
        temperature: summarize용 temperature (0.0 ~ 1.0)
        record_date: 기록 날짜 (일기 생성 시 사용)
        tags: 태그 목록
        s3_key: S3 이미지 키
    """
    try:
        # Agent API 호출
        # record_date가 있으면 사용, 없으면 오늘 날짜 사용
        current_date = request.record_date.strftime("%Y-%m-%d") if request.record_date else date.today().strftime("%Y-%m-%d")
        
        agent_result = agent_api_service.orchestrate_request(
            user_input=request.content,
            user_id=request.user_id,
            request_type=request.request_type,
            temperature=request.temperature,
            current_date=current_date
        )
        
        result_type = agent_result["type"]
        
        if result_type == "data":
            # 데이터인 경우: Messages 테이블에 저장
            logger.info("데이터로 판단됨 - 메시지 저장")
            
            db_message = Message(
                user_id=request.user_id,
                content=request.content
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            return AgentResponse(
                type="data",
                content="",
                message="메시지가 저장되었습니다.",
                history_id=str(db_message.id)
            )
        
        elif result_type == "answer":
            # 질문인 경우: 답변만 반환 (저장하지 않음)
            logger.info("질문으로 판단됨 - 답변만 반환")
            
            return AgentResponse(
                type="answer",
                content=agent_result["content"],
                message="질문에 대한 답변입니다."
            )
        
        elif result_type == "diary":
            # 일기 생성인 경우: History 테이블에 저장
            logger.info("일기 생성 - History 저장")
            
            # 날짜 설정 (없으면 오늘)
            target_date = request.record_date or date.today()
            
            # 기존 히스토리 확인
            existing_history = db.query(History).filter(
                History.user_id == request.user_id,
                History.record_date == target_date
            ).first()
            
            if existing_history:
                # 기존 기록 업데이트
                existing_history.content = agent_result["content"]
                if request.s3_key:
                    existing_history.s3_key = request.s3_key
                if request.tags:
                    existing_history.tags = request.tags
                history_id = existing_history.id
            else:
                # 새 기록 생성
                new_history = History(
                    user_id=request.user_id,
                    content=agent_result["content"],
                    record_date=target_date,
                    tags=request.tags,
                    s3_key=request.s3_key
                )
                db.add(new_history)
                db.commit()
                db.refresh(new_history)
                history_id = new_history.id
            
            db.commit()
            
            return AgentResponse(
                type="diary",
                content=agent_result["content"],
                message="일기가 생성되었습니다.",
                history_id=str(history_id)
            )
        
        else:
            # 예상하지 못한 타입
            logger.warning(f"알 수 없는 타입: {result_type}")
            return AgentResponse(
                type="unknown",
                content=agent_result.get("content", ""),
                message="처리 결과를 확인할 수 없습니다."
            )
            
    except Exception as e:
        logger.error(f"Agent 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/test")
def test_agent(
    content: str, 
    user_id: str = "test-user",
    request_type: Optional[str] = None,
    temperature: Optional[float] = None
):
    """
    Agent API 테스트용 엔드포인트
    """
    try:
        result = agent_api_service.orchestrate_request(
            user_input=content,
            user_id=user_id,
            request_type=request_type,
            temperature=temperature,
            current_date=date.today().strftime("%Y-%m-%d")
        )
        return {
            "input": content,
            "request_type": request_type,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
