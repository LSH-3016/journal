from pydantic import BaseModel
from datetime import datetime
import uuid

class MessageCreate(BaseModel):
    user_id: str
    content: str

class MessageResponse(BaseModel):
    id: str  # UUID를 문자열로 반환
    user_id: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v)
        }

class MessageUpdate(BaseModel):
    content: str

class MessageContentResponse(BaseModel):
    contents: str