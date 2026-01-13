from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class SummaryRequest(BaseModel):
    user_id: str
    s3_key: Optional[str] = None  # 문자열로 변경
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="응답의 무작위성 (0.0 ~ 1.0)")
    top_k: Optional[int] = Field(None, ge=1, le=500, description="상위 K개 토큰에서 샘플링 (1 ~ 500)")

class SummaryResponse(BaseModel):
    summary: str
    message_count: int
    s3_key: Optional[str] = None  # 문자열로 변경

class SummaryExistsResponse(BaseModel):
    exists: bool
    id: int | None = None  # 히스토리 ID 추가
    record_date: date | None = None
    summary: str | None = None
    s3_key: str | None = None