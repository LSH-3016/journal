import boto3
import json
import logging
from typing import Dict, Any, Optional

from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AGENT_RUNTIME_ARN

logger = logging.getLogger(__name__)

class AgentCoreService:
    """Bedrock Agent-Core를 사용한 통합 AI 서비스"""
    
    def __init__(self):
        # AWS 자격증명 검증
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise ValueError("AWS 자격증명이 설정되지 않았습니다. Secrets Manager 또는 환경변수를 확인해주세요.")
        
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        self.agent_runtime_arn = AGENT_RUNTIME_ARN
        
        if self.agent_runtime_arn:
            logger.info(f"AgentCoreService initialized with ARN: {self.agent_runtime_arn}")
        else:
            logger.warning("Agent Runtime ARN이 설정되지 않았습니다. 임시 구현을 사용합니다.")
    
    def orchestrate_request(
        self,
        user_input: str,
        user_id: str,
        request_type: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        사용자 요청을 분석하여 적절한 agent로 라우팅하는 메인 함수
        
        Args:
            user_input (str): 사용자 입력 데이터
            user_id (str): 사용자 ID (Knowledge Base 검색 필터용)
            request_type (Optional[str]): 요청 타입 ('summarize' 또는 'question'). 
                                          None이면 orchestrator가 자동 판단
            temperature (Optional[float]): summarize agent용 temperature 파라미터 (0.0 ~ 1.0)
        
        Returns:
            Dict[str, Any]: 처리 결과
            {
                "type": "data" | "answer" | "diary",
                "content": str,
                "message": str
            }
        """
        try:
            # Agent Runtime ARN이 설정되어 있으면 실제 Agent-Core 사용
            if self.agent_runtime_arn:
                return self._invoke_agent_core(user_input, user_id, request_type, temperature)
            
            # 설정되지 않았으면 임시 구현 사용
            return self._fallback_implementation(user_input, user_id, request_type, temperature)
        
        except Exception as e:
            logger.error(f"Agent-Core 처리 실패: {e}")
            # 실패 시 임시 구현으로 폴백
            return self._fallback_implementation(user_input, user_id, request_type, temperature)
    
    def _invoke_agent_core(
        self,
        user_input: str,
        user_id: str,
        request_type: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        실제 Agent-Core 호출
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID (Knowledge Base 검색 필터용)
            request_type: 요청 타입
            temperature: temperature 파라미터
        """
        # TODO: 실제 Agent-Core API 호출 구현
        logger.info(f"Agent-Core 호출: {self.agent_runtime_arn}, user_id: {user_id}")
        
        # 임시로 폴백 구현 사용
        return self._fallback_implementation(user_input, user_id, request_type, temperature)
    
    def _fallback_implementation(
        self,
        user_input: str,
        user_id: str,
        request_type: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        임시 구현 (Agent-Core 없이 동작)
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID
            request_type: 요청 타입
            temperature: temperature 파라미터
        """
        # request_type이 명시되지 않은 경우 자동 판단
        if request_type is None:
            request_type = self._classify_request(user_input)
        
        if request_type == "summarize":
            # 일기 생성 (요약)
            result = self._summarize_agent(user_input, temperature)
            return {
                "type": "diary",
                "content": result,
                "message": "일기가 생성되었습니다."
            }
        
        elif request_type == "question":
            # 질문 답변
            result = self._question_agent(user_input, user_id)
            return {
                "type": "answer",
                "content": result,
                "message": "질문에 대한 답변입니다."
            }
        
        else:
            # 데이터 저장
            return {
                "type": "data",
                "content": "",
                "message": "메시지가 저장되었습니다."
            }
    
    def _classify_request(self, user_input: str) -> str:
        """
        사용자 입력을 분석하여 요청 타입을 자동 판단
        
        Returns:
            "data" | "question" | "summarize"
        """
        # TODO: Agent-Core의 orchestrator 사용
        # 임시 구현: 간단한 키워드 기반 분류
        
        question_keywords = ["?", "뭐", "무엇", "어디", "언제", "누구", "왜", "어떻게"]
        summarize_keywords = ["요약", "정리", "일기"]
        
        user_input_lower = user_input.lower()
        
        # 질문 판단
        if any(keyword in user_input for keyword in question_keywords):
            return "question"
        
        # 요약 판단
        if any(keyword in user_input_lower for keyword in summarize_keywords):
            return "summarize"
        
        # 기본값: 데이터 저장
        return "data"
    
    def _summarize_agent(self, content: str, temperature: Optional[float] = None) -> str:
        """
        일기 생성 agent
        
        Args:
            content: 요약할 내용
            temperature: 응답의 무작위성 (0.0 ~ 1.0)
        
        Returns:
            생성된 일기 내용
        """
        # TODO: Agent-Core의 summarize agent 호출
        # 임시 구현: 직접 Bedrock 호출
        logger.info(f"Summarize agent 호출 - temperature: {temperature}")
        
        try:
            from config import BEDROCK_MODEL_ID
            
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
            
            # System prompt 설정
            system_prompt = "너는 일기를 매일 작성하는 맞춤법과 문단 나누기에 엄격한 학생이야."
            
            # User message 설정
            user_message = f"""일기 형식으로 작성하고, 줄글 형식, 1인칭 시점으로 요약해줘. 날짜는 따로 적지않아도 돼.
일기 내용:
{content}"""
            
            # Bedrock 요청 페이로드 구성
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": temperature if temperature is not None else 0.7,
                "system": system_prompt,
                "messages": [{
                    "role": "user",
                    "content": user_message
                }]
            }
            
            # Bedrock API 호출
            response = bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps(payload),
                contentType='application/json'
            )
            
            # 응답 처리
            response_body = json.loads(response['body'].read())
            summary = response_body['content'][0]['text'].strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Bedrock 호출 실패: {e}")
            raise Exception(f"일기 생성 실패: {str(e)}")
    
    def _question_agent(self, question: str, user_id: str) -> str:
        """
        질문 답변 agent
        
        Args:
            question: 사용자 질문
            user_id: 사용자 ID (Knowledge Base 검색 필터용)
        
        Returns:
            답변 내용
        """
        # TODO: Agent-Core의 question agent 호출
        # TODO: user_id로 Knowledge Base 필터링하여 개인화된 답변 제공
        # 임시 구현: 직접 Bedrock 호출
        logger.info(f"Question agent 호출 - user_id: {user_id}")
        
        try:
            from config import BEDROCK_MODEL_ID
            
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
            
            # System prompt 설정
            system_prompt = f"너는 사용자(ID: {user_id})의 일기 데이터를 기반으로 질문에 답변하는 AI 어시스턴트야. 친절하고 자연스럽게 답변해줘."
            
            # User message 설정
            user_message = f"""사용자 질문: {question}

현재는 일기 데이터에 접근할 수 없어서 일반적인 답변만 제공할 수 있어. 
질문에 대해 도움이 될 만한 답변을 해줘.

참고: 실제 Agent-Core 구현 시에는 사용자 ID({user_id})로 Knowledge Base를 필터링하여 
해당 사용자의 일기 데이터를 기반으로 답변할 수 있어."""
            
            # Bedrock 요청 페이로드 구성
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": [{
                    "role": "user",
                    "content": user_message
                }]
            }
            
            # Bedrock API 호출
            response = bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps(payload),
                contentType='application/json'
            )
            
            # 응답 처리
            response_body = json.loads(response['body'].read())
            answer = response_body['content'][0]['text'].strip()
            
            return answer
            
        except Exception as e:
            logger.error(f"Bedrock 호출 실패: {e}")
            return f"죄송합니다. 질문에 답변하는 중 오류가 발생했습니다: {str(e)}"

# 싱글톤 인스턴스
agent_core_service = AgentCoreService()
