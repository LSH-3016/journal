# ArgoCD 배포 설정 가이드

이 문서는 GitHub Actions로 ECR에 이미지를 푸시하고, 기존 ArgoCD가 자동으로 EKS에 배포하도록 설정하는 방법을 설명합니다.

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [사전 준비사항](#사전-준비사항)
3. [ArgoCD 설정](#argocd-설정)
4. [Application 배포](#application-배포)
5. [GitHub Actions 워크플로우](#github-actions-워크플로우)
6. [검증 및 모니터링](#검증-및-모니터링)

---

## 🏗️ 아키텍처 개요

### 배포 플로우

```
코드 푸시 (GitHub)
    ↓
GitHub Actions 트리거
    ↓
Docker 이미지 빌드
    ↓
ECR에 이미지 푸시
    ↓
k8s manifest 업데이트 & Git 푸시
    ↓
ArgoCD가 변경 감지
    ↓
EKS에 자동 배포
```

### 주요 변경사항

**이전 (GitHub Actions 직접 배포)**
- GitHub Actions가 kubectl로 직접 EKS에 배포
- 배포 상태 추적 어려움
- 롤백 복잡

**현재 (ArgoCD 배포)**
- GitHub Actions는 ECR 이미지 빌드만 담당
- ArgoCD가 Git 저장소를 모니터링하여 자동 배포
- GitOps 방식으로 배포 이력 관리
- UI를 통한 쉬운 모니터링 및 롤백

---

## 📝 사전 준비사항

### 1. ArgoCD 접근 정보 확인

기존 ArgoCD가 설치되어 있으므로 다음 정보를 확인하세요:

- **ArgoCD URL**: ArgoCD 서버 주소
- **관리자 계정**: 로그인 자격증명
- **네임스페이스**: ArgoCD가 설치된 네임스페이스 (일반적으로 `argocd`)

### 2. ArgoCD CLI 설치 (선택사항)

CLI를 사용하면 더 편리하게 관리할 수 있습니다.

**macOS:**
```bash
brew install argocd
```

**Linux:**
```bash
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```

**Windows:**
```powershell
choco install argocd-cli
```

### 3. ArgoCD 로그인

```bash
# CLI 로그인 (ArgoCD URL을 실제 주소로 변경)
argocd login <argocd-server-url> --username admin

# 예시
argocd login argocd.example.com --username admin
```

---

## ⚙️ ArgoCD 설정

### 1. ECR 접근 권한 설정

ArgoCD가 ECR에서 이미지를 가져올 수 있도록 설정합니다.

**방법 1: IAM Role (IRSA - 권장)**

ArgoCD ServiceAccount에 ECR 접근 권한이 있는 IAM Role을 연결합니다.

```bash
# ArgoCD가 사용하는 ServiceAccount 확인
kubectl get sa -n argocd

# ServiceAccount에 IAM Role 어노테이션 추가
kubectl annotate serviceaccount argocd-application-controller \
  -n argocd \
  eks.amazonaws.com/role-arn=arn:aws:iam::ACCOUNT_ID:role/argocd-ecr-role
```

**IAM Role 정책 예시:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }
    ]
}
```

**방법 2: imagePullSecrets 사용**

배포할 네임스페이스에 ECR 자격증명 Secret을 생성합니다.

```bash
# ECR 로그인 토큰 생성
ECR_TOKEN=$(aws ecr get-login-password --region us-east-1)
ECR_REGISTRY="ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"

# Docker config Secret 생성
kubectl create secret docker-registry ecr-registry-secret \
  --docker-server=$ECR_REGISTRY \
  --docker-username=AWS \
  --docker-password=$ECR_TOKEN \
  --namespace=default
```

그리고 `k8s-deployment.yaml`에 imagePullSecrets 추가:
```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: ecr-registry-secret
```

> **참고**: ECR 토큰은 12시간마다 만료되므로, 방법 1(IRSA)을 권장합니다.

### 2. Git 저장소 연결

ArgoCD에 이 프로젝트의 Git 저장소를 등록합니다.

**CLI 사용:**
```bash
# Public 저장소
argocd repo add https://github.com/your-org/journal-api.git

# Private 저장소 (Personal Access Token)
argocd repo add https://github.com/your-org/journal-api.git \
  --username your-username \
  --password ghp_your_personal_access_token

# Private 저장소 (SSH)
argocd repo add git@github.com:your-org/journal-api.git \
  --ssh-private-key-path ~/.ssh/id_rsa
```

**UI 사용:**
1. ArgoCD UI 접속
2. **Settings** → **Repositories** → **Connect Repo**
3. 저장소 정보 입력:
   - Repository URL: `https://github.com/your-org/journal-api.git`
   - Username: GitHub 사용자명 (Private 저장소인 경우)
   - Password: Personal Access Token (Private 저장소인 경우)
4. **Connect** 클릭

**저장소 연결 확인:**
```bash
argocd repo list
```

---

## 🌐 네트워크 및 인프라 구성

### 네임스페이스
이 애플리케이션은 **`default` 네임스페이스**에 배포됩니다.

```bash
# 네임스페이스 확인
kubectl get all -n default -l app=journal-api
```

다른 네임스페이스를 사용하려면:
1. `k8s-deployment.yaml`, `k8s-ingress.yaml`의 `namespace` 필드 수정
2. `argocd-application.yaml`의 `destination.namespace` 수정

### 로드밸런서 구성

**Service (NodePort)**
- 타입: `NodePort`
- 포트: 8000
- NodePort: 32000
- NLB 어노테이션 포함 (향후 확장 가능)

**Ingress (ALB)**
- **ALB 그룹**: `fproject-alb`
- **도메인**: `journal.aws11.shop`
- **SSL/TLS**: ACM 인증서 자동 적용
- **프로토콜**: HTTP (80) → HTTPS (443) 리다이렉트

**중요**: `alb.ingress.kubernetes.io/group.name: fproject-alb` 설정으로 인해:
- 새로운 ALB가 생성되지 않음
- 기존 `fproject-alb` ALB에 이 서비스가 자동으로 추가됨
- 같은 ALB 그룹을 사용하는 다른 서비스들과 ALB를 공유
- 비용 절감 및 관리 효율성 향상

```yaml
# k8s-ingress.yaml의 핵심 설정
annotations:
  alb.ingress.kubernetes.io/group.name: fproject-alb  # 기존 ALB 그룹 사용
  alb.ingress.kubernetes.io/scheme: internet-facing
  alb.ingress.kubernetes.io/target-type: ip
```

### ALB 그룹 확인

```bash
# ALB Ingress 목록 확인
kubectl get ingress -A

# 특정 ALB 그룹의 Ingress 확인
kubectl get ingress -A -o json | jq '.items[] | select(.metadata.annotations["alb.ingress.kubernetes.io/group.name"] == "fproject-alb")'

# ALB 상태 확인
kubectl describe ingress journal-api-ingress -n default
```

---

## 📦 Application 배포

### 1. Application 매니페스트 수정

`argocd-application.yaml` 파일을 프로젝트에 맞게 수정:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: journal-api
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/your-org/journal-api.git  # 실제 저장소 URL로 변경
    targetRevision: main  # 또는 develop
    path: .
  
  destination:
    server: https://kubernetes.default.svc
    namespace: default  # 배포할 네임스페이스
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 2. Application 생성

**방법 1: kubectl 사용**
```bash
kubectl apply -f argocd-application.yaml
```

**방법 2: ArgoCD CLI 사용**
```bash
argocd app create journal-api \
  --repo https://github.com/your-org/journal-api.git \
  --path . \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

**방법 3: ArgoCD UI 사용**
1. Applications → New App
2. 필요한 정보 입력
3. Create

### 3. 동기화 확인

```bash
# Application 상태 확인
argocd app get journal-api

# 동기화 실행 (자동 동기화가 비활성화된 경우)
argocd app sync journal-api

# 로그 확인
argocd app logs journal-api
```

---

## 🔄 GitHub Actions 워크플로우

### 워크플로우 동작 방식

1. **코드 푸시**: `main` 또는 `develop` 브랜치에 푸시
2. **이미지 빌드**: Docker 이미지 빌드 및 ECR 푸시
3. **Manifest 업데이트**: `k8s-deployment.yaml`의 이미지 태그 업데이트
4. **Git 푸시**: 업데이트된 manifest를 Git에 커밋 및 푸시
5. **ArgoCD 감지**: ArgoCD가 변경사항 감지 (최대 3분 소요)
6. **자동 배포**: EKS에 새 버전 배포

### 주요 변경사항

**제거된 단계:**
- ❌ kubectl 설치
- ❌ EKS kubeconfig 설정
- ❌ kubectl apply 명령
- ❌ 배포 상태 확인

**추가된 단계:**
- ✅ Manifest 파일 업데이트
- ✅ Git 커밋 및 푸시
- ✅ 빌드 요약 정보

### 필요한 GitHub Secrets

```
AWS_ACCESS_KEY_ID: AWS 액세스 키
AWS_SECRET_ACCESS_KEY: AWS 시크릿 키
```

---

## 🔍 검증 및 모니터링

### 1. ArgoCD UI에서 확인

ArgoCD UI에 접속하여 애플리케이션 상태를 확인합니다.

**확인 사항:**
- Application 상태: **Healthy** & **Synced**
- 최근 동기화 시간
- 배포된 리소스 목록 (Deployment, Service, Ingress 등)
- Pod 상태 및 로그

### 2. CLI로 확인

```bash
# Application 목록
argocd app list

# 상세 정보
argocd app get journal-api

# 동기화 이력
argocd app history journal-api

# 리소스 상태
argocd app resources journal-api
```

### 3. Kubernetes 리소스 확인

```bash
# Deployment 상태
kubectl get deployment journal-api

# Pod 상태
kubectl get pods -l app=journal-api

# Service 확인
kubectl get svc journal-api-service

# 로그 확인
kubectl logs -l app=journal-api --tail=100
```

### 4. 배포 이벤트 확인

```bash
# ArgoCD 이벤트
kubectl get events -n argocd --sort-by='.lastTimestamp'

# Application 네임스페이스 이벤트
kubectl get events -n default --sort-by='.lastTimestamp'
```

---

## 🔧 트러블슈팅

### 1. ArgoCD가 변경사항을 감지하지 못함

**원인:**
- Git 저장소 폴링 주기 (기본 3분)
- 저장소 접근 권한 문제

**해결:**
```bash
# 수동 동기화
argocd app sync journal-api

# 저장소 연결 확인
argocd repo list

# 폴링 주기 변경 (ConfigMap 수정)
kubectl edit configmap argocd-cm -n argocd
# timeout.reconciliation: 60s 추가
```

### 2. ECR 이미지 Pull 실패

**원인:**
- ECR 접근 권한 부족
- 토큰 만료 (방법 2 사용 시)

**해결:**
```bash
# IRSA 설정 확인
kubectl describe sa argocd-application-controller -n argocd

# Secret 확인
kubectl get secret ecr-registry-secret -n default

# Pod 이벤트 확인
kubectl describe pod <pod-name>
```

### 3. 동기화 실패

**원인:**
- Manifest 파일 문법 오류
- 리소스 충돌

**해결:**
```bash
# 상세 로그 확인
argocd app get journal-api --show-operation

# Manifest 검증
kubectl apply --dry-run=client -f k8s-deployment.yaml

# 강제 동기화
argocd app sync journal-api --force
```

### 4. GitHub Actions에서 Git Push 실패

**원인:**
- 권한 부족
- 브랜치 보호 규칙

**해결:**
- GitHub Settings → Actions → General → Workflow permissions
- "Read and write permissions" 활성화
- 브랜치 보호 규칙에서 "Allow force pushes" 또는 봇 예외 추가

---

## 📊 모니터링 및 알림

### 1. ArgoCD Notifications 설정

```bash
# Notifications 설치
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-notifications/stable/manifests/install.yaml
```

**Slack 알림 설정:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-deployed]
  template.app-deployed: |
    message: |
      Application {{.app.metadata.name}} is now running new version.
    slack:
      attachments: |
        [{
          "title": "{{.app.metadata.name}}",
          "color": "good",
          "fields": [{
            "title": "Sync Status",
            "value": "{{.app.status.sync.status}}",
            "short": true
          }]
        }]
```

### 2. Prometheus 메트릭

ArgoCD는 기본적으로 Prometheus 메트릭을 제공합니다:

```bash
# 메트릭 엔드포인트
kubectl port-forward svc/argocd-metrics -n argocd 8082:8082
curl http://localhost:8082/metrics
```

---

## 🔄 롤백 방법

### 1. ArgoCD UI에서 롤백

1. Application 선택
2. History 탭
3. 이전 버전 선택
4. Rollback 클릭

### 2. CLI로 롤백

```bash
# 이력 확인
argocd app history journal-api

# 특정 버전으로 롤백
argocd app rollback journal-api <revision-id>
```

### 3. Git 기반 롤백

```bash
# Git 커밋 되돌리기
git revert <commit-hash>
git push

# ArgoCD가 자동으로 이전 버전 배포
```

---

## 📝 베스트 프랙티스

### 1. 환경별 분리

```
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       └── kustomization.yaml
```

### 2. 이미지 태그 전략

- ✅ 버전 태그 사용: `v1.0.0`, `v123`
- ✅ Git SHA 태그: `abc1234`
- ❌ `latest` 태그만 사용 (추적 어려움)

### 3. 동기화 정책

- **개발 환경**: 자동 동기화 + Self-Heal
- **프로덕션**: 수동 승인 또는 제한된 자동 동기화

### 4. 보안

- ECR 이미지 스캔 활성화
- IRSA 사용 (하드코딩된 자격증명 지양)
- ArgoCD RBAC 설정
- Secrets 관리 (Sealed Secrets, External Secrets)

---

## 🎯 다음 단계

1. **Kustomize 도입**: 환경별 설정 관리
2. **Helm Chart 전환**: 더 유연한 배포 관리
3. **Progressive Delivery**: Argo Rollouts로 카나리/블루-그린 배포
4. **Multi-Cluster**: 여러 클러스터 관리
5. **GitOps 확장**: Infrastructure as Code (Terraform + ArgoCD)

---

## 📚 참고 자료

- [ArgoCD 공식 문서](https://argo-cd.readthedocs.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [GitOps 가이드](https://www.gitops.tech/)
- [Kustomize 문서](https://kustomize.io/)

---

**Happy GitOps! 🚀**
