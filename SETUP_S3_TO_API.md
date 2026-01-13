# S3 웹 호스팅에서 API 호출 설정

## 현재 상태
- API 배포: 완료 ✅
- NLB 생성: 진행 중 (EXTERNAL-IP pending)
- S3 웹 호스팅: www.aws11.shop

## 1단계: NLB DNS 확인

몇 분 후 다음 명령어로 확인:

```bash
kubectl get svc journal-api-service
```

출력 예시:
```
NAME                  TYPE           EXTERNAL-IP
journal-api-service   LoadBalancer   a1234567890.us-east-1.elb.amazonaws.com
```

## 2단계: Route 53 설정

### 방법 A: CNAME 레코드 (권장)

1. Route 53 콘솔: https://console.aws.amazon.com/route53/v2/hostedzones
2. `aws11.shop` 호스팅 영역 선택
3. "레코드 생성" 클릭
4. 설정:
   - **레코드 이름**: `journal`
   - **레코드 유형**: `CNAME`
   - **값**: NLB DNS 이름 (예: `a1234567890.us-east-1.elb.amazonaws.com`)
   - **TTL**: `300`
5. "레코드 생성" 클릭

### 방법 B: Alias 레코드

1. "레코드 생성" 클릭
2. 설정:
   - **레코드 이름**: `journal`
   - **레코드 유형**: `A`
   - **별칭**: `예`
   - **트래픽 라우팅 대상**: `Network Load Balancer에 대한 별칭`
   - **리전**: `us-east-1`
   - **로드 밸런서**: NLB 선택
3. "레코드 생성" 클릭

## 3단계: CORS 설정 확인

API의 CORS가 이미 설정되어 있습니다:

```python
# main.py
ALLOWED_ORIGINS = "*"  # 모든 origin 허용
```

프로덕션에서는 특정 도메인만 허용하도록 변경:

```yaml
# k8s-deployment.yaml
- name: ALLOWED_ORIGINS
  value: "https://www.aws11.shop,https://aws11.shop"
```

## 4단계: S3 웹사이트에서 API 호출

### JavaScript 예시:

```javascript
// API 기본 URL
const API_BASE_URL = 'https://api.aws11.shop/journal';

// 메시지 전송
async function sendMessage(content) {
    try {
        const response = await fetch(`${API_BASE_URL}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: 'user123',
                content: content
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Success:', data);
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// 히스토리 조회
async function getHistory(userId, date) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/history/${userId}?date=${date}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// 사용 예시
document.getElementById('sendBtn').addEventListener('click', async () => {
    const content = document.getElementById('messageInput').value;
    try {
        const result = await sendMessage(content);
        alert('메시지 전송 완료!');
    } catch (error) {
        alert('전송 실패: ' + error.message);
    }
});
```

### Fetch API 옵션:

```javascript
// GET 요청
fetch('https://api.aws11.shop/journal/health')
    .then(response => response.json())
    .then(data => console.log(data));

// POST 요청
fetch('https://api.aws11.shop/journal/messages', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        user_id: 'user123',
        content: '오늘의 일기'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Axios 사용:

```javascript
// Axios 설치 (HTML에 추가)
// <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>

const api = axios.create({
    baseURL: 'https://api.aws11.shop/journal',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 메시지 전송
api.post('/messages', {
    user_id: 'user123',
    content: '오늘의 일기'
})
.then(response => {
    console.log('Success:', response.data);
})
.catch(error => {
    console.error('Error:', error);
});

// 히스토리 조회
api.get('/history/user123', {
    params: { date: '2026-01-03' }
})
.then(response => {
    console.log('History:', response.data);
})
.catch(error => {
    console.error('Error:', error);
});
```

## 5단계: API 엔드포인트 목록

### 메시지 관련:
- `POST /journal/messages` - 메시지 전송
- `GET /journal/messages/{user_id}` - 메시지 목록 조회

### 히스토리 관련:
- `GET /journal/history/{user_id}` - 히스토리 조회
- `POST /journal/history` - 히스토리 생성
- `DELETE /journal/history/{history_id}` - 히스토리 삭제

### 요약 관련:
- `POST /journal/summary` - 요약 생성

### Flow 관련:
- `POST /journal/process` - Flow 호출

### 기타:
- `GET /journal/health` - 헬스체크
- `GET /journal/docs` - API 문서 (Swagger UI)

## 6단계: 테스트

### 브라우저 콘솔에서 테스트:

```javascript
// 헬스체크
fetch('https://api.aws11.shop/journal/health')
    .then(r => r.json())
    .then(console.log);

// API 문서 확인
window.open('https://api.aws11.shop/journal/docs', '_blank');
```

## 7단계: 프로덕션 보안 설정

### CORS 제한:

```yaml
# k8s/k8s-deployment.yaml
- name: ALLOWED_ORIGINS
  value: "https://www.aws11.shop,https://api.aws11.shop"
```

### HTTPS 강제:

S3 웹사이트가 HTTPS를 사용하는지 확인하고, API도 HTTPS로만 호출하세요.

## 트러블슈팅

### CORS 에러:
```
Access to fetch at 'https://journal.aws11.shop' from origin 'https://www.aws11.shop' 
has been blocked by CORS policy
```

**해결:** ALLOWED_ORIGINS에 S3 웹사이트 도메인 추가

### 연결 실패:
```
Failed to fetch
```

**확인:**
1. NLB가 생성되었는지: `kubectl get svc`
2. Route 53 레코드가 올바른지
3. Pod가 실행 중인지: `kubectl get pods`

### 타임아웃:
```
Request timeout
```

**확인:**
1. Security Group에서 80 포트 허용 확인
2. Pod 로그 확인: `kubectl logs -l app=journal-api`

## 완료 체크리스트

- [ ] NLB EXTERNAL-IP 확인
- [ ] Route 53 레코드 생성 (journal.aws11.shop)
- [ ] DNS 전파 확인 (1-2분)
- [ ] 브라우저에서 https://api.aws11.shop/journal/health 접속
- [ ] S3 웹사이트에서 API 호출 테스트
- [ ] CORS 설정 확인
