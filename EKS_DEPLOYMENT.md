# EKS 배포 가이드

## 사전 준비사항

### 1. Docker 이미지 빌드 및 푸시
```bash
# Docker 이미지 빌드
docker build -t journal-api:latest .

# ECR에 푸시 (예시)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag journal-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/journal-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/journal-api:latest
```

### 2. 환경변수 설정
`k8s-deployment.yaml` 파일에서 다음 값들을 실제 값으로 수정:

#### Secret 값들:
- `db-host`: PostgreSQL 호스트 주소
- `db-user`: 데이터베이스 사용자명
- `db-password`: 데이터베이스 비밀번호
- `aws-access-key-id`: AWS 액세스 키
- `aws-secret-access-key`: AWS 시크릿 키
- `bedrock-flow-arn`: Bedrock Flow ARN
- `bedrock-flow-alias`: Bedrock Flow 별칭

#### ConfigMap 값들:
- `s3-bucket-name`: S3 버킷 이름
- `bedrock-model-id`: Bedrock 모델 ID

### 3. 이미지 레지스트리 주소 수정
`k8s-deployment.yaml`에서 `image: your-registry/journal-api:latest`를 실제 이미지 주소로 변경

## 배포 명령어

### 1. Kubernetes 리소스 배포
```bash
kubectl apply -f k8s-deployment.yaml
```

### 2. 배포 상태 확인
```bash
# Pod 상태 확인
kubectl get pods -l app=journal-api

# 서비스 상태 확인
kubectl get svc journal-api-service

# 로그 확인
kubectl logs -l app=journal-api
```

### 3. 서비스 접근
```bash
# 포트 포워딩으로 테스트
kubectl port-forward svc/journal-api-service 8080:80

# 헬스체크 테스트
curl http://localhost:8080/health
```

## 프로덕션 고려사항

### 1. Ingress 설정
외부 접근을 위해 Ingress 컨트롤러 설정:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: journal-api-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: journal-api-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: journal-api-service
            port:
              number: 80
```

### 2. HPA (Horizontal Pod Autoscaler) 설정
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: journal-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: journal-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 3. 환경변수 관리
- AWS Secrets Manager 또는 External Secrets Operator 사용 권장
- 민감한 정보는 Kubernetes Secret으로 관리

### 4. 모니터링 설정
- Prometheus + Grafana 설정
- CloudWatch 로그 수집 설정
- 애플리케이션 메트릭 추가

## 트러블슈팅

### 1. Pod가 시작되지 않는 경우
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### 2. 데이터베이스 연결 실패
- Secret의 데이터베이스 정보 확인
- 네트워크 정책 및 보안 그룹 확인

### 3. AWS 서비스 접근 실패
- IAM 권한 확인
- AWS 자격 증명 확인
- 리전 설정 확인

## 롤백 방법
```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/journal-api

# 특정 리비전으로 롤백
kubectl rollout undo deployment/journal-api --to-revision=2
```