from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class SummaryRequest(BaseModel):
    user_id: str
    s3_key: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="응답의 무작위성 (0.0 ~ 1.0)")

class SummaryResponse(BaseModel):
    summary: str
    message_count: int
    s3_key: Optional[str] = None

class SummaryExistsResponse(BaseModel):
    exists: bool
    id: int | None = None
    record_date: date | None = None
    summary: str | None = None
    s3_key: str | None = None