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
   - **Application Name**: `journal-api`
   - **Project**: `default`
   - **Sync Policy**: `Automatic` 체크
   - **Repository URL**: `https://github.com/LSH-3016/journal.git`
   - **Revision**: `main`
   - **Path**: `.` (루트 디렉토리)
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `default`
3. **Create** 클릭

**방법 C: CLI 사용**

```bash
argocd app create journal-api \
  --repo https://github.com/LSH-3016/journal.git \
  --path . \
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
```

---

## ✅ 체크리스트

배포 전 확인사항:

- [ ] GitHub Personal Access Token 생성
- [ ] ArgoCD에 Git 저장소 등록 (`https://github.com/LSH-3016/journal.git`)
- [ ] ArgoCD Application 생성 (`journal-api`)
- [ ] ECR 접근 권한 설정 (IRSA 권장)
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
- **SSL 인증서**: ACM 인증서 자동 적용

**중요**: `alb.ingress.kubernetes.io/group.name: fproject-alb` 설정으로 인해 이 애플리케이션은 기존 `fproject-alb` ALB에 자동으로 추가됩니다. 별도의 ALB가 생성되지 않습니다.

---

## 🔄 배포 플로우

```
1. 코드 푸시 (main/develop 브랜치)
   ↓
2. GitHub Actions 실행
   - Docker 이미지 빌드
   - ECR에 푸시
   - k8s-deployment.yaml 업데이트
   - Git에 커밋 & 푸시
   ↓
3. ArgoCD가 변경 감지 (최대 3분)
   ↓
4. EKS에 자동 배포
   ↓
5. 배포 완료 (ArgoCD UI에서 확인)
```

---

## 🛠️ ECR 접근 권한 설정

### 옵션 1: IRSA (권장)

ArgoCD가 이미 IRSA로 ECR 접근 권한이 있다면 추가 설정 불필요.

확인 방법:
```bash
kubectl describe sa argocd-application-controller -n argocd | grep eks.amazonaws.com/role-arn
```

### 옵션 2: imagePullSecrets

IRSA가 설정되어 있지 않다면, 배포할 네임스페이스에 Secret 생성:

```bash
# ECR 자격증명 Secret 생성
aws ecr get-login-password --region us-east-1 | \
kubectl create secret docker-registry ecr-registry-secret \
  --docker-server=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password-stdin \
  --namespace=default
```

그리고 `k8s-deployment.yaml`에 추가:
```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: ecr-registry-secret
```

---

## 📊 모니터링

### ArgoCD UI에서 확인

- **Sync Status**: Synced (녹색)
- **Health Status**: Healthy (녹색)
- **Last Sync**: 최근 동기화 시간

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
kubectl get pods -l app=journal-api

# 로그 확인
kubectl logs -l app=journal-api --tail=100 -f

# Service 확인
kubectl get svc journal-api-service
```

---

## 🔧 트러블슈팅

### Application이 OutOfSync 상태

**원인**: Git 저장소와 클러스터 상태가 다름

**해결**:
```bash
# 수동 동기화
argocd app sync journal-api
```

### Image Pull 실패

**원인**: ECR 접근 권한 부족

**해결**:
1. IRSA 설정 확인
2. imagePullSecrets 생성 및 적용
3. Pod 이벤트 확인: `kubectl describe pod <pod-name>`

### 변경사항이 반영되지 않음

**원인**: ArgoCD 폴링 주기 (기본 3분)

**해결**:
```bash
# 즉시 동기화
argocd app sync journal-api

# 또는 UI에서 Refresh 버튼 클릭
```

---

## 🎯 다음 단계

1. **환경별 설정**: Kustomize로 dev/staging/prod 분리
2. **알림 설정**: Slack/Discord 알림 연동
3. **Progressive Delivery**: Argo Rollouts로 카나리 배포
4. **모니터링**: Prometheus + Grafana 연동

자세한 내용은 [ARGOCD_SETUP.md](./ARGOCD_SETUP.md)를 참조하세요.
