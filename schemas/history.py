from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class HistoryCreate(BaseModel):
    user_id: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    s3_key: Optional[str] = None  # 문자열로 변경

class HistoryResponse(BaseModel):
    id: int
    user_id: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    s3_key: Optional[str] = None  # 문자열로 변경
    
    class Config:
        from_attributes = True