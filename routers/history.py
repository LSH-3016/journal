from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging

from database import get_db
from models.history import History
from schemas.history import HistoryCreate, HistoryResponse
from services.s3 import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])

@router.post("", response_model=HistoryResponse)
def create_history(history: HistoryCreate, db: Session = Depends(get_db)):
    """
    새로운 기록을 저장하는 엔드포인트
    같은 날짜에 같은 사용자의 기록이 이미 있으면 덮어씁니다.
    DB와 S3에 동시에 저장됩니다.
    """
    # 같은 날짜, 같은 사용자의 기록이 있는지 확인
    existing_history = db.query(History).filter(
        History.user_id == history.user_id,
        History.record_date == history.record_date
    ).first()
    
    # S3에 저장
    try:
        text_url = s3_service.save_history_to_s3(
            user_id=history.user_id,
            content=history.content,
            record_date=history.record_date,
            tags=history.tags
        )
    except Exception as e:
        logger.error(f"S3 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"S3 저장 중 오류가 발생했습니다: {str(e)}")
    
    if existing_history:
        # 기존 기록이 있으면 업데이트 (덮어쓰기)
        existing_history.content = history.content
        existing_history.tags = history.tags
        existing_history.s3_key = history.s3_key  # 이미지 주소
        existing_history.text_url = text_url  # 텍스트 파일 URL
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
            s3_key=history.s3_key,  # 이미지 주소
            text_url=text_url  # 텍스트 파일 URL
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history

@router.get("/search", response_model=List[HistoryResponse])
def search_history(
    user_id: str,
    q: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    키워드로 기록을 검색하는 엔드포인트
    content 필드에서 키워드를 검색합니다.
    
    - user_id: 사용자 ID (필수)
    - q: 검색 키워드 (필수)
    - limit: 가져올 기록 수 (기본값: 100)
    - offset: 건너뛸 기록 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(History).filter(
        History.user_id == user_id,
        History.content.ilike(f"%{q}%")
    )
    
    history_records = query.order_by(History.record_date.desc()).offset(offset).limit(limit).all()
    return history_records

@router.get("/tags", response_model=List[HistoryResponse])
def search_by_tags(
    user_id: str,
    tags: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    태그로 기록을 검색하는 엔드포인트
    
    - user_id: 사용자 ID (필수)
    - tags: 태그 (쉼표로 구분, 예: "개발,학습") (필수)
    - limit: 가져올 기록 수 (기본값: 100)
    - offset: 건너뛸 기록 수 (페이지네이션용, 기본값: 0)
    """
    tag_list = [tag.strip() for tag in tags.split(",")]
    
    query = db.query(History).filter(
        History.user_id == user_id,
        History.tags.overlap(tag_list)
    )
    
    history_records = query.order_by(History.record_date.desc()).offset(offset).limit(limit).all()
    return history_records

@router.get("/date-range", response_model=List[HistoryResponse])
def get_by_date_range(
    user_id: str,
    start_date: date,
    end_date: date,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    날짜 범위로 기록을 조회하는 엔드포인트
    
    - user_id: 사용자 ID (필수)
    - start_date: 시작 날짜 (YYYY-MM-DD) (필수)
    - end_date: 종료 날짜 (YYYY-MM-DD) (필수)
    - limit: 가져올 기록 수 (기본값: 100)
    - offset: 건너뛸 기록 수 (페이지네이션용, 기본값: 0)
    """
    query = db.query(History).filter(
        History.user_id == user_id,
        History.record_date >= start_date,
        History.record_date <= end_date
    )
    
    history_records = query.order_by(History.record_date.desc()).offset(offset).limit(limit).all()
    return history_records

@router.get("/tags/list", response_model=dict)
def get_all_tags(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    사용자의 모든 태그 목록을 반환하는 엔드포인트
    
    - user_id: 사용자 ID (필수)
    
    Returns:
        {
            "user_id": "xxx",
            "tags": ["태그1", "태그2", ...],
            "count": 태그 개수
        }
    """
    # 사용자의 모든 히스토리 조회
    histories = db.query(History).filter(History.user_id == user_id).all()
    
    # 모든 태그 수집 (중복 제거)
    all_tags = set()
    for history in histories:
        if history.tags:
            all_tags.update(history.tags)
    
    # 정렬된 리스트로 변환
    sorted_tags = sorted(list(all_tags))
    
    return {
        "user_id": user_id,
        "tags": sorted_tags,
        "count": len(sorted_tags)
    }

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
    DB와 S3 파일을 모두 업데이트합니다.
    """
    db_history = db.query(History).filter(History.id == history_id).first()
    if not db_history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    
    # S3에 저장 (덮어쓰기)
    try:
        text_url = s3_service.save_history_to_s3(
            user_id=history.user_id,
            content=history.content,
            record_date=history.record_date,
            tags=history.tags
        )
    except Exception as e:
        logger.error(f"S3 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"S3 저장 중 오류가 발생했습니다: {str(e)}")
    
    # DB 업데이트
    db_history.user_id = history.user_id
    db_history.content = history.content
    db_history.record_date = history.record_date
    db_history.tags = history.tags
    db_history.s3_key = history.s3_key  # 이미지 주소
    db_history.text_url = text_url  # 텍스트 파일 URL
    
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

@router.get("/{history_id}/s3-content")
def get_history_s3_content(history_id: int, db: Session = Depends(get_db)):
    """
    S3에서 히스토리 파일 내용을 읽어오는 엔드포인트
    """
    history = db.query(History).filter(History.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    
    if not history.s3_key:
        raise HTTPException(status_code=404, detail="S3 파일이 없습니다")
    
    try:
        content = s3_service.get_history_from_s3(history.s3_key)
        return {"s3_key": history.s3_key, "content": content}
    except Exception as e:
        logger.error(f"S3 읽기 실패: {e}")
        raise HTTPException(status_code=500, detail=f"S3에서 파일을 읽는 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{history_id}")
def delete_history(history_id: int, db: Session = Depends(get_db)):
    """
    기록을 삭제하는 엔드포인트
    DB와 S3 파일을 모두 삭제합니다.
    """
    db_history = db.query(History).filter(History.id == history_id).first()
    if not db_history:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다")
    
    # S3 파일 삭제 (text_url이 있는 경우)
    if db_history.text_url:
        try:
            s3_key = s3_service.extract_s3_key_from_url(db_history.text_url)
            if s3_key:
                s3_service.delete_history_from_s3(s3_key)
                logger.info(f"S3 텍스트 파일 삭제 완료: {s3_key}")
        except Exception as e:
            logger.warning(f"S3 텍스트 파일 삭제 실패 (계속 진행): {e}")
    
    # S3 이미지 파일 삭제 (s3_key가 있는 경우)
    if db_history.s3_key:
        try:
            s3_key = s3_service.extract_s3_key_from_url(db_history.s3_key)
            if s3_key:
                s3_service.delete_history_from_s3(s3_key)
                logger.info(f"S3 이미지 파일 삭제 완료: {s3_key}")
        except Exception as e:
            logger.warning(f"S3 이미지 파일 삭제 실패 (계속 진행): {e}")
    
    # DB에서 삭제
    db.delete(db_history)
    db.commit()
    return {"message": "기록이 삭제되었습니다"}