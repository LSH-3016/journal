from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)

from database import Base, engine
from routers import messages, history, summary, flow

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS 설정
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "journal-api"}

@app.get("/")
async def root():
    return {"message": "Journal API is running", "docs": "/docs"}

# 라우터 등록
app.include_router(messages.router)
app.include_router(history.router)
app.include_router(summary.router)
app.include_router(flow.router)