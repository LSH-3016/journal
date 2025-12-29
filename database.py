from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

def get_database_url():
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    # 필수 환경변수 체크
    if not all([db_host, db_port, db_name, db_user, db_password]):
        raise ValueError(
            "데이터베이스 설정이 필요합니다. "
            ".env 파일에 DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD를 설정해주세요."
        )
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASE_URL = get_database_url()

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
    # 연결 테스트
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"데이터베이스 연결 실패: {e}")
    print("환경변수 설정을 확인해주세요.")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()