# Changelog

## [2.0.0] - 2026-01-18

### 🚀 주요 변경사항
- Bedrock Flow → Bedrock Agent-Core로 마이그레이션
- 개별 Bedrock 서비스 통합

### ✨ 추가
- `services/agent_core.py` - Bedrock Agent-Core 통합 서비스
- `routers/agent.py` - Agent 기반 라우터
- 새로운 응답 타입: `"diary"` (일기 생성)

### 🗑️ 제거
- `services/flow.py` - Bedrock Flow 서비스
- `services/bedrock.py` - 개별 Bedrock 서비스
- `routers/flow.py` - Flow 라우터
- Flow 관련 환경변수 (`BEDROCK_FLOW_ARN`, `BEDROCK_FLOW_ALIAS`)

### 🔄 변경
- `POST /journal/process` - Agent-Core 기반으로 변경
  - 새로운 필드: `request_type` ("summarize" | "question")
  - 새로운 필드: `temperature` (0.0 ~ 1.0)
  - 새로운 응답 타입: `"diary"`
- `POST /journal/summary` - Agent-Core 사용

### 📦 프로젝트 구조
```
journal-api/
├── models/          # SQLAlchemy 모델
├── schemas/         # Pydantic 스키마
├── routers/         # FastAPI 라우터
│   ├── agent.py     # ✨ 새로 추가
│   ├── messages.py
│   ├── history.py
│   └── summary.py
├── services/        # 비즈니스 로직
│   ├── agent_core.py  # ✨ 새로 추가
│   └── s3.py
├── k8s/
├── main.py
├── database.py
└── config.py
```

### 🔧 환경변수
**제거됨:**
- `BEDROCK_FLOW_ARN`
- `BEDROCK_FLOW_ALIAS`

**유지됨:**
- `DATABASE_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_NAME`
- `BEDROCK_MODEL_ID`
- `ENVIRONMENT`
- `DEBUG`
- `ALLOWED_ORIGINS`

### 📝 API 호환성
모든 기존 API 엔드포인트는 그대로 유지되며 호환됩니다.

---

## [1.0.0] - 2026-01-01

### ✨ 초기 릴리즈
- FastAPI 기반 Journal API
- PostgreSQL 데이터베이스
- AWS Bedrock Flow 통합
- S3 저장소 연동
- 메시지, 히스토리, 요약 기능
