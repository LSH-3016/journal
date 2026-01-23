import json
import logging
import httpx
from typing import Dict, Any, Optional
from config import AGENT_API_URL

logger = logging.getLogger(__name__)

class AgentAPIService:
    """Agent API 서비스를 사용한 통합 AI 서비스"""
    
    def __init__(self):
        # Agent API 서비스 URL (같은 클러스터 내 서비스)
        self.agent_api_url = AGENT_API_URL
        logger.info(f"AgentAPIService initialized with URL: {self.agent_api_url}")
    
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
            user_id (str): 사용자 ID
            request_type (Optional[str]): 요청 타입 ('summarize' 또는 'question'). 
                                          None이면 orchestrator가 자동 판단
            temperature (Optional[float]): summarize agent용 temperature 파라미터 (0.0 ~ 1.0)
            current_date (Optional[str]): 현재 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            Dict[str, Any]: 처리 결과
            {
                "type": "data" | "answer" | "diary",
                "content": str,
                "message": str
            }
        """
        try:
            return self._invoke_agent_api(user_input, user_id, request_type, temperature, current_date)
        except Exception as e:
            logger.error(f"Agent API 호출 실패: {e}")
            raise
    
    def _invoke_agent_api(
        self,
        user_input: str,
        user_id: str,
        request_type: Optional[str] = None,
        temperature: Optional[float] = None,
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Agent API 서비스 호출
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID
            request_type: 요청 타입
            temperature: temperature 파라미터
            current_date: 현재 날짜 (YYYY-MM-DD)
        """
        try:
            logger.info(f"Agent API 호출 시작")
            logger.info(f"URL: {self.agent_api_url}/agent")
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
            
            logger.info(f"Request payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # HTTP POST 요청
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.agent_api_url}/agent",
                    json=payload
                )
                response.raise_for_status()
            
            logger.info(f"Agent API 응답 수신 - Status: {response.status_code}")
            
            # JSON 응답 파싱
            result = response.json()
            logger.info(f"응답 타입: {result.get('type')}")
            
            return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Agent API HTTP 에러: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Agent API 호출 실패: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Agent API 요청 에러: {str(e)}")
            raise Exception(f"Agent API 연결 실패: {str(e)}")
        except Exception as e:
            logger.error(f"Agent API 호출 실패: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

# 싱글톤 인스턴스
agent_api_service = AgentAPIService()
