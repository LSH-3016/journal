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

# 헬스체크 엔드포인트 (ALB health check용 - /journal prefix 포함)
@app.get("/journal/health")
async def health_check():
    return {"status": "healthy", "service": "journal-api"}

@app.get("/journal")
async def root():
    return {"message": "Journal API is running", "docs": "/journal/docs"}

# 라우터 등록 (모든 라우터에 /journal prefix 적용)
app.include_router(messages.router, prefix="/journal")
app.include_router(history.router, prefix="/journal")
app.include_router(summary.router, prefix="/journal")
app.include_router(flow.router, prefix="/journal")