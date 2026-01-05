# Journal API - 프로젝트 개요

## 📁 프로젝트 파일 구조

### 핵심 애플리케이션 파일
```
├── main.py                     # FastAPI 애플리케이션 진입점
├── database.py                 # PostgreSQL 연결 설정
├── config.py                   # 환경 설정 관리
├── requirements.txt            # Python 패키지 의존성
├── Dockerfile                  # Docker 이미지 빌드 정의
└── .env                       # 환경변수 (로컬 개발용)
```

### 애플리케이션 레이어
```
├── models/                     # 데이터베이스 모델 (SQLAlchemy ORM)
│   ├── message.py             # 메시지 테이블 모델
│   └── history.py             # 히스토리 테이블 모델
│
├── schemas/                    # API 요청/응답 스키마 (Pydantic)
│   ├── message.py             # 메시지 스키마
│   ├── history.py             # 히스토리 스키마
│   └── summary.py             # 요약 스키마
│
├── routers/                    # API 엔드포인트 라우터
│   ├── messages.py            # 메시지 CRUD API
│   ├── history.py             # 히스토리 CRUD API
│   ├── summary.py             # AI 요약 API
│   └── flow.py                # Bedrock Flow API
│
└── services/                   # 비즈니스 로직 및 외부 서비스 연동
    ├── bedrock.py             # AWS Bedrock (Claude) 연동
    ├── s3.py                  # AWS S3 파일 저장
    └── flow.py                # Bedrock Flow 처리
```

### Kubernetes 배포 파일
```
├── k8s-deployment.yaml         # Deployment, Service, ServiceAccount 정의
├── k8s-ingress.yaml           # ALB Ingress 설정
└── argocd-application.yaml    # ArgoCD Application 정의
```

### CI/CD 파일
```
└── .github/
    └── workflows/
        └── deploy.yml          # GitHub Actions 워크플로우
                               # - Docker 이미지 빌드
                               # - ECR 푸시
                               # - Manifest 업데이트
```

### 문서
```
├── README.md                   # 프로젝트 메인 문서
├── PROJECT_OVERVIEW.md         # 이 파일 - 프로젝트 구조 설명
├── API_DOCUMENTATION.md        # API 엔드포인트 상세 문서
├── DATABASE_ERD.md            # 데이터베이스 스키마
├── DATABASE_SETUP.md          # 데이터베이스 설정 가이드
├── ARGOCD_QUICKSTART.md       # ArgoCD 빠른 시작 (5분)
├── ARGOCD_SETUP.md            # ArgoCD 상세 설정 가이드
├── SECRETS_SETUP.md           # AWS Secrets Manager 설정
├── SETUP_CLOUDFRONT.md        # CloudFront 설정
└── SETUP_S3_TO_API.md         # S3 연동 설정
```

---

## 🔄 배포 아키텍처

### GitOps 기반 배포 플로우

```
┌─────────────────┐
│  개발자 코드 푸시  │
│  (main/develop) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│   GitHub Actions        │
│  ─────────────────────  │
│  1. Docker 이미지 빌드   │
│  2. ECR에 푸시          │
│  3. k8s manifest 업데이트│
│  4. Git 커밋 & 푸시     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│      ArgoCD             │
│  ─────────────────────  │
│  1. Git 변경 감지       │
│  2. Manifest 동기화     │
│  3. EKS에 배포          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│    EKS Cluster          │
│  ─────────────────────  │
│  • Deployment (2 pods)  │
│  • Service (NodePort)   │
│  • Ingress (ALB)        │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   AWS ALB (fproject)    │
│  ─────────────────────  │
│  journal.aws11.shop     │
│  (HTTPS with ACM)       │
└─────────────────────────┘
```

---

## 🗂️ 주요 파일 설명

### 1. 애플리케이션 코어

**main.py**
- FastAPI 애플리케이션 초기화
- CORS 설정
- 라우터 등록
- 데이터베이스 테이블 생성

**database.py**
- PostgreSQL 연결 설정
- SQLAlchemy 엔진 및 세션 관리
- Base 모델 정의

**config.py**
- 환경변수 로드 및 관리
- 설정 값 검증

### 2. Kubernetes 리소스

**k8s-deployment.yaml**
- **Deployment**: 2개의 Pod 레플리카, 리소스 제한, Health Check
- **Service**: NodePort 타입 (포트 32000)
- **ServiceAccount**: IRSA를 통한 AWS 권한 부여

**k8s-ingress.yaml**
- AWS ALB Ingress Controller 사용
- `fproject-alb` 그룹에 연결 (기존 ALB 공유)
- HTTPS 리다이렉트 및 ACM 인증서 적용
- 도메인: `journal.aws11.shop`

**argocd-application.yaml**
- Git 저장소: `https://github.com/LSH-3016/journal.git`
- 자동 동기화 활성화 (prune, selfHeal)
- 배포 대상: `default` 네임스페이스

### 3. CI/CD

**.github/workflows/deploy.yml**
- 트리거: `main`, `develop` 브랜치 푸시
- ECR 로그인 및 이미지 빌드
- 3가지 태그 생성: `v{run_number}`, `latest`, `{commit_sha}`
- k8s-deployment.yaml 이미지 태그 업데이트
- Git 커밋 및 푸시 (ArgoCD가 감지)

---

## 🔐 보안 및 권한

### AWS IAM 역할

**journal-api-secrets-role**
- ServiceAccount에 연결 (IRSA)
- ECR 이미지 Pull 권한
- S3 읽기/쓰기 권한
- Bedrock 모델 호출 권한
- Secrets Manager 접근 권한

### GitHub Secrets

- `AWS_ACCESS_KEY_ID`: ECR 푸시용 AWS 액세스 키
- `AWS_SECRET_ACCESS_KEY`: ECR 푸시용 AWS 시크릿 키
- `GITHUB_TOKEN`: 자동 생성, manifest 업데이트 푸시용

### ArgoCD 저장소 인증

- GitHub Personal Access Token 사용
- `repo` 권한 필요

---

## 🌐 네트워크 구성

### 네임스페이스
- **default**: 모든 리소스 배포

### 서비스 노출
1. **Pod** (8000) → **Service** (NodePort 32000)
2. **Service** → **Ingress** (ALB)
3. **ALB** → 인터넷 (HTTPS 443)

### 도메인 및 SSL
- 도메인: `journal.aws11.shop`
- SSL/TLS: AWS ACM 인증서
- HTTP → HTTPS 자동 리다이렉트

### ALB 그룹 공유
- `alb.ingress.kubernetes.io/group.name: fproject-alb`
- 여러 서비스가 하나의 ALB 공유
- 비용 절감 및 관리 효율성

---

## 📊 리소스 사양

### Pod 리소스
```yaml
requests:
  memory: "256Mi"
  cpu: "250m"
limits:
  memory: "512Mi"
  cpu: "500m"
```

### 레플리카
- 기본: 2개 Pod
- HPA 설정 가능 (향후 확장)

### Health Check
- **Liveness Probe**: `/health` (30초 후 시작, 10초 간격)
- **Readiness Probe**: `/health` (5초 후 시작, 5초 간격)

---

## 🚀 빠른 시작

### 로컬 개발
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 수정

# 3. 서버 실행
uvicorn main:app --reload
```

### ArgoCD 배포
```bash
# 1. 저장소 등록
argocd repo add https://github.com/LSH-3016/journal.git \
  --username LSH-3016 \
  --password <token>

# 2. Application 생성
kubectl apply -f argocd-application.yaml

# 3. 상태 확인
argocd app get journal-api
```

자세한 내용은 [ARGOCD_QUICKSTART.md](./ARGOCD_QUICKSTART.md)를 참조하세요.

---

## 📚 문서 가이드

| 문서 | 용도 | 대상 |
|------|------|------|
| [README.md](./README.md) | 프로젝트 전체 개요 | 모든 사용자 |
| [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) | 파일 구조 및 아키텍처 | 개발자 |
| [ARGOCD_QUICKSTART.md](./ARGOCD_QUICKSTART.md) | 5분 빠른 배포 | DevOps |
| [ARGOCD_SETUP.md](./ARGOCD_SETUP.md) | 상세 배포 설정 | DevOps |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | API 엔드포인트 상세 | 개발자 |
| [DATABASE_ERD.md](./DATABASE_ERD.md) | 데이터베이스 스키마 | 개발자 |
| [DATABASE_SETUP.md](./DATABASE_SETUP.md) | DB 설정 가이드 | DevOps |

---

## 🔄 업데이트 히스토리

### v2.0.0 - GitOps 전환
- GitHub Actions → ECR 이미지 빌드 전용
- ArgoCD 기반 자동 배포
- Manifest 자동 업데이트

### v1.0.0 - 초기 릴리즈
- FastAPI 기반 REST API
- AWS Bedrock 연동
- S3 파일 저장
- PostgreSQL 데이터베이스
