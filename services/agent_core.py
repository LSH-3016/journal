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
        
        # Bedrock Agent Core Runtime 클라이언트
        self.client = boto3.client(
            'bedrock-agentcore-runtime',
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
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        사용자 요청을 분석하여 적절한 agent로 라우팅하는 메인 함수
        
        Args:
            user_input (str): 사용자 입력 데이터
            user_id (str): 사용자 ID (Knowledge Base 검색 필터용)
            request_type (Optional[str]): 요청 타입 ('summarize' 또는 'question'). 
                                          None이면 orchestrator가 자동 판단
            temperature (Optional[float]): summarize agent용 temperature 파라미터 (0.0 ~ 1.0)
            current_date (Optional[str]): 현재 날짜 (YYYY-MM-DD 형식, 검색 컨텍스트용)
        
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
                return self._invoke_agent_core(user_input, user_id, request_type, temperature, current_date)
            
            # 설정되지 않았으면 임시 구현 사용
            return self._fallback_implementation(user_input, user_id, request_type, temperature, current_date)
        
        except Exception as e:
            logger.error(f"Agent-Core 처리 실패: {e}")
            # 실패 시 임시 구현으로 폴백
            return self._fallback_implementation(user_input, user_id, request_type, temperature, current_date)
    
    def _invoke_agent_core(
        self,
        user_input: str,
        user_id: str,
        request_type: Optional[str] = None,
        temperature: Optional[float] = None,
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        실제 Agent-Core 호출
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID (Knowledge Base 검색 필터용)
            request_type: 요청 타입
            temperature: temperature 파라미터
            current_date: 현재 날짜 (YYYY-MM-DD)
        """
        try:
            logger.info(f"Agent-Core Runtime 호출 시작")
            logger.info(f"Runtime ARN: {self.agent_runtime_arn}")
            logger.info(f"Parameters - user_id: {user_id}, request_type: {request_type}, date: {current_date}")
            
            # 요청 페이로드 구성
            payload = {
                "content": user_input,
                "user_id": user_id,
                "record_date": current_date or ""
            }
            
            # request_type이 명시된 경우 추가
            if request_type:
                payload["request_type"] = request_type
            
            # temperature가 있는 경우 추가
            if temperature is not None:
                payload["temperature"] = temperature
            
            input_text = json.dumps(payload, ensure_ascii=False)
            logger.info(f"Request payload: {input_text}")
            
            # Bedrock Agent Core Runtime 호출
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_runtime_arn,
                inputText=input_text
            )
            
            # 응답 처리
            body = response['body'].read().decode('utf-8')
            logger.info(f"Agent-Core Runtime 응답 수신: {len(body)} bytes")
            logger.info(f"응답 내용: {body[:500]}...")
            
            # 응답 파싱
            try:
                result = json.loads(body)
                
                # 응답 구조 확인 및 변환
                if 'body' in result:
                    # 응답이 {"statusCode": 200, "body": {...}} 형태인 경우
                    actual_result = result['body']
                else:
                    # 응답이 직접 {"type": "...", "content": "..."} 형태인 경우
                    actual_result = result
                
                logger.info(f"파싱 성공 - 응답 타입: {actual_result.get('type')}")
                return actual_result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                logger.error(f"원본 응답: {body}")
                # 파싱 실패 시 폴백
                return self._fallback_implementation(user_input, user_id, request_type, temperature, current_date)
                
        except Exception as e:
            logger.error(f"Agent-Core Runtime 호출 실패: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.info("폴백 구현으로 전환")
            return self._fallback_implementation(user_input, user_id, request_type, temperature, current_date)
    
    def _fallback_implementation(
        self,
        user_input: str,
        user_id: str,
        request_type: Optional[str] = None,
        temperature: Optional[float] = None,
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        임시 구현 (Agent-Core 없이 동작)
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID
            request_type: 요청 타입
            temperature: temperature 파라미터
            current_date: 현재 날짜 (YYYY-MM-DD)
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
            result = self._question_agent(user_input, user_id, current_date)
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
        일기 생성 agent (폴백 구현)
        
        Args:
            content: 요약할 내용
            temperature: 응답의 무작위성 (0.0 ~ 1.0)
        
        Returns:
            생성된 일기 내용
        """
        logger.warning("Summarize agent 폴백 구현 호출 - Agent Core Runtime을 사용할 수 없습니다")
        return f"[일기 생성 실패] Agent Core Runtime을 사용할 수 없습니다. 시스템 관리자에게 문의하세요.\n\n입력 내용: {content[:100]}..."
    
    def _question_agent(self, question: str, user_id: str, current_date: Optional[str] = None) -> str:
        """
        질문 답변 agent (폴백 구현)
        
        Args:
            question: 사용자 질문
            user_id: 사용자 ID (Knowledge Base 검색 필터용)
            current_date: 현재 날짜 (YYYY-MM-DD, 검색 컨텍스트용)
        
        Returns:
            답변 내용
        """
        logger.warning("Question agent 폴백 구현 호출 - Agent Core Runtime을 사용할 수 없습니다")
        return "죄송합니다. 현재 질문 답변 서비스를 사용할 수 없습니다. Agent Core Runtime 연결을 확인해주세요."

# 싱글톤 인스턴스
agent_core_service = AgentCoreService()
