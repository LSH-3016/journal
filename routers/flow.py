from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional, Union
from uuid import UUID
import logging

from database import get_db
from models.history import History
from schemas.history import HistoryCreate
from services.flow import flow_service
from services.s3 import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["flow"])

class FlowRequest(BaseModel):
    user_id: str
    content: str
    record_date: date
    tags: list[str] = None
    s3_key: str = None  # 이미지 주소

class FlowResponse(BaseModel):
    type: str  # "data" | "answer"
    content: str
    message: Optional[str] = None
    history_id: Optional[Union[int, str]] = None  # UUID를 문자열로 받을 수 있도록 변경

@router.post("/process", response_model=FlowResponse)
def process_with_flow(request: FlowRequest, db: Session = Depends(get_db)):
    """
    Bedrock Flow를 사용하여 입력을 처리합니다.
    - 데이터인 경우: DB와 S3에 저장
    - 질문인 경우: 답변만 반환 (저장하지 않음)
    """
    try:
        # Bedrock Flow 호출
        flow_result = flow_service.invoke_flow(request.content)
        
        if flow_result["node_name"] == "Data_return":
            # 데이터인 경우: 메시지로 DB에만 저장
            logger.info("데이터로 판단됨 - 메시지 저장")
            
            # 메시지 테이블에 저장 (S3 저장 없음)
            from models.message import Message
            
            db_message = Message(
                user_id=request.user_id,
                content=request.content
                # created_at은 자동으로 현재 시간이 설정됨
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            return FlowResponse(
                type="data",
                content=flow_result["content"],
                message="메시지가 저장되었습니다.",
                history_id=str(db_message.id)  # UUID를 문자열로 변환
            )
        
        elif flow_result["node_name"] == "Answer_return":
            # 질문인 경우: 답변만 반환 (저장하지 않음)
            logger.info("질문으로 판단됨 - 답변만 반환")
            
            return FlowResponse(
                type="answer",
                content=flow_result["content"],
                message="질문에 대한 답변입니다."
            )
        
        else:
            # 예상하지 못한 노드
            logger.warning(f"알 수 없는 노드: {flow_result['node_name']}")
            return FlowResponse(
                type="unknown",
                content=flow_result["content"],
                message="처리 결과를 확인할 수 없습니다."
            )
            
    except Exception as e:
        logger.error(f"Flow 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Flow 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/test")
def test_flow(content: str):
    """
    Flow 테스트용 엔드포인트
    """
    try:
        result = flow_service.invoke_flow(content)
        return {
            "input": content,
            "node_name": result["node_name"],
            "content": result["content"],
            "is_question": result["is_question"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))