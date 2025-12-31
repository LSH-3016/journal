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
    같은 날짜에 같은 사용자의 기록이 이미 있으면 덮어씁니다.
    """
    # 같은 날짜, 같은 사용자의 기록이 있는지 확인
    existing_history = db.query(History).filter(
        History.user_id == history.user_id,
        History.record_date == history.record_date
    ).first()
    
    if existing_history:
        # 기존 기록이 있으면 업데이트 (덮어쓰기)
        existing_history.content = history.content
        existing_history.tags = history.tags
        existing_history.s3_key = history.s3_key
        db.commit()
        db.refresh(existing_history)
        return existing_history
    else:
        # 기존 기록이 없으면 새로 생성
        db_history = History(
            user_id=history.user_id,
            content=history.content,
            record_date=history.record_date,
            tags=history.tags,
            s3_key=history.s3_key
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history

@router.get("", response_model=List[HistoryResponse])
def get_history(
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tags: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    기록을 조회하는 엔드포인트
    
    - user_id: 특정 사용자의 기록만 조회 (선택사항)
    - start_date: 시작 날짜 (선택사항)
    - end_date: 종료 날짜 (선택사항)
    - tags: 태그로 필터링 (쉼표로 구분, 예: "개발,학습")
    - limit: 가져올 기록 수 (기본값: 100)
    - offset: 건너뛸 기록 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(History)
    
    if user_id:
        query = query.filter(History.user_id == user_id)
    
    if start_date:
        query = query.filter(History.record_date >= start_date)
    
    if end_date:
        query = query.filter(History.record_date <= end_date)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        query = query.filter(History.tags.overlap(tag_list))
    
    history_records = query.order_by(History.record_date.desc()).offset(offset).limit(limit).all()
    return history_records

@router.get("/check-s3-by-date", response_model=dict)
def check_s3_key_by_date(
    user_id: str,
    record_date: str,
    db: Session = Depends(get_db)
):
    """
    user_id와 record_date로 기록을 찾아 s3_key가 null인지 확인하는 엔드포인트
    record_date 형식: YYYY-MM-DD (예: 2025-12-31)
    """
    from datetime import datetime
    
    try:
        parsed_date = datetime.strptime(record_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")
    
    history = db.query(History).filter(
        History.user_id == user_id,
        History.record_date == parsed_date
    ).first()
    
    if not history:
        return {
            "found": False,
            "history_id": None,
            "has_s3_key": False,
            "s3_key": None
        }
    
    return {
        "found": True,
        "history_id": history.id,
        "has_s3_key": history.s3_key is not None,
        "s3_key": history.s3_key
    }

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
    
    db_history.user_id = history.user_id
    db_history.content = history.content
    db_history.record_date = history.record_date
    db_history.tags = history.tags
    db_history.s3_key = history.s3_key
    
    db.commit()
    db.refresh(db_history)
    return db_history

@router.get("/{history_id}/check-s3", response_model=dict)
def check_s3_key(history_id: int, db: Session = Depends(get_db)):
    """
    특정 기록의 s3_key가 null인지 확인하는 엔드포인트
    """
    history = db.query(History).filter(History.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    
    return {
        "history_id": history_id,
        "has_s3_key": history.s3_key is not None,
        "s3_key": history.s3_key
    }

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