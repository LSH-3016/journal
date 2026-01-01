import boto3
import os
from datetime import date
from typing import Optional
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME 환경변수가 설정되지 않았습니다.")
    
    def generate_s3_key(self, user_id: str, record_date: date) -> str:
        """S3 키를 생성합니다. 형식: {user_id}/history/{YYYY}/{MM}/{YYYY-MM-DD}.txt"""
        year = record_date.strftime("%Y")
        month = record_date.strftime("%m")
        date_str = record_date.strftime("%Y-%m-%d")
        return f"{user_id}/history/{year}/{month}/{date_str}.txt"
    
    def save_history_to_s3(self, user_id: str, content: str, record_date: date, tags: Optional[list] = None) -> str:
        """
        히스토리를 S3에 텍스트 파일로 저장합니다.
        
        Args:
            user_id: 사용자 ID
            content: 저장할 내용
            record_date: 기록 날짜
            tags: 태그 리스트 (선택사항)
            
        Returns:
            str: S3 텍스트 파일 URL
        """
        s3_key = self.generate_s3_key(user_id, record_date)
        
        # 텍스트 파일 내용 구성
        file_content = f"날짜: {record_date}\n"
        file_content += f"사용자: {user_id}\n"
        if tags:
            file_content += f"태그: {', '.join(tags)}\n"
        file_content += f"\n내용:\n{content}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content.encode('utf-8'),
                ContentType='text/plain; charset=utf-8'
            )
            logger.info(f"S3에 히스토리 저장 완료: {s3_key}")
            
            # S3 URL 생성
            text_url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"
            return text_url
        except ClientError as e:
            logger.error(f"S3 저장 실패: {e}")
            raise Exception(f"S3 저장 중 오류가 발생했습니다: {str(e)}")
    
    def get_history_from_s3(self, s3_key: str) -> str:
        """
        S3에서 히스토리 파일을 읽어옵니다.
        
        Args:
            s3_key: S3 키
            
        Returns:
            str: 파일 내용
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            logger.error(f"S3 읽기 실패: {e}")
            raise Exception(f"S3에서 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
    
    def delete_history_from_s3(self, s3_key: str) -> bool:
        """
        S3에서 히스토리 파일을 삭제합니다.
        
        Args:
            s3_key: S3 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"S3에서 히스토리 삭제 완료: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 삭제 실패: {e}")
            return False
    
    def check_file_exists(self, s3_key: str) -> bool:
        """
        S3에 파일이 존재하는지 확인합니다.
        
        Args:
            s3_key: S3 키
            
        Returns:
            bool: 파일 존재 여부
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

# 싱글톤 인스턴스
s3_service = S3Service()