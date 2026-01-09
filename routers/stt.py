from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional
import logging
import json

from database import get_db
from schemas.stt import STTResponse, STTMessageCreate
from schemas.message import MessageResponse
from services.stt import stt_service
from models.message import Message
import uuid
from datetime import datetime

router = APIRouter(prefix="/stt", tags=["STT (Speech-to-Text)"])
logger = logging.getLogger(__name__)

@router.websocket("/stream")
async def websocket_stt_stream(websocket: WebSocket):
    """
    실시간 음성 스트림을 텍스트로 변환합니다 (WebSocket).
    
    클라이언트는 음성 데이터를 바이너리로 전송하고,
    서버는 실시간으로 변환된 텍스트만 JSON으로 반환합니다.
    
    **메시지 형식:**
    - 클라이언트 → 서버: 바이너리 음성 데이터 (PCM 16kHz)
    - 서버 → 클라이언트: JSON {"text": "...", "is_final": false}
    
    **연결 예시 (JavaScript):**
    ```javascript
    const ws = new WebSocket('wss://journal.aws11.shop/stt/stream');
    
    // 음성 데이터 전송
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
          ws.send(event.data);
        };
        mediaRecorder.start(100); // 100ms마다 전송
      });
    
    // 변환된 텍스트만 수신 (답변 없음)
    ws.onmessage = (event) => {
      const result = JSON.parse(event.data);
      console.log(result.text); // 변환된 텍스트만
    };
    ```
    """
    await websocket.accept()
    logger.info("WebSocket STT 연결 시작")
    
    try:
        full_transcript = ""
        
        while True:
            # 클라이언트로부터 음성 데이터 수신
            audio_chunk = await websocket.receive_bytes()
            
            if len(audio_chunk) == 0:
                continue
            
            logger.debug(f"음성 청크 수신: {len(audio_chunk)} bytes")
            
            # 실시간 STT 변환만 수행 (답변 생성 없음)
            try:
                result = await stt_service.transcribe_audio(audio_chunk, "audio/pcm")
                
                if result["text"]:
                    full_transcript += result["text"] + " "
                    
                    # 변환된 텍스트만 전송
                    await websocket.send_json({
                        "text": result["text"],
                        "full_text": full_transcript.strip(),
                        "is_final": False
                    })
                    
            except Exception as e:
                logger.error(f"STT 처리 오류: {e}")
                await websocket.send_json({
                    "error": str(e),
                    "text": "",
                    "is_final": False
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket STT 연결 종료")
        if full_transcript:
            logger.info(f"최종 변환 텍스트: {full_transcript}")
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        await websocket.close()

@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="음성 파일 (wav, mp3, ogg 등)")
):
    """
    음성 파일을 텍스트로 변환합니다.
    
    - **audio**: 음성 파일 (최대 10MB)
    
    지원 형식: WAV, MP3, OGG, FLAC, M4A
    """
    # 파일 크기 제한 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    try:
        # 파일 읽기
        audio_data = await audio.read()
        
        if len(audio_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE / 1024 / 1024}MB까지 지원합니다."
            )
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")
        
        # Content-Type 결정
        content_type = audio.content_type or "audio/wav"
        
        logger.info(f"STT 요청: {audio.filename}, {len(audio_data)} bytes, {content_type}")
        
        # STT 변환
        result = await stt_service.transcribe_audio(audio_data, content_type)
        
        return STTResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT 변환 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe-and-save", response_model=MessageResponse)
async def transcribe_and_save_message(
    audio: UploadFile = File(..., description="음성 파일"),
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """
    음성 파일을 텍스트로 변환하고 메시지로 저장합니다.
    
    - **audio**: 음성 파일
    - **user_id**: 사용자 ID (쿼리 파라미터)
    
    변환된 텍스트가 자동으로 메시지로 저장됩니다.
    """
    try:
        # 파일 읽기
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")
        
        # Content-Type 결정
        content_type = audio.content_type or "audio/wav"
        
        logger.info(f"STT + 저장 요청: user_id={user_id}, {audio.filename}")
        
        # STT 변환
        result = await stt_service.transcribe_audio(audio_data, content_type)
        
        if not result["text"]:
            raise HTTPException(status_code=400, detail="음성을 인식할 수 없습니다.")
        
        # 메시지 저장
        new_message = Message(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=result["text"],
            created_at=datetime.utcnow()
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        logger.info(f"STT 메시지 저장 완료: {new_message.id}, confidence={result['confidence']}")
        
        return MessageResponse(
            id=new_message.id,
            user_id=new_message.user_id,
            content=new_message.content,
            created_at=new_message.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT + 저장 오류: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def stt_health_check():
    """STT 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "stt",
        "model": "amazon.nova-2-sonic-v1:0",
        "streaming": "enabled"
    }
