from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models.message import Message
from schemas.message import MessageCreate, MessageResponse, MessageContentResponse

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/content", response_model=MessageContentResponse)
def get_messages_content_only(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    메시지의 content를 콤마로 구분된 한 줄 문자열로 반환하는 엔드포인트
    
    - user_id: 특정 사용자의 메시지만 가져올 때 사용 (선택사항)
    - limit: 가져올 메시지 수 (기본값: 100)
    - offset: 건너뛸 메시지 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(Message.content)
    
    # 사용자별 필터링 (선택사항)
    if user_id:
        query = query.filter(Message.user_id == user_id)
    
    contents = query.order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    
    # 모든 content를 콤마로 구분하여 하나의 문자열로 합치기
    content_list = [content[0] for content in contents]
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
    
    # 오늘 날짜 필터링
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    query = query.filter(Message.created_at >= today_start, Message.created_at <= today_end)
    
    # 사용자별 필터링 (선택사항)
    if user_id:
        query = query.filter(Message.user_id == user_id)
    
    messages = query.order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    
    # UUID를 문자열로 변환
    return [
        MessageResponse(
            id=str(msg.id),
            user_id=msg.user_id,
            content=msg.content,
            created_at=msg.created_at
        )
        for msg in messages
    ]

@router.post("", response_model=MessageResponse)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """
    새로운 메시지를 저장하는 엔드포인트
    """
    db_message = Message(
        user_id=message.user_id,
        content=message.content
    )
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