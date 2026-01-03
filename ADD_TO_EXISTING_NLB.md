# 기존 NLB에 journal-api 추가하기

## 현재 상황
- 기존 NLB: `a3c22a2b065a64df888bad01f3cffa1a`
- 기존 API: 80/443 포트 사용 중
- journal-api: 새로 추가 필요

## 방법 1: 다른 포트 사용 (권장)

### 1단계: Service를 NodePort로 변경 (이미 완료)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: journal-api-service
spec:
  type: NodePort
  ports:
    - port: 8000
      targetPort: 8000
      nodePort: 32000  # 30000-32767 범위
```

### 2단계: Target Group 생성

AWS Console > EC2 > Target Groups:

1. **"Create target group"** 클릭
2. 설정:
   - **Target type**: `Instances`
   - **Target group name**: `journal-api-tg`
   - **Protocol**: `TCP`
   - **Port**: `32000`
   - **VPC**: EKS 클러스터와 동일한 VPC 선택
   - **Health check protocol**: `HTTP`
   - **Health check path**: `/health`
3. **"Next"** 클릭
4. **EKS 워커 노드 선택**:
   - EC2 인스턴스 목록에서 EKS 노드 선택
   - Port: `32000`
5. **"Create target group"** 클릭

### 3단계: NLB에 리스너 추가

AWS Console > EC2 > Load Balancers > `a3c22a2b065a64df888bad01f3cffa1a`:

1. **"Listeners" 탭** 클릭
2. **"Add listener"** 클릭
3. 설정:
   - **Protocol**: `TCP`
   - **Port**: `8000`
   - **Default action**: Forward to `journal-api-tg`
4. **"Add"** 클릭

### 4단계: Route 53 설정

1. Route 53 > aws11.shop 호스팅 영역
2. 레코드 생성:
   - **이름**: `journal`
   - **타입**: `CNAME`
   - **값**: `a3c22a2b065a64df888bad01f3cffa1a-c1fe9d883c1c6510.elb.us-east-1.amazonaws.com`

### 5단계: 접근

```
http://journal.aws11.shop:8000/health
http://journal.aws11.shop:8000/docs
```

## 방법 2: 새로운 NLB 생성

Service를 LoadBalancer 타입으로 변경하고 새로운 NLB 생성:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: journal-api-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8000
```

장점: 독립적인 로드밸런서
단점: 추가 비용 ($0.0225/시간)

## 방법 3: Ingress 사용 (ALB Controller 필요)

ALB Controller를 설치하고 Ingress로 호스트 기반 라우팅:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: journal-api-ingress
spec:
  rules:
  - host: journal.aws11.shop
    http:
      paths:
      - path: /
        backend:
          service:
            name: journal-api-service
            port:
              number: 8000
```

장점: 호스트 기반 라우팅, 80/443 포트 사용
단점: ALB Controller 설치 필요

## 권장 방법

**개발/테스트**: 방법 1 (다른 포트 사용)
- 빠르고 간단
- 추가 비용 없음
- 포트 번호 필요 (예: :8000)

**프로덕션**: 방법 3 (Ingress + ALB)
- 표준 포트 (80/443) 사용
- 호스트 기반 라우팅
- SSL/TLS 종료
- 더 많은 기능

## EKS 워커 노드 찾기

```bash
# CLI로 확인
aws ec2 describe-instances \
  --filters "Name=tag:eks:cluster-name,Values=fproject-dev-eks" \
  --query "Reservations[*].Instances[*].[InstanceId,PrivateIpAddress,State.Name]" \
  --output table
```

또는 EC2 Console에서:
- 태그 필터: `eks:cluster-name = fproject-dev-eks`
