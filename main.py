from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# 전역 예외 핸들러 - 500 에러에도 CORS 헤더 포함
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
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