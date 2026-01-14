import boto3
import json
import logging
from datetime import date
from typing import Dict, Any

# config.py에서 설정 가져오기
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, BEDROCK_FLOW_ARN, BEDROCK_FLOW_ALIAS

logger = logging.getLogger(__name__)

class BedrockFlowService:
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
        
        self.flow_arn = BEDROCK_FLOW_ARN
        self.flow_alias = BEDROCK_FLOW_ALIAS or 'LIVE'
        
        if not self.flow_arn:
            raise ValueError("BEDROCK_FLOW_ARN이 설정되지 않았습니다.")
        
        logger.info(f"BedrockFlowService initialized with flow: {self.flow_arn}")
    
    def invoke_flow(self, user_input: str, user_id: str, current_date: date = None) -> Dict[str, Any]:
        """
        Bedrock Flow를 호출하여 입력이 질문인지 데이터인지 판단합니다.
        
        Args:
            user_input: 사용자 입력 텍스트
            user_id: Cognito 사용자 고유 ID (sub)
            current_date: 현재 날짜 (기본값: 오늘 날짜)
            
        Returns:
            Dict: Flow 응답 결과
            {
                "node_name": "Data_return" | "Answer_return",
                "content": "응답 내용",
                "is_question": bool
            }
        """
        try:
            # 현재 날짜 설정
            if current_date is None:
                current_date = date.today()
            
            current_date_str = current_date.strftime("%Y.%m.%d")
            
            # Flow 입력 구성 - string 타입으로 모든 내용 합쳐서 전송
            combined_input = f"{user_input}\ncurrent_date: {current_date_str}\nuser_id: {user_id}"
            
            inputs = [
                {
                    'content': {
                        'document': combined_input
                    },
                    'nodeName': 'FlowInputNode',
                    'nodeOutputName': 'document'
                }
            ]
            
            # Flow 호출 - Alias ARN 사용 시에도 flowAliasIdentifier 필요
            if self.flow_alias.startswith('arn:aws:bedrock:'):
                # Alias ARN에서 Alias ID 추출
                alias_id = self.flow_alias.split('/')[-1]
                response = self.client.invoke_flow(
                    flowIdentifier=self.flow_arn,
                    flowAliasIdentifier=alias_id,
                    inputs=inputs
                )
            else:
                # Flow ARN + Alias ID를 사용하는 경우
                response = self.client.invoke_flow(
                    flowIdentifier=self.flow_arn,
                    flowAliasIdentifier=self.flow_alias,
                    inputs=inputs
                )
            
            # 응답 처리
            flow_completion = ""
            node_name = ""
            
            # 스트림 응답 처리
            if 'responseStream' in response:
                for event in response['responseStream']:
                    if 'flowOutputEvent' in event:
                        output_event = event['flowOutputEvent']
                        node_name = output_event.get('nodeName', '')
                        content = output_event.get('content', {})
                        
                        if 'document' in content:
                            flow_completion = content['document']
                        elif isinstance(content, str):
                            flow_completion = content
            
            # 결과 구성
            is_question = node_name == "Answer_return"
            
            result = {
                "node_name": node_name,
                "content": flow_completion,
                "is_question": is_question,
                "raw_response": response
            }
            
            logger.info(f"Flow 호출 완료 - 노드: {node_name}")
            return result
            
        except Exception as e:
            logger.error(f"Bedrock Flow 호출 실패: {e}")
            raise Exception(f"Flow 처리 중 오류가 발생했습니다: {str(e)}")

# 싱글톤 인스턴스
flow_service = BedrockFlowService()