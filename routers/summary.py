from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone, timedelta
from typing import Optional
import re
import logging
import httpx

from database import get_db
from models.message import Message
from models.history import History
from schemas.summary import SummaryRequest, SummaryResponse, SummaryExistsResponse
from config import AGENT_API_URL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summary", tags=["summary"])

def _validate_user_id(user_id: str) -> None:
    """사용자 ID 형식 검증"""
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다")
    
    # 기본적인 형식 검증 (영문, 숫자, 언더스코어, 하이픈 허용 - UUID 지원)
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 형식입니다")

async def _get_user_messages_summary(
    user_id: str, 
    target_date: Optional[date], 
    s3_key: Optional[str],
    temperature: Optional[float],
    db: Session
) -> SummaryResponse:
    """공통 요약 로직 - Agent API 사용"""
    # 사용자 ID 검증
    _validate_user_id(user_id)
    
    # 날짜가 지정되지 않으면 오늘 날짜 사용
    if target_date is None:
        kst = timezone(timedelta(hours=9))
        target_date = datetime.now(kst).date()
    
    # 모든 메시지를 가져온 후 날짜 필터링
    all_messages = db.query(Message).filter(
        Message.user_id == user_id,
        Message.content.isnot(None),
        Message.content != ""
    ).order_by(Message.created_at.asc()).limit(1000).all()
    
    # 한국 시간대로 날짜 필터링
    kst = timezone(timedelta(hours=9))
    filtered_messages = []
    
    for msg in all_messages:
        # timezone-aware로 변환
        if msg.created_at.tzinfo is None:
            msg_dt = msg.created_at.replace(tzinfo=timezone.utc)
        else:
            msg_dt = msg.created_at
        
        # 한국 시간으로 변환하여 날짜 비교
        msg_date_kst = msg_dt.astimezone(kst).date()
        if msg_date_kst == target_date:
            filtered_messages.append(msg)
    
    if not filtered_messages:
        raise HTTPException(status_code=404, detail="요약할 메시지가 없습니다")
    
    # 빈 문자열 제거 및 더 자연스러운 구분자 사용
    content_list = [msg.content.strip() for msg in filtered_messages if msg.content and msg.content.strip()]
    
    if not content_list:
        raise HTTPException(status_code=404, detail="유효한 메시지 내용이 없습니다")
    
    # 개행으로 구분하여 더 자연스럽게 결합
    combined_content = "\n\n".join(content_list)
    
    try:
        # Agent API 서비스로 요약 요청 전송
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{AGENT_API_URL}/agent/summarize",
                json={
                    "content": combined_content,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            agent_result = response.json()
        
        logger.info(f"Agent API 응답: {agent_result}")
        
        # 응답 형식 확인 및 처리
        # 응답이 {"success": true, "summary": "..."} 형태인 경우
        if "success" in agent_result:
            if not agent_result.get("success"):
                error_msg = agent_result.get("error", "요약 생성에 실패했습니다")
                raise ValueError(error_msg)
            summary = agent_result.get("summary", "")
        # 응답이 {"summary": "..."} 형태인 경우
        elif "summary" in agent_result:
            summary = agent_result["summary"]
        # 응답이 {"response": "..."} 형태인 경우
        elif "response" in agent_result:
            summary = agent_result["response"]
        # 응답이 문자열인 경우
        elif isinstance(agent_result, str):
            summary = agent_result
        else:
            logger.error(f"예상하지 못한 응답 형식: {agent_result}")
            raise ValueError("Agent API 응답 형식이 올바르지 않습니다")
        
        if not summary or not summary.strip():
            raise ValueError("요약 내용이 비어있습니다")
        
        # History에 요약 저장 (같은 날짜가 있으면 업데이트)
        existing_history = db.query(History).filter(
            History.user_id == user_id,
            History.record_date == target_date
        ).first()
        
        if existing_history:
            # 기존 기록 업데이트
            existing_history.content = summary
            if s3_key:
                existing_history.s3_key = s3_key
        else:
            # 새 기록 생성
            new_history = History(
                user_id=user_id,
                content=summary,
                record_date=target_date,
                s3_key=s3_key
            )
            db.add(new_history)
        
        db.commit()
        
        return SummaryResponse(
            summary=summary,
            message_count=len(content_list),
            s3_key=s3_key
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Agent API 요청 실패 (HTTP {e.response.status_code}): {e.response.text}")
        raise HTTPException(status_code=502, detail=f"Agent API 요청 실패: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Agent API 연결 실패: {e}")
        raise HTTPException(status_code=503, detail="Agent API 서비스에 연결할 수 없습니다")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AI 요약 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"AI 요약 생성 실패: {str(e)}")

@router.post("", response_model=SummaryResponse)
async def create_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db)
):
    """
    사용자의 메시지들을 AI로 요약하는 엔드포인트 (POST 방식)
    
    - user_id: 요약할 사용자의 ID
    - s3_key: 업로드된 파일의 S3 키 (선택사항)
    - temperature: 응답의 무작위성 (0.0 ~ 1.0, 선택사항, 기본값: 0.7)
    """
    return await _get_user_messages_summary(
        request.user_id, 
        None, 
        request.s3_key, 
        request.temperature,
        db
    )

@router.get("/{user_id}", response_model=SummaryResponse)
async def get_summary(
    user_id: str,
    date: Optional[str] = Query(None, description="요약할 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)"),
    s3_key: Optional[str] = Query(None, description="업로드된 파일의 S3 키"),
    temperature: Optional[float] = Query(None, ge=0.0, le=1.0, description="응답의 무작위성 (0.0 ~ 1.0)"),
    db: Session = Depends(get_db)
):
    """
    사용자의 메시지들을 AI로 요약하는 엔드포인트 (GET 방식)
    
    - user_id: 요약할 사용자의 ID
    - date: 요약할 날짜 (선택사항, 기본값: 오늘)
    - s3_key: 업로드된 파일의 S3 키 (선택사항)
    - temperature: 응답의 무작위성 (0.0 ~ 1.0, 선택사항, 기본값: 0.7)
    """
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")
    
    return await _get_user_messages_summary(
        user_id, 
        target_date, 
        s3_key, 
        temperature,
        db
    )

@router.get("/check/{user_id}", response_model=SummaryExistsResponse)
async def check_today_summary_exists(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    오늘 날짜의 요약이 이미 존재하는지 확인하는 엔드포인트
    
    - user_id: 확인할 사용자의 ID
    
    Returns:
    - exists: 오늘 날짜의 요약 존재 여부
    - record_date: 요약 날짜 (존재하는 경우)
    - summary: 요약 내용 (존재하는 경우)
    """
    # 사용자 ID 검증
    _validate_user_id(user_id)
    
    # 오늘 날짜
    today = date.today()
    
    # 오늘 날짜의 요약 조회
    existing_summary = db.query(History).filter(
        History.user_id == user_id,
        History.record_date == today
    ).first()
    
    if existing_summary:
        return SummaryExistsResponse(
            exists=True,
            id=existing_summary.id,
            record_date=existing_summary.record_date,
            summary=existing_summary.content,
            s3_key=existing_summary.s3_key
        )
    else:
        return SummaryExistsResponse(
            exists=False,
            id=None,
            record_date=None,
            summary=None,
            s3_key=None
        )
