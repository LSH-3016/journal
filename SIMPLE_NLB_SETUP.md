# 기존 NLB 사용하여 API 노출

## 현재 상황
- 기존 NLB: `a3c22a2b065a64df888bad01f3cffa1a-c1fe9d883c1c6510.elb.us-east-1.amazonaws.com`
- 새 NLB 생성 실패
- Service: NodePort로 변경 (포트 32000)

## 해결 방법: 기존 NLB에 리스너 추가

### 1단계: Target Group 생성

AWS Console > EC2 > Target Groups > Create target group

**설정:**
- Target type: `Instances`
- Target group name: `journal-api-tg`
- Protocol: `TCP`
- Port: `32000`
- VPC: EKS 클러스터와 동일한 VPC 선택
- Health check:
  - Protocol: `HTTP`
  - Path: `/health`
  - Port: `32000`

**Targets 등록:**
- EKS 워커 노드 인스턴스 선택 (i-0950a453277a34041, i-0e5874f12374f7f8e)
- Port: `32000`
- "Include as pending below" 클릭
- "Create target group" 클릭

### 2단계: NLB에 리스너 추가

AWS Console > EC2 > Load Balancers > `a3c22a2b065a64df888bad01f3cffa1a` 선택

**Listeners 탭:**
1. "Add listener" 클릭
2. 설정:
   - Protocol: `TCP`
   - Port: `8000`
   - Default action: Forward to `journal-api-tg`
3. "Add" 클릭

### 3단계: Security Group 확인

**워커 노드 Security Group:**
- Inbound rule 추가:
  - Type: `Custom TCP`
  - Port: `32000`
  - Source: NLB Security Group

### 4단계: 접근 테스트

```bash
# NLB DNS로 직접 접근
curl http://a3c22a2b065a64df888bad01f3cffa1a-c1fe9d883c1c6510.elb.us-east-1.amazonaws.com:8000/health

# 또는 Route 53 설정 후
curl http://journal.aws11.shop:8000/health
```

## 대안: Ingress 사용 (권장)

기존 NLB 대신 Ingress를 사용하는 것이 더 깔끔합니다.

### 필요 사항:
1. AWS Load Balancer Controller 설치
2. Ingress 배포

### 장점:
- 호스트 기반 라우팅
- SSL/TLS 자동 관리
- 경로 기반 라우팅
- 여러 서비스를 하나의 ALB로 통합

## 가장 간단한 방법: CloudFront 사용

S3 웹사이트와 API를 CloudFront로 통합:

### 1. CloudFront Distribution 생성

**Origins:**
1. S3 웹사이트: `www.aws11.shop.s3-website-us-east-1.amazonaws.com`
2. API (NLB): `a3c22a2b065a64df888bad01f3cffa1a-c1fe9d883c1c6510.elb.us-east-1.amazonaws.com:8000`

**Behaviors:**
- Default: S3 웹사이트
- `/api/*`: NLB (API)

### 2. S3에서 API 호출

```javascript
// 같은 도메인에서 호출 (CORS 불필요)
fetch('/api/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        user_id: 'user123',
        content: '오늘의 일기'
    })
})
.then(r => r.json())
.then(console.log);
```

## 추천 방법

**단기 (지금 바로):**
- 기존 NLB에 리스너 추가 (위 1-4단계)
- 포트 8000으로 접근

**장기 (프로덕션):**
- AWS Load Balancer Controller 설치
- Ingress 사용
- 또는 CloudFront로 통합
