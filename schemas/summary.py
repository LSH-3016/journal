from pydantic import BaseModel

class SummaryRequest(BaseModel):
    user_id: str

class SummaryResponse(BaseModel):
    summary: str
    message_count: int