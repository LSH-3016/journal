from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timezone, timedelta
import uuid

from database import get_db
from models.message import Message
from schemas.message import MessageCreate, MessageResponse, MessageContentResponse, MessageUpdate

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/content", response_model=MessageContentResponse)
def get_messages_content_only(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    메시지의 content를 콤마로 구분된 한 줄 문자열로 반환하는 엔드포인트 (오늘 날짜만)
    
    - user_id: 특정 사용자의 메시지만 가져올 때 사용 (선택사항)
    - limit: 가져올 메시지 수 (기본값: 100)
    - offset: 건너뛸 메시지 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(Message)
    
    # 사용자별 필터링 (선택사항)
    if user_id:
        query = query.filter(Message.user_id == user_id)
    
    # 모든 메시지를 가져온 후 Python에서 날짜 필터링
    all_messages = query.order_by(Message.created_at.asc()).all()
    
    # 한국 시간대 (KST, UTC+9)
    kst = timezone(timedelta(hours=9))
    # 오늘 날짜 (한국 시간 기준)
    today = datetime.now(kst).date()
    
    # 오늘 날짜의 메시지만 필터링 (한국 시간 기준)
    today_messages = []
    for msg in all_messages:
        # timezone-aware로 변환
        if msg.created_at.tzinfo is None:
            msg_dt = msg.created_at.replace(tzinfo=timezone.utc)
        else:
            msg_dt = msg.created_at
        
        # 한국 시간으로 변환하여 날짜 비교
        msg_date_kst = msg_dt.astimezone(kst).date()
        if msg_date_kst == today:
            today_messages.append(msg)
    
    # 페이지네이션 적용
    paginated_messages = today_messages[offset:offset + limit]
    
    # 모든 content를 콤마로 구분하여 하나의 문자열로 합치기
    content_list = [msg.content for msg in paginated_messages]
    combined_contents = ", ".join(content_list)
    
    return MessageContentResponse(contents=combined_contents)

@router.get("", response_model=List[MessageResponse])
def get_messages(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    저장된 메시지를 가져오는 엔드포인트 (오늘 날짜만)
    
    - user_id: 특정 사용자의 메시지만 가져올 때 사용 (선택사항)
    - limit: 가져올 메시지 수 (기본값: 100)
    - offset: 건너뛸 메시지 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(Message)
    
    # 사용자별 필터링 (선택사항)
    if user_id:
        query = query.filter(Message.user_id == user_id)
    
    # 모든 메시지를 가져온 후 Python에서 날짜 필터링
    all_messages = query.order_by(Message.created_at.asc()).all()
    
    # 한국 시간대 (KST, UTC+9)
    kst = timezone(timedelta(hours=9))
    # 오늘 날짜 (한국 시간 기준)
    today = datetime.now(kst).date()
    
    # 오늘 날짜의 메시지만 필터링 (한국 시간 기준)
    today_messages = []
    for msg in all_messages:
        # timezone-aware로 변환
        if msg.created_at.tzinfo is None:
            msg_dt = msg.created_at.replace(tzinfo=timezone.utc)
        else:
            msg_dt = msg.created_at
        
        # 한국 시간으로 변환하여 날짜 비교
        msg_date_kst = msg_dt.astimezone(kst).date()
        if msg_date_kst == today:
            today_messages.append(msg)
    
    # 페이지네이션 적용
    paginated_messages = today_messages[offset:offset + limit]
    
    # UUID를 문자열로 변환
    return [
        MessageResponse(
            id=str(msg.id),
            user_id=msg.user_id,
            content=msg.content,
            created_at=msg.created_at
        )
        for msg in paginated_messages
    ]

@router.post("", response_model=MessageResponse)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """
    새로운 메시지를 저장하는 엔드포인트
    
    - user_id: 사용자 ID
    - content: 메시지 내용
    - created_at: 메시지 생성 시간 (선택사항, 기본값: 현재 시간)
    """
    db_message = Message(
        user_id=message.user_id,
        content=message.content
    )
    
    # created_at이 제공된 경우 설정
    if message.created_at:
        db_message.created_at = message.created_at
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # UUID를 문자열로 변환하여 반환
    return MessageResponse(
        id=str(db_message.id),
        user_id=db_message.user_id,
        content=db_message.content,
        created_at=db_message.created_at
    )

@router.get("/{message_id}", response_model=MessageResponse)
def get_message_by_id(message_id: str, db: Session = Depends(get_db)):
    """
    특정 ID의 메시지를 조회하는 엔드포인트
    """
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 UUID 형식입니다")
    
    message = db.query(Message).filter(Message.id == message_uuid).first()
    if not message:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다")
    
    return MessageResponse(
        id=str(message.id),
        user_id=message.user_id,
        content=message.content,
        created_at=message.created_at
    )

@router.put("/{message_id}", response_model=MessageResponse)
def update_message(message_id: str, message_update: MessageUpdate, db: Session = Depends(get_db)):
    """
    메시지를 수정하는 엔드포인트
    """
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 UUID 형식입니다")
    
    db_message = db.query(Message).filter(Message.id == message_uuid).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다")
    
    # content 업데이트
    db_message.content = message_update.content
    db.commit()
    db.refresh(db_message)
    
    return MessageResponse(
        id=str(db_message.id),
        user_id=db_message.user_id,
        content=db_message.content,
        created_at=db_message.created_at
    )

@router.delete("/{message_id}")
def delete_message(message_id: str, db: Session = Depends(get_db)):
    """
    메시지를 삭제하는 엔드포인트
    """
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 UUID 형식입니다")
    
    db_message = db.query(Message).filter(Message.id == message_uuid).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다")
    
    db.delete(db_message)
    db.commit()
    return {"message": "메시지가 삭제되었습니다"}