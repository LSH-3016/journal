from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
import re

from database import get_db
from models.message import Message
from models.history import History
from schemas.summary import SummaryRequest, SummaryResponse, SummaryExistsResponse
from services.bedrock import bedrock_service

router = APIRouter(prefix="/summary", tags=["summary"])

def _validate_user_id(user_id: str) -> None:
    """사용자 ID 형식 검증"""
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다")
    
    # 기본적인 형식 검증 (영문, 숫자, 언더스코어만 허용)
    if not re.match(r'^[a-zA-Z0-9_]+$', user_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 형식입니다")

async def _get_user_messages_summary(user_id: str, db: Session) -> SummaryResponse:
    """공통 요약 로직"""
    # 사용자 ID 검증
    _validate_user_id(user_id)
    
    # 빈 content 필터링과 함께 필요한 컬럼만 조회
    contents = db.query(Message.content).filter(
        Message.user_id == user_id,
        Message.content.isnot(None),
        Message.content != ""
    ).order_by(Message.created_at.asc()).limit(1000).all()  # 최대 1000개 제한
    
    if not contents:
        raise HTTPException(status_code=404, detail="요약할 메시지가 없습니다")
    
    # 빈 문자열 제거 및 더 자연스러운 구분자 사용
    content_list = [content[0].strip() for content in contents if content[0] and content[0].strip()]
    
    if not content_list:
        raise HTTPException(status_code=404, detail="유효한 메시지 내용이 없습니다")
    
    # 개행으로 구분하여 더 자연스럽게 결합
    combined_content = "\n\n".join(content_list)
    
    try:
        # Bedrock을 사용하여 요약 생성
        summary = await bedrock_service.summarize_content(combined_content)
        
        return SummaryResponse(
            summary=summary,
            message_count=len(content_list)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Bedrock 요약 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"AI 요약 생성 실패: {str(e)}")

@router.post("", response_model=SummaryResponse)
async def create_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db)
):
    """
    사용자의 메시지들을 AI로 요약하는 엔드포인트 (POST 방식)
    
    - user_id: 요약할 사용자의 ID
    """
    return await _get_user_messages_summary(request.user_id, db)

@router.get("/{user_id}", response_model=SummaryResponse)
async def get_summary(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    사용자의 메시지들을 AI로 요약하는 엔드포인트 (GET 방식)
    
    - user_id: 요약할 사용자의 ID
    """
    return await _get_user_messages_summary(user_id, db)

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
        History.username == user_id,
        History.record_date == today
    ).first()
    
    if existing_summary:
        return SummaryExistsResponse(
            exists=True,
            record_date=existing_summary.record_date,
            summary=existing_summary.content
        )
    else:
        return SummaryExistsResponse(
            exists=False,
            record_date=None,
            summary=None
        )