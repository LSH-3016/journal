from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# .env 파일 로드 (로컬 개발용)
load_dotenv()

# config.py에서 설정 가져오기
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_database_url():
    # 필수 환경변수 체크
    if not all([DB_USER, DB_PASSWORD]):
        raise ValueError(
            "데이터베이스 인증 정보가 필요합니다. "
            "DB_USER, DB_PASSWORD 환경변수를 설정하거나 AWS Secrets Manager를 사용하세요."
        )
    
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # 연결 전에 ping으로 확인
)

logger.info(f"Database engine created for: {DB_HOST}:{DB_PORT}/{DB_NAME}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()