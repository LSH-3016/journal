# Kubernetes Secrets 설정 가이드

## 보안 주의사항

⚠️ **중요**: `k8s-secrets.yaml` 파일은 민감한 정보를 포함하고 있어 `.gitignore`에 추가되어 있습니다. 절대 Git에 커밋하지 마세요!

## 1. Secret 파일 생성

`k8s-secrets.example.yaml`을 복사하여 `k8s-secrets.yaml`을 생성하고 실제 값으로 채우세요:

```bash
cp k8s-secrets.example.yaml k8s-secrets.yaml
```

그리고 실제 값으로 수정:
```yaml
stringData:
  db-host: "fproject-dev-postgres.c9eksq6cmh3c.us-east-1.rds.amazonaws.com"
  db-port: "5432"
  db-name: "fproject_db"
  db-user: "fproject_user"
  db-password: "실제_비밀번호"
  aws-access-key-id: "실제_AWS_키"
  aws-secret-access-key: "실제_AWS_시크릿"
  bedrock-flow-arn: "실제_Flow_ARN"
  bedrock-flow-alias: "실제_Alias"
```

## 2. EKS에 Secret 배포 (최초 1회만)

### GitHub Actions 사용 (권장)

1. GitHub Repository > Actions 탭으로 이동
2. "Deploy Secrets to EKS" workflow 선택
3. "Run workflow" 클릭
4. 민감 정보 입력:
   - Database Password: 실제 DB 비밀번호
   - AWS Access Key ID: 실제 AWS Access Key
   - AWS Secret Access Key: 실제 AWS Secret Key
5. "Run workflow" 실행

Secret은 최초 1회만 배포하면 되고, 이후 애플리케이션 배포는 자동으로 진행됩니다.

```bash
# EKS 연결
aws eks update-kubeconfig --name fproject-dev-eks --region us-east-1

# Secret 배포
kubectl apply -f k8s-secrets.yaml

# 확인
kubectl get secret journal-secrets
kubectl describe secret journal-secrets
```

## 3. Secret 업데이트

값을 변경해야 할 때는 GitHub Actions의 "Deploy Secrets to EKS" workflow를 다시 실행하면 됩니다.

업데이트 후 Pod 재시작:
1. GitHub Repository > Actions
2. "Deploy to EKS" workflow 실행 (자동으로 Pod 재시작됨)

## 4. 더 안전한 방법 (프로덕션 권장)

### Option 1: AWS Secrets Manager 사용

```bash
# AWS Secrets Manager에 저장
aws secretsmanager create-secret \
  --name journal-api/db-password \
  --secret-string "your-password"

# External Secrets Operator 설치
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

### Option 2: Sealed Secrets 사용

```bash
# Sealed Secrets Controller 설치
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# kubeseal CLI 설치 후 Secret 암호화
kubeseal -f k8s-secrets.yaml -w k8s-sealed-secrets.yaml

# 암호화된 파일은 Git에 커밋 가능
git add k8s-sealed-secrets.yaml
```

### Option 3: GitHub Secrets로 관리

GitHub Actions에서 Secret을 생성하고 배포 시 적용:

1. GitHub Repository > Settings > Secrets에 각 값 추가
2. Workflow에서 Secret 생성:

```yaml
- name: Create Kubernetes Secret
  run: |
    kubectl create secret generic journal-secrets \
      --from-literal=db-host=${{ secrets.DB_HOST }} \
      --from-literal=db-password=${{ secrets.DB_PASSWORD }} \
      --from-literal=aws-access-key-id=${{ secrets.AWS_ACCESS_KEY_ID }} \
      --from-literal=aws-secret-access-key=${{ secrets.AWS_SECRET_ACCESS_KEY }} \
      --dry-run=client -o yaml | kubectl apply -f -
```

## 5. 보안 체크리스트

- [ ] `k8s-secrets.yaml`이 `.gitignore`에 포함되어 있는지 확인
- [ ] Git 히스토리에 민감 정보가 없는지 확인
- [ ] AWS IAM 권한을 최소 권한으로 설정
- [ ] 프로덕션 환경에서는 AWS Secrets Manager 또는 Sealed Secrets 사용
- [ ] Secret 값을 정기적으로 로테이션
- [ ] RBAC으로 Secret 접근 제한

## 6. 긴급 상황 (Secret 노출 시)

1. 즉시 AWS 자격 증명 비활성화
2. RDS 비밀번호 변경
3. 새로운 Secret 생성 및 배포
4. Git 히스토리에서 민감 정보 제거 (BFG Repo-Cleaner 사용)
