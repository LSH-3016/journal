from pydantic import BaseModel, Field
from typing import Optional

class STTResponse(BaseModel):
    """STT 변환 응답"""
    text: str = Field(..., description="변환된 텍스트")
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)")
    language: str = Field(default="ko-KR", description="감지된 언어")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "안녕하세요, 오늘 날씨가 좋네요",
                "confidence": 0.95,
                "language": "ko-KR"
            }
        }

class STTMessageCreate(BaseModel):
    """STT 변환 후 메시지 생성"""
    user_id: str = Field(..., description="사용자 ID")
    audio_text: str = Field(..., description="변환된 텍스트")
    confidence: float = Field(..., description="변환 신뢰도")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "audio_text": "오늘 아침 7시에 기상했다",
                "confidence": 0.95
            }
        }
