# 빠른 시작 가이드

## 1단계: GitHub Secrets 설정 (5분)

### 방법:
1. https://github.com/LSH-3016/journal/settings/secrets/actions 로 이동
2. **New repository secret** 클릭
3. 다음 2개의 secret 추가:

#### Secret 1:
- **Name**: `AWS_ACCESS_KEY_ID`
- **Secret**: (실제 AWS Access Key)

#### Secret 2:
- **Name**: `AWS_SECRET_ACCESS_KEY`
- **Secret**: (실제 AWS Secret Key)

## 2단계: AWS Secrets Manager 확인

모든 민감 정보는 이미 AWS Secrets Manager에 저장되어 있습니다:
- journal-api/database
- journal-api/aws-credentials
- journal-api/bedrock

확인: https://console.aws.amazon.com/secretsmanager/home?region=us-east-1

## 3단계: 애플리케이션 배포 (자동)

### 방법:
코드를 수정하고 main 브랜치에 푸시하면 자동으로 배포됩니다:

```bash
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main
```

또는 수동으로 배포:
1. https://github.com/LSH-3016/journal/actions/workflows/deploy.yml 로 이동
2. **Run workflow** 클릭

## 배포 확인

GitHub Actions 탭에서 배포 진행 상황을 실시간으로 확인할 수 있습니다:
- https://github.com/LSH-3016/journal/actions

## 트러블슈팅

### "Credentials could not be loaded" 에러
→ 1단계의 GitHub Secrets 설정을 확인하세요

### Secrets Manager 접근 에러
→ IAM Role이 올바르게 설정되었는지 확인하세요

### 배포 실패
→ GitHub Actions 로그를 확인하고 에러 메시지를 확인하세요

## 현재 AWS 리소스

- **EKS 클러스터**: fproject-dev-eks
- **ECR 리포지토리**: fproject-dev-api
- **RDS**: fproject-dev-postgres
- **S3 버킷**: knowledge-base-test-6575574
