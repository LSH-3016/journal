# Journal API

AI 기반 일기 및 메시지 관리 시스템입니다. FastAPI와 AWS Bedrock을 활용하여 지능형 텍스트 분류, 자동 요약, S3 저장 기능을 제공합니다.

## 🚀 주요 기능

### 📝 메시지 관리
- 일일 메시지 저장 및 조회
- 한국 시간(KST) 기준 당일 메시지 필터링
- UUID 기반 고유 식별자

### 📚 히스토리 관리
- 요약된 일기 내용 저장
- PostgreSQL DB + AWS S3 이중 저장
- 이미지 URL과 텍스트 파일 URL 분리 관리
- 태그 기반 분류 및 검색

### 🤖 AI 기반 기능
- **지능형 분류**: Bedrock Flow를 통한 자동 데이터/질문 분류
- **자동 요약**: Claude를 활용한 메시지 요약 생성
- **질문 응답**: 질문 입력 시 자동 답변 제공

### ☁️ AWS 연동
- **S3**: 텍스트 파일 및 이미지 저장
- **Bedrock**: Claude 모델을 통한 AI 처리
- **Bedrock Flow**: 지능형 워크플로우 처리

---

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL
- **AI/ML**: AWS Bedrock (Claude), Bedrock Flow
- **Storage**: AWS S3
- **ORM**: SQLAlchemy
- **Validation**: Pydantic

---

## 📋 사전 요구사항

### 1. Python 환경
```bash
Python 3.8 이상
pip 또는 poetry
```

### 2. PostgreSQL
```bash
PostgreSQL 12 이상
```

### 3. AWS 계정 및 권한
```bash
# 필요한 AWS 서비스
- Bedrock (Claude 모델 액세스)
- Bedrock Flow
- S3 버킷
- IAM 권한 설정
```

---

## 🚀 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd journal-api
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=journal_db
DB_USER=your_username
DB_PASSWORD=your_password

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=your-journal-bucket

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Bedrock Flow Configuration
BEDROCK_FLOW_ARN=arn:aws:bedrock:us-east-1:account:flow/FLOWID
BEDROCK_FLOW_ALIAS=your-alias-id

# Application Configuration
DEBUG=True
ENVIRONMENT=development
```

### 5. 데이터베이스 마이그레이션
```bash
# 마이그레이션 스크립트 실행
python migrate_history_table.py
```

### 6. 서버 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📖 API 사용법

### 메시지 저장
```bash
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "content": "오늘 아침 7시에 기상했다"
  }'
```

### 지능형 처리 (Flow API)
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "content": "7시에 기상했다",
    "record_date": "2026-01-01",
    "tags": ["일상"],
    "s3_key": "https://example.com/image.jpg"
  }'
```

### AI 요약 생성
```bash
curl -X POST "http://localhost:8000/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "s3_key": "https://example.com/image.jpg"
  }'
```

### AI 요약 존재 확인
```bash
curl "http://localhost:8000/summary/check/user_001"
```

**응답:**
```json
{
  "exists": true,
  "id": 123,
  "record_date": "2026-01-01",
  "summary": "오늘은 일찍 일어나서...",
  "s3_key": "https://example.com/image.jpg"
}
```

더 자세한 API 사용법은 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)를 참조하세요.

---

## 🗄️ 데이터베이스 구조

### Messages 테이블
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### History 테이블
```sql
CREATE TABLE history (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    record_date DATE NOT NULL,
    tags TEXT[],
    s3_key TEXT,      -- 이미지 URL
    text_url TEXT     -- 텍스트 파일 URL
);
```

자세한 ERD는 [DATABASE_ERD.md](./DATABASE_ERD.md)를 참조하세요.

---

## 🏗️ 프로젝트 구조

```
journal-api/
├── main.py                 # FastAPI 애플리케이션 진입점
├── database.py             # 데이터베이스 연결 설정
├── requirements.txt        # Python 의존성
├── .env                   # 환경변수 (git에 포함되지 않음)
├── .env.example           # 환경변수 예시
├── migrate_history_table.py # 데이터베이스 마이그레이션
│
├── models/                # SQLAlchemy 모델
│   ├── __init__.py
│   ├── message.py         # Message 모델
│   └── history.py         # History 모델
│
├── schemas/               # Pydantic 스키마
│   ├── __init__.py
│   ├── message.py         # Message 스키마
│   ├── history.py         # History 스키마
│   └── summary.py         # Summary 스키마
│
├── routers/               # FastAPI 라우터
│   ├── __init__.py
│   ├── messages.py        # 메시지 API
│   ├── history.py         # 히스토리 API
│   ├── summary.py         # 요약 API
│   └── flow.py           # Flow API
│
├── services/              # 비즈니스 로직
│   ├── __init__.py
│   ├── bedrock.py         # Bedrock 서비스
│   ├── s3.py             # S3 서비스
│   └── flow.py           # Flow 서비스
│
└── docs/                  # 문서
    ├── API_DOCUMENTATION.md
    ├── DATABASE_ERD.md
    └── README.md
```

---

## 🔧 AWS 설정

### 1. IAM 권한 설정
다음 권한이 필요합니다:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:InvokeFlow",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "*"
        }
    ]
}
```

### 2. Bedrock 모델 액세스
AWS Console에서 다음 모델에 대한 액세스를 요청하세요:
- Claude 3.5 Sonnet
- 기타 사용하려는 Claude 모델

### 3. S3 버킷 생성
```bash
aws s3 mb s3://your-journal-bucket --region us-east-1
```

### 4. Bedrock Flow 설정
AWS Console에서 Flow를 생성하고 ARN을 환경변수에 설정하세요.

---

## 🧪 테스트

### 단위 테스트 실행
```bash
pytest tests/
```

### API 테스트
```bash
# 서버가 실행 중인 상태에서
curl http://localhost:8000/docs
```

---

## 📊 모니터링 및 로깅

### 로그 레벨 설정
```python
# main.py에서 로깅 레벨 조정
import logging
logging.basicConfig(level=logging.INFO)
```

### 주요 로그 확인 포인트
- Flow 처리 결과
- S3 업로드/다운로드 상태
- Bedrock API 호출 결과
- 데이터베이스 쿼리 성능

---

## 🚀 배포

### GitOps 기반 배포 (ArgoCD)

이 프로젝트는 GitOps 방식으로 배포됩니다:

1. **GitHub Actions**: 코드 푸시 시 Docker 이미지를 빌드하여 ECR에 푸시
2. **ArgoCD**: Git 저장소를 모니터링하여 EKS에 자동 배포

```
코드 푸시 → GitHub Actions → ECR 이미지 푸시 → ArgoCD → EKS 배포
```

**배포 설정:**
- GitHub Actions 워크플로우: `.github/workflows/deploy.yml`
- ArgoCD Application: `argocd-application.yaml`
- Kubernetes Manifests: `k8s-deployment.yaml`, `k8s-ingress.yaml`

**배포 가이드:**
- 🚀 **빠른 시작**: [ARGOCD_QUICKSTART.md](./ARGOCD_QUICKSTART.md) - 5분 안에 배포하기
- 📚 **상세 가이드**: [ARGOCD_SETUP.md](./ARGOCD_SETUP.md) - 전체 설정 및 트러블슈팅

### Docker를 사용한 로컬 배포
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 이미지 빌드
docker build -t journal-api:latest .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env journal-api:latest
```

### 환경별 설정
- **개발환경**: `DEBUG=True`, 로컬 DB, Port Forward
- **스테이징**: `DEBUG=False`, 클라우드 DB, ArgoCD 자동 배포
- **프로덕션**: `DEBUG=False`, 프로덕션 DB, ArgoCD + 수동 승인

---

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 📞 지원 및 문의

- **이슈 리포트**: GitHub Issues
- **문서**: [API 문서](./API_DOCUMENTATION.md), [ERD](./DATABASE_ERD.md)
- **이메일**: your-email@example.com

---

## 🔄 버전 히스토리

### v1.0.0 (2026-01-01)
- ✨ 초기 릴리즈
- 📝 메시지 및 히스토리 관리 기능
- 🤖 AI 기반 분류 및 요약 기능
- ☁️ AWS S3 및 Bedrock 연동

### 향후 계획
- 📱 모바일 앱 지원
- 🔍 고급 검색 기능
- 📈 사용자 대시보드
- 🔐 사용자 인증 시스템

---

## ⚡ 성능 최적화

### 데이터베이스 최적화
- 적절한 인덱스 설정
- 쿼리 최적화
- 연결 풀링

### API 최적화
- 응답 캐싱
- 페이지네이션
- 비동기 처리

### AWS 비용 최적화
- S3 스토리지 클래스 최적화
- Bedrock 사용량 모니터링
- 불필요한 API 호출 최소화

---

**Happy Coding! 🎉**