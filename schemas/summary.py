from pydantic import BaseModel
from datetime import date

class SummaryRequest(BaseModel):
    user_id: str

class SummaryResponse(BaseModel):
    summary: str
    message_count: int

class SummaryExistsResponse(BaseModel):
    exists: bool
    record_date: date | None = None
    summary: str | None = None