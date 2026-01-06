# ArgoCD 빠른 시작 가이드

기존 ArgoCD에 journal-api 애플리케이션을 등록하는 빠른 가이드입니다.

## 🚀 5분 안에 배포하기

### 1단계: ArgoCD에 Git 저장소 등록

**방법 A: ArgoCD UI 사용 (추천)**

1. ArgoCD UI 접속
2. **Settings** → **Repositories** → **Connect Repo**
3. 다음 정보 입력:
   - **Connection Method**: `VIA HTTPS`
   - **Type**: `git`
   - **Repository URL**: `https://github.com/LSH-3016/journal.git`
   - **Username**: `LSH-3016`
   - **Password**: GitHub Personal Access Token
4. **Connect** 클릭

**방법 B: CLI 사용**

```bash
argocd repo add https://github.com/LSH-3016/journal.git \
  --username LSH-3016 \
  --password <your-github-token>
```

**GitHub Personal Access Token 생성:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. 권한: `repo` 전체 선택
4. Generate token 후 복사

### 2단계: Application 생성

**방법 A: kubectl 사용 (추천)**

```bash
kubectl apply -f argocd-application.yaml
```

**방법 B: ArgoCD UI 사용**

1. **Applications** → **New App**
2. 다음 정보 입력:
   - **Application Name**: `journal-api` (소문자 필수!)
   - **Project**: `default`
   - **Sync Policy**: `Automatic` 체크
   - **Repository URL**: `https://github.com/LSH-3016/journal.git`
   - **Revision**: `main`
   - **Path**: `k8s` (중요! 루트가 아닌 k8s 폴더)
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `default`
3. **Create** 클릭

**방법 C: CLI 사용**

```bash
argocd app create journal-api \
  --repo https://github.com/LSH-3016/journal.git \
  --path k8s \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### 3단계: 배포 확인

```bash
# Application 상태 확인
argocd app get journal-api

# 또는 kubectl로 확인
kubectl get pods -l app=journal-api -n default
kubectl get svc journal-api-service -n default
kubectl get ingress journal-api-ingress -n default

# 서비스 접속 테스트
curl https://journal.aws11.shop/health
```

---

## ✅ 체크리스트

배포 전 확인사항:

- [ ] GitHub Personal Access Token 생성
- [ ] ArgoCD에 Git 저장소 등록 (`https://github.com/LSH-3016/journal.git`)
- [ ] ArgoCD Application 생성 (`journal-api`, path: `k8s`)
- [ ] AWS Secrets Manager에 DB 자격증명 등록 (`journal-api/database`)
- [ ] ServiceAccount IAM Role 설정 (IRSA)
- [ ] GitHub Secrets 설정 (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- [ ] GitHub Actions 워크플로우 권한 설정 (Read and write permissions)

---

## 🌐 네트워크 구성

### 네임스페이스
- **배포 네임스페이스**: `default`

### 로드밸런서 구성
- **Service 타입**: `NodePort` (포트 32000)
- **Ingress**: AWS ALB Controller 사용
- **ALB 그룹**: `fproject-alb` (기존 ALB에 자동으로 추가됨)
- **도메인**: `journal.aws11.shop`
- **SSL 인증서**: ACM 인증서 (arn:aws:acm:us-east-1:324547056370:certificate/dcba4e4a-c0d5-4e97-aecc-91a1b35f7355)

**중요**: `alb.ingress.kubernetes.io/group.name: fproject-alb` 설정으로 인해 이 애플리케이션은 기존 `fproject-alb` ALB에 자동으로 추가됩니다. 별도의 ALB가 생성되지 않습니다.

---

## 🔄 배포 플로우

```
1. 코드 푸시 (main/develop 브랜치)
   ↓
2. GitHub Actions 실행
   - Docker 이미지 빌드
   - ECR에 푸시 (v{run_number}, latest, {commit_sha})
   - k8s/k8s-deployment.yaml 업데이트
   - Git에 커밋 & 푸시
   ↓
3. ArgoCD가 변경 감지 (최대 3분)
   ↓
4. EKS에 자동 배포
   - k8s/k8s-deployment.yaml 적용
   - k8s/k8s-ingress.yaml 적용
   ↓
5. 배포 완료 (ArgoCD UI에서 확인)
```

---

## 🛠️ 주요 설정

### 환경변수 (k8s/k8s-deployment.yaml)

```yaml
env:
- name: AWS_REGION
  value: "us-east-1"
- name: ALLOWED_ORIGINS
  value: "https://www.aws11.shop,https://aws11.shop,https://journal.aws11.shop"
- name: DEBUG
  value: "False"
- name: ENVIRONMENT
  value: "production"  # Secrets Manager 사용
- name: S3_BUCKET_NAME
  value: "knowledge-base-test-6575574"
- name: BEDROCK_MODEL_ID
  value: "arn:aws:bedrock:us-east-1:324547056370:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### CORS 설정

`ALLOWED_ORIGINS` 환경변수로 제어 (main.py):
- `https://www.aws11.shop`
- `https://aws11.shop`
- `https://journal.aws11.shop`

추가 도메인이 필요하면 콤마로 구분하여 추가

### 데이터베이스 자격증명

**AWS Secrets Manager** 사용 (config.py):
- Secret 이름: `journal-api/database`
- 필수 키:
  - `host`: DB 호스트
  - `port`: DB 포트
  - `dbname`: 데이터베이스 이름
  - `username`: DB 사용자
  - `password`: DB 비밀번호

### ServiceAccount IAM Role (IRSA)

```yaml
serviceAccountName: journal-api-sa
# IAM Role: arn:aws:iam::324547056370:role/journal-api-secrets-role
```

**필요한 권한:**
- Secrets Manager 읽기
- ECR 이미지 Pull
- S3 읽기/쓰기
- Bedrock 모델 호출

---

## 📊 모니터링

### ArgoCD UI에서 확인

- **Sync Status**: Synced (녹색)
- **Health Status**: Healthy (녹색)
- **Last Sync**: 최근 동기화 시간

**참고**: `aws-load-balancer-controller`가 보이는 것은 정상입니다. Ingress의 연관 리소스로 표시되는 것이며, ArgoCD가 관리하는 리소스가 아닙니다. **절대 삭제하지 마세요!**

### CLI로 확인

```bash
# 전체 상태
argocd app get journal-api

# 동기화 이력
argocd app history journal-api

# 실시간 로그
argocd app logs journal-api -f
```

### Kubernetes에서 확인

```bash
# Pod 상태
kubectl get pods -l app=journal-api -n default

# 로그 확인
kubectl logs -l app=journal-api -n default --tail=100 -f

# Service 확인
kubectl get svc journal-api-service -n default

# Ingress 확인
kubectl get ingress journal-api-ingress -n default
kubectl describe ingress journal-api-ingress -n default
```

---

## 🔧 트러블슈팅

### Application이 OutOfSync 상태

**원인**: Git 저장소와 클러스터 상태가 다름

**해결**:
```bash
# 수동 동기화
argocd app sync journal-api

# 또는 UI에서 SYNC 버튼 클릭
```

### Image Pull 실패

**원인**: ECR 접근 권한 부족

**해결**:
1. ServiceAccount IAM Role 확인
2. ECR 정책 확인
3. Pod 이벤트 확인: `kubectl describe pod <pod-name> -n default`

### 변경사항이 반영되지 않음

**원인**: ArgoCD 폴링 주기 (기본 3분)

**해결**:
```bash
# 즉시 동기화
argocd app sync journal-api

# 또는 UI에서 Refresh 버튼 클릭
```

### Database 연결 실패

**원인**: Secrets Manager 접근 권한 또는 자격증명 오류

**해결**:
1. Secrets Manager에 `journal-api/database` 시크릿 확인
2. ServiceAccount IAM Role에 Secrets Manager 읽기 권한 확인
3. Pod 로그 확인: `kubectl logs -l app=journal-api -n default`

### CORS 오류

**원인**: 허용되지 않은 도메인에서 접근

**해결**:
`k8s/k8s-deployment.yaml`의 `ALLOWED_ORIGINS`에 도메인 추가:
```yaml
- name: ALLOWED_ORIGINS
  value: "https://www.aws11.shop,https://aws11.shop,https://journal.aws11.shop,https://new-domain.com"
```

---

## 🎯 다음 단계

1. **환경별 설정**: Kustomize로 dev/staging/prod 분리
2. **알림 설정**: Slack/Discord 알림 연동
3. **Progressive Delivery**: Argo Rollouts로 카나리 배포
4. **모니터링**: Prometheus + Grafana 연동
5. **로그 수집**: ELK Stack 또는 CloudWatch Logs

자세한 내용은 [ARGOCD_SETUP.md](./ARGOCD_SETUP.md)를 참조하세요.
