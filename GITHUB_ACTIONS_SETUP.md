# GitHub Actions 설정 가이드

## 1. GitHub Secrets 설정

GitHub 리포지토리 Settings > Secrets and variables > Actions에서 다음 secrets를 추가하세요:

### 필수 Secrets:
- `AWS_ACCESS_KEY_ID`: 실제 AWS Access Key ID
- `AWS_SECRET_ACCESS_KEY`: 실제 AWS Secret Access Key

## 2. Workflow 설명

### deploy.yml (자동 배포)
- **트리거**: main 또는 develop 브랜치에 push할 때
- **동작**:
  1. Docker 이미지 빌드
  2. ECR에 푸시 (commit SHA 태그 + latest 태그)
  3. EKS에 자동 배포
  4. 배포 상태 확인

### build-only.yml (빌드만)
- **트리거**: Pull Request 생성 시
- **동작**:
  1. Docker 이미지 빌드
  2. ECR에 푸시 (pr-{번호} 태그)
  3. 배포는 하지 않음 (테스트용)

## 3. 사용 방법

### 자동 배포:
```bash
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main
```

### 수동 배포:
GitHub Actions 탭에서 "Deploy to EKS" workflow를 선택하고 "Run workflow" 버튼 클릭

## 4. IAM 권한 확인

GitHub Actions에서 사용하는 IAM 사용자에게 다음 권한이 필요합니다:

### ECR 권한:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`

### EKS 권한:
- `eks:DescribeCluster`
- `eks:ListClusters`

### Kubernetes RBAC:
EKS 클러스터의 aws-auth ConfigMap에 IAM 사용자를 추가해야 합니다:

```bash
kubectl edit configmap aws-auth -n kube-system
```

다음 내용을 추가:
```yaml
mapUsers: |
  - userarn: arn:aws:iam::324547056370:user/testuser
    username: testuser
    groups:
      - system:masters
```

## 5. 배포 확인

GitHub Actions 탭에서 workflow 실행 상태를 확인할 수 있습니다:
- ✅ 성공: 배포 완료
- ❌ 실패: 로그 확인 후 수정

## 6. 롤백 방법

특정 커밋으로 롤백:
```bash
git revert <commit-hash>
git push origin main
```

또는 kubectl로 직접 롤백:
```bash
kubectl rollout undo deployment/journal-api
```

## 7. 환경별 배포

### Development 환경:
```bash
git push origin develop
```

### Production 환경:
```bash
git push origin main
```

## 8. 트러블슈팅

### ECR 로그인 실패:
- AWS credentials 확인
- IAM 권한 확인

### EKS 배포 실패:
- kubectl 권한 확인
- aws-auth ConfigMap 확인
- k8s-deployment.yaml 문법 확인

### 이미지 빌드 실패:
- Dockerfile 문법 확인
- requirements.txt 확인
