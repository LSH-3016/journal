import os
import json
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def get_secret(secret_name, region_name="us-east-1"):
    """AWS Secrets Manager에서 시크릿 가져오기"""
    
    # 로컬 개발 환경에서는 환경변수 사용
    env = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Environment: {env}")
    
    if env == "development":
        logger.info("Development mode - using environment variables")
        return None
    
    logger.info(f"Production mode - fetching secret: {secret_name}")
    
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        logger.info(f"Successfully retrieved secret: {secret_name}")
        return json.loads(secret)
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
        return None

# Database 설정
db_secret = get_secret("journal-api/database")
if db_secret:
    DB_HOST = db_secret.get("host")
    DB_PORT = db_secret.get("port")
    DB_NAME = db_secret.get("dbname")
    DB_USER = db_secret.get("username")
    DB_PASSWORD = db_secret.get("password")
    logger.info(f"Using database from Secrets Manager: {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    # 환경변수에서 가져오기 (로컬 개발용)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "journal_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    logger.warning(f"Failed to get database config from Secrets Manager, using environment variables: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # Production 환경에서 localhost를 사용하는 경우 경고
    if os.getenv("ENVIRONMENT") == "production" and DB_HOST == "localhost":
        logger.error("CRITICAL: Production environment is using localhost for database connection!")

# AWS 자격 증명
aws_secret = get_secret("journal-api/aws-credentials")
if aws_secret:
    AWS_ACCESS_KEY_ID = aws_secret.get("access_key_id")
    AWS_SECRET_ACCESS_KEY = aws_secret.get("secret_access_key")
else:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# 기타 설정
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")