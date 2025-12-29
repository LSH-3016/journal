from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from models.history import History
from schemas.history import HistoryCreate, HistoryResponse

router = APIRouter(prefix="/history", tags=["history"])

@router.post("", response_model=HistoryResponse)
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

@router.get("", response_model=List[HistoryResponse])
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

@router.get("/{history_id}", response_model=HistoryResponse)
def get_history_by_id(history_id: int, db: Session = Depends(get_db)):
    """
    특정 ID의 기록을 조회하는 엔드포인트
    """
    history = db.query(History).filter(History.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    return history

@router.put("/{history_id}", response_model=HistoryResponse)
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

@router.delete("/{history_id}")
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