# AWS Secrets Manager 설정 가이드

## 개요

이 프로젝트는 AWS Secrets Manager를 사용하여 민감한 정보를 안전하게 관리합니다.
Kubernetes Secret 대신 Secrets Manager를 사용하여 더 나은 보안과 관리 편의성을 제공합니다.

## 이미 설정된 Secrets

다음 secrets가 AWS Secrets Manager에 이미 생성되어 있습니다:

1. **journal-api/database** - 데이터베이스 연결 정보
   - host, port, dbname, username, password

2. **journal-api/aws-credentials** - AWS 자격 증명
   - access_key_id, secret_access_key

3. **journal-api/bedrock** - Bedrock 설정
   - flow_arn, flow_alias

## IAM Role 설정

EKS Pod가 Secrets Manager에 접근할 수 있도록 IAM Role이 설정되어 있습니다:

- **Role**: journal-api-secrets-role
- **Policy**: JournalApiSecretsPolicy
- **ServiceAccount**: journal-api-sa (k8s-deployment.yaml에 정의됨)

## Secret 값 확인/수정

### AWS CLI로 확인:
```bash
aws secretsmanager get-secret-value --secret-id journal-api/database --region us-east-1
aws secretsmanager get-secret-value --secret-id journal-api/aws-credentials --region us-east-1
aws secretsmanager get-secret-value --secret-id journal-api/bedrock --region us-east-1
```

### AWS Console에서 확인:
https://console.aws.amazon.com/secretsmanager/home?region=us-east-1

### Secret 값 업데이트:
```bash
aws secretsmanager update-secret \
  --secret-id journal-api/database \
  --secret-string '{"host":"new-host","port":"5432","dbname":"db","username":"user","password":"pass"}' \
  --region us-east-1
```

업데이트 후 Pod 재시작 (GitHub Actions 사용):
1. https://github.com/LSH-3016/journal/actions/workflows/deploy.yml
2. "Run workflow" 클릭

## 로컬 개발

로컬에서는 `.env` 파일의 환경변수를 사용합니다.
`config.py`가 자동으로 환경을 감지하여 적절한 소스에서 설정을 가져옵니다:

- **ENVIRONMENT=production**: AWS Secrets Manager 사용
- **ENVIRONMENT=development**: .env 파일 사용

## 보안 장점

1. **중앙 집중식 관리**: 모든 secrets를 한 곳에서 관리
2. **자동 암호화**: AWS KMS로 자동 암호화
3. **접근 제어**: IAM으로 세밀한 권한 관리
4. **감사 로그**: CloudTrail로 접근 기록 추적
5. **버전 관리**: Secret 변경 이력 자동 저장
6. **자동 로테이션**: 비밀번호 자동 교체 가능

## 비용

AWS Secrets Manager 비용:
- Secret 저장: $0.40/월 per secret
- API 호출: $0.05 per 10,000 calls

현재 3개 secrets = 약 $1.20/월
