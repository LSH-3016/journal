from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Date, BigInteger, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid

# .env 파일 로드
load_dotenv()

# 데이터베이스 설정
def get_database_url():
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    # 필수 환경변수 체크
    if not all([db_host, db_port, db_name, db_user, db_password]):
        raise ValueError(
            "데이터베이스 설정이 필요합니다. "
            ".env 파일에 DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD를 설정해주세요."
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

# History 모델 정의
class History(Base):
    __tablename__ = "history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    username = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=False)
    record_date = Column(Date, nullable=False)
    tags = Column(ARRAY(Text), nullable=True)

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
        json_encoders = {
            uuid.UUID: lambda v: str(v)
        }

class HistoryCreate(BaseModel):
    username: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None

class HistoryResponse(BaseModel):
    id: int
    username: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    
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

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (프로덕션에서는 특정 도메인만 허용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.get("/messages", response_model=List[MessageResponse])
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
    
    # UUID를 문자열로 변환하여 반환
    return MessageResponse(
        id=str(db_message.id),
        user_id=db_message.user_id,
        content=db_message.content,
        created_at=db_message.created_at
    )

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

@app.get("/messages/{message_id}", response_model=MessageResponse)
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

@app.delete("/messages/{message_id}")
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

# History API
@app.post("/history", response_model=HistoryResponse)
def create_history(history: HistoryCreate, db: Session = Depends(get_db)):
    """
    새로운 기록을 저장하는 엔드포인트
    """
    db_history = History(
        username=history.username,
        content=history.content,
        record_date=history.record_date,
        tags=history.tags
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

@app.get("/history", response_model=List[HistoryResponse])
def get_history(
    username: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tags: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    기록을 조회하는 엔드포인트
    
    - username: 특정 사용자의 기록만 조회 (선택사항)
    - start_date: 시작 날짜 (선택사항)
    - end_date: 종료 날짜 (선택사항)
    - tags: 태그로 필터링 (쉼표로 구분, 예: "개발,학습")
    - limit: 가져올 기록 수 (기본값: 100)
    - offset: 건너뛸 기록 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(History)
    
    if username:
        query = query.filter(History.username == username)
    
    if start_date:
        query = query.filter(History.record_date >= start_date)
    
    if end_date:
        query = query.filter(History.record_date <= end_date)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        query = query.filter(History.tags.overlap(tag_list))
    
    history_records = query.order_by(History.record_date.desc()).offset(offset).limit(limit).all()
    return history_records

@app.get("/history/{history_id}", response_model=HistoryResponse)
def get_history_by_id(history_id: int, db: Session = Depends(get_db)):
    """
    특정 ID의 기록을 조회하는 엔드포인트
    """
    history = db.query(History).filter(History.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    return history

@app.put("/history/{history_id}", response_model=HistoryResponse)
def update_history(history_id: int, history: HistoryCreate, db: Session = Depends(get_db)):
    """
    기록을 수정하는 엔드포인트
    """
    db_history = db.query(History).filter(History.id == history_id).first()
    if not db_history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    
    db_history.username = history.username
    db_history.content = history.content
    db_history.record_date = history.record_date
    db_history.tags = history.tags
    
    db.commit()
    db.refresh(db_history)
    return db_history

@app.delete("/history/{history_id}")
def delete_history(history_id: int, db: Session = Depends(get_db)):
    """
    기록을 삭제하는 엔드포인트
    """
    db_history = db.query(History).filter(History.id == history_id).first()
    if not db_history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    
    db.delete(db_history)
    db.commit()
    return {"message": "기록이 삭제되었습니다"}