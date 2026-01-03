# Ingress 설정 가이드

## 현재 상태

- **Service Type**: ClusterIP (내부 전용)
- **외부 접근**: 불가능

## Ingress로 외부 접근 설정

### 1. AWS Load Balancer Controller 설치 확인

먼저 EKS 클러스터에 AWS Load Balancer Controller가 설치되어 있는지 확인:

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

설치되어 있지 않다면 설치 필요:
https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html

### 2. Ingress 배포

`k8s-ingress.yaml` 파일이 준비되어 있습니다:

- **도메인**: api.aws11.shop
- **SSL 인증서**: *.aws11.shop (이미 발급됨)
- **로드밸런서**: 기존 ALB 재사용
- **Health Check**: /health 엔드포인트

배포 방법:
```bash
kubectl apply -f k8s-ingress.yaml
```

또는 GitHub Actions에서 자동 배포됩니다.

### 3. Route 53 설정

Ingress가 생성되면 ALB의 DNS 이름을 확인:

```bash
kubectl get ingress journal-api-ingress
```

Route 53에서 api.aws11.shop을 ALB로 연결:

1. Route 53 콘솔 > aws11.shop 호스팅 영역
2. 레코드 생성:
   - 레코드 이름: `api`
   - 레코드 유형: `A - IPv4 주소`
   - 별칭: `예`
   - 트래픽 라우팅 대상: `Application/Classic Load Balancer에 대한 별칭`
   - 리전: `us-east-1`
   - 로드 밸런서: ALB 선택

### 4. 접근 테스트

```bash
# HTTP (자동으로 HTTPS로 리다이렉트)
curl http://api.aws11.shop/health

# HTTPS
curl https://api.aws11.shop/health

# API 문서
https://api.aws11.shop/docs
```

## 기존 로드밸런서 재사용

현재 로드밸런서가 이미 존재하므로:
- 새로운 ALB를 생성하지 않고 기존 ALB에 리스너 규칙 추가
- 비용 절감
- 관리 간소화

## 트러블슈팅

### Ingress가 생성되지 않음
- AWS Load Balancer Controller 설치 확인
- ServiceAccount의 IAM Role 확인

### 502 Bad Gateway
- Pod가 정상 실행 중인지 확인: `kubectl get pods`
- Health check 경로 확인: `/health`

### SSL 인증서 오류
- ACM 인증서가 us-east-1 리전에 있는지 확인
- 인증서 상태가 "발급됨"인지 확인

## 비용

- ALB: 시간당 $0.0225 + 처리된 데이터 GB당 $0.008
- 기존 ALB 재사용 시 추가 비용 없음
