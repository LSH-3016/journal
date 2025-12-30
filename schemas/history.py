from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class HistoryCreate(BaseModel):
    username: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    file_url: Optional[str] = None

class HistoryResponse(BaseModel):
    id: int
    username: str
    content: str
    record_date: date
    tags: Optional[List[str]] = None
    file_url: Optional[str] = None
    
    class Config:
        from_attributes = True