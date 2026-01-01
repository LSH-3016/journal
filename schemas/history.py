from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class HistoryCreate(BaseModel):
    user_id: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    s3_key: Optional[str] = None  # 이미지 주소
    text_url: Optional[str] = None  # 텍스트 파일 주소

class HistoryResponse(BaseModel):
    id: int
    user_id: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    s3_key: Optional[str] = None  # 이미지 주소
    text_url: Optional[str] = None  # 텍스트 파일 주소
    
    class Config:
        from_attributes = True