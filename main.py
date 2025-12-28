from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid

# .env 파일 로드
load_dotenv()

# 데이터베이스 설정
def get_database_url():
    # 전체 DATABASE_URL이 있으면 사용
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # 개별 환경변수로 구성
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    # 필수 환경변수 체크
    if not all([db_host, db_port, db_name, db_user, db_password]):
        raise ValueError(
            "데이터베이스 설정이 필요합니다. "
            ".env 파일에 DATABASE_URL 또는 개별 DB 환경변수들을 설정해주세요."
        )
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASE_URL = get_database_url()

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
    # 연결 테스트
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"데이터베이스 연결 실패: {e}")
    print("환경변수 설정을 확인해주세요.")
    raise
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 메시지 모델 정의
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

# 테이블 생성
Base.metadata.create_all(bind=engine)

# Pydantic 모델
class MessageResponse(BaseModel):
    id: str  # UUID를 문자열로 반환
    user_id: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get("/messages", response_model=List[MessageResponse])
def get_messages(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    저장된 메시지를 가져오는 엔드포인트
    
    - user_id: 특정 사용자의 메시지만 가져올 때 사용 (선택사항)
    - limit: 가져올 메시지 수 (기본값: 100)
    - offset: 건너뛸 메시지 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(Message)
    
    # 사용자별 필터링 (선택사항)
    if user_id:
        query = query.filter(Message.user_id == user_id)
    
    messages = query.order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    return messages


# 메시지 생성용 Pydantic 모델
class MessageCreate(BaseModel):
    user_id: str
    content: str

@app.post("/messages", response_model=MessageResponse)
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
    return db_message

@app.get("/users/{user_id}/messages", response_model=List[MessageResponse])
def get_user_messages(
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 메시지만 가져오는 엔드포인트
    """
    messages = db.query(Message).filter(
        Message.user_id == user_id
    ).order_by(Message.created_at.asc()).offset(offset).limit(limit).all()
    
    return messages