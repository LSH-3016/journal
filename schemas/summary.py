from pydantic import BaseModel
from datetime import date
from typing import Optional

class SummaryRequest(BaseModel):
    user_id: str
    s3_key: Optional[str] = None  # 문자열로 변경

class SummaryResponse(BaseModel):
    summary: str
    message_count: int
    s3_key: Optional[str] = None  # 문자열로 변경

class SummaryExistsResponse(BaseModel):
    exists: bool
    record_date: date | None = None
    summary: str | None = None
    s3_key: str | None = None  # 문자열로 변경