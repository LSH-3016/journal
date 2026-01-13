import boto3
import json
import logging
from typing import Dict, Any, Optional

# config.py에서 설정 가져오기
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, BEDROCK_MODEL_ID

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        # AWS 자격증명 검증
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise ValueError("AWS 자격증명이 설정되지 않았습니다. Secrets Manager 또는 환경변수를 확인해주세요.")
        
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.model_id = BEDROCK_MODEL_ID
        
        # 기본 모델 파라미터
        self.default_temperature = 1
        self.default_top_k = 250
        
        logger.info(f"BedrockService initialized with model: {self.model_id}")
    
    async def summarize_content(
        self, 
        content: str,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None
    ) -> str:
        """
        주어진 내용을 Claude를 사용하여 요약합니다.
        
        Args:
            content: 요약할 텍스트 내용
            temperature: 응답의 무작위성 (0.0 ~ 1.0, 낮을수록 일관된 응답)
            top_k: 상위 K개 토큰에서 샘플링 (1 ~ 500)
            
        Returns:
            요약된 텍스트
            
        Raises:
            ValueError: 입력 내용이 유효하지 않을 때
            Exception: Bedrock API 호출 실패 시
        """
        # 입력 검증 강화
        if not content or not content.strip():
            raise ValueError('요약할 내용이 없습니다.')
        
        # 내용 길이 제한 (토큰 제한 고려)
        if len(content) > 50000:  # 약 50KB 제한
            content = content[:50000] + "..."
        
        # 파라미터 기본값 설정
        temp = temperature if temperature is not None else self.default_temperature
        tk = top_k if top_k is not None else self.default_top_k
        
        # System prompt 설정
        system_prompt = """너는 일기를 매일 작성하는 맞춤법과 문단 나누기에 엄격한 학생이야."""

        # User message 설정
        user_message = f"""
        일기 형식으로 작성하고, 줄글 형식, 1인칭 시점으로 요약해줘. 날짜는 따로 적지않아도 돼.
일기 내용:
{content}"""
        
        # Bedrock 요청 페이로드 구성
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": temp,
            "top_k": tk,
            "system": system_prompt,
            "messages": [{
                "role": "user",
                "content": user_message
            }]
        }
        
        logger.info(f"Bedrock 호출 - temperature: {temp}, top_k: {tk}")
        
        try:
            # Bedrock API 호출
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload),
                contentType='application/json'
            )
            
            # 응답 처리
            response_body = json.loads(response['body'].read())
            
            # 응답 구조 검증
            if 'content' not in response_body or not response_body['content']:
                raise Exception("Bedrock API 응답 형식이 올바르지 않습니다")
            
            summary = response_body['content'][0]['text'].strip()
            
            # 빈 응답 검증
            if not summary:
                raise Exception("AI가 빈 요약을 반환했습니다")
            
            return summary
            
        except json.JSONDecodeError as e:
            logger.error(f"Bedrock API 응답 파싱 실패: {e}")
            raise Exception("AI 응답을 처리하는 중 오류가 발생했습니다")
        except KeyError as e:
            logger.error(f"Bedrock API 응답 구조 오류: {e}")
            raise Exception("AI 응답 형식이 예상과 다릅니다")
        except Exception as e:
            logger.error(f"Bedrock API 호출 실패: {e}")
            # AWS 관련 오류인지 확인
            if "credentials" in str(e).lower():
                raise Exception("AWS 자격증명 오류입니다. 설정을 확인해주세요")
            elif "throttling" in str(e).lower():
                raise Exception("API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요")
            else:
                raise Exception(f"AI 요약 생성 실패: {str(e)}")

# 싱글톤 인스턴스
bedrock_service = BedrockService()