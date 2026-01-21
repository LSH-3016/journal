# Journal API

AI 기반 일기 및 메시지 관리 시스템입니다. FastAPI와 외부 Agent API를 활용하여 지능형 텍스트 분류, 자동 요약, S3 저장 기능을 제공합니다.

## 🚀 주요 기능

- **메시지 관리**: 일일 메시지 저장/조회, KST 기준 필터링
- **히스토리 관리**: PostgreSQL + S3 이중 저장, 태그 기반 분류
- **AI 기능**: Agent API 자동 분류 (데이터/질문/일기), AI 요약 생성, 질문 응답
- **AWS 연동**: S3 저장

## 🛠️ 기술 스택

FastAPI, Python 3.8+, PostgreSQL, AWS S3, SQLAlchemy, Pydantic, httpx

---

## 🚀 설치 및 실행

### 로컬 개발

```bash
# 1. 설치
git clone <repository-url>
cd journal-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. PostgreSQL 설정
# CREATE DATABASE chatdb;
# CREATE USER chatuser WITH PASSWORD 'your_password';
# GRANT ALL PRIVILEGES ON DATABASE chatdb TO chatuser;

# 3. .env 파일 생성 (.env.example 참고)
DATABASE_URL=postgresql://chatuser:password@localhost:5432/chatdb
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=knowledge-base-test-6575574
AGENT_API_URL=http://agent-api-service:8000
ENVIRONMENT=development
DEBUG=True

# 4. 서버 실행
uvicorn main:app --reload
```

**로컬 URL:**
- API: http://localhost:8000/journal
- 문서: http://localhost:8000/journal/docs

### 프로덕션 환경

프로덕션에서는 AWS Secrets Manager를 사용합니다:
- `journal-api/database` - DB 연결 정보
- `journal-api/aws-credentials` - AWS 자격 증명 (S3용)

환경변수에 `ENVIRONMENT=production` 설정 시 자동으로 Secrets Manager에서 로드합니다.

**프로덕션 URL:**
- API: https://api.aws11.shop/journal
- 문서: https://api.aws11.shop/journal/docs

---

## 📖 API 사용법

### 메시지 저장
```bash
curl -X POST "http://localhost:8000/journal/messages" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "content": "오늘 아침 7시에 기상했다"}'
```

### 통합 처리 (Agent API)
```bash
# 자동 판단 (데이터/질문/일기 자동 분류)
curl -X POST "http://localhost:8000/journal/process" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "content": "오늘 아침 7시에 기상했다"}'

# 일기 생성 (명시적 지정)
curl -X POST "http://localhost:8000/journal/process" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "content": "오늘 하루...", "request_type": "summarize", "temperature": 0.7}'

# 질문 답변 (명시적 지정)
curl -X POST "http://localhost:8000/journal/process" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "content": "어제 뭐 했어?", "request_type": "question"}'
```

### AI 요약 생성
```bash
curl -X POST "http://localhost:8000/journal/summary" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "temperature": 0.7}'
```

더 자세한 API 사용법은 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)를 참조하세요.

---

## 🗄️ 데이터베이스 구조

자세한 ERD는 [DATABASE_ERD.md](./DATABASE_ERD.md)를 참조하세요.

**Messages 테이블:** `id` (UUID), `user_id`, `content`, `created_at`

**History 테이블:** `id` (BIGSERIAL), `user_id`, `content`, `record_date`, `tags`, `s3_key`, `text_url`

---

## 🏗️ 프로젝트 구조

```
journal-api/
├── models/          # SQLAlchemy 모델
├── schemas/         # Pydantic 스키마
├── routers/         # FastAPI 라우터 (agent, messages, history, summary)
├── services/        # 비즈니스 로직 (agent_api, s3)
├── k8s/             # Kubernetes manifests
├── main.py          # FastAPI 진입점
├── database.py      # DB 연결
├── config.py        # 설정 관리
└── Dockerfile       # Docker 이미지
```

---

## 🔧 AWS 설정

**필요한 IAM 권한:** `s3:GetObject`, `s3:PutObject`, `secretsmanager:GetSecretValue`

**설정 항목:**
- S3 버킷 생성
- Secrets Manager 설정 (선택사항)

---

## 🧪 테스트

```bash
pytest tests/
curl http://localhost:8000/journal/health
```

---

## 🚀 배포

### GitOps 배포 (ArgoCD)

```
코드 푸시 → GitHub Actions (ECR 빌드) → ArgoCD → EKS 배포
```

**빠른 시작:**
```bash
# 1. Git 저장소 등록
argocd repo add https://github.com/LSH-3016/journal.git \
  --username LSH-3016 --password <github-token>

# 2. Application 생성
kubectl apply -f argocd-application.yaml

# 3. 배포 확인
argocd app get journal-api
```

**네트워크:** `default` 네임스페이스, ALB 그룹 `one-api-alb`, 도메인 `api.aws11.shop/journal`

**GitHub Secrets:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Docker 로컬 배포
```bash
docker build -t journal-api:latest .
docker run -p 8000:8000 --env-file .env journal-api:latest
```

---

**Happy Coding! 🎉**
