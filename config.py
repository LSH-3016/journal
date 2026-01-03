import os
import json
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name="us-east-1"):
    """AWS Secrets Manager에서 시크릿 가져오기"""
    
    # 로컬 개발 환경에서는 환경변수 사용
    if os.getenv("ENVIRONMENT") == "development":
        return None
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)
    except ClientError as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None

# Database 설정
db_secret = get_secret("journal-api/database")
if db_secret:
    DB_HOST = db_secret.get("host")
    DB_PORT = db_secret.get("port")
    DB_NAME = db_secret.get("dbname")
    DB_USER = db_secret.get("username")
    DB_PASSWORD = db_secret.get("password")
else:
    # 환경변수에서 가져오기 (로컬 개발용)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "journal_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# AWS 자격 증명
aws_secret = get_secret("journal-api/aws-credentials")
if aws_secret:
    AWS_ACCESS_KEY_ID = aws_secret.get("access_key_id")
    AWS_SECRET_ACCESS_KEY = aws_secret.get("secret_access_key")
else:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Bedrock 설정
bedrock_secret = get_secret("journal-api/bedrock")
if bedrock_secret:
    BEDROCK_FLOW_ARN = bedrock_secret.get("flow_arn")
    BEDROCK_FLOW_ALIAS = bedrock_secret.get("flow_alias")
else:
    BEDROCK_FLOW_ARN = os.getenv("BEDROCK_FLOW_ARN")
    BEDROCK_FLOW_ALIAS = os.getenv("BEDROCK_FLOW_ALIAS")

# 기타 설정
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "knowledge-base-test-6575574")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "arn:aws:bedrock:us-east-1:324547056370:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
