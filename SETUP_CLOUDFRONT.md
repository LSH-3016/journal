# CloudFront로 HTTPS 지원 추가

## 문제
- S3 웹사이트: `https://www.aws11.shop` (HTTPS)
- API: `http://journal.aws11.shop:8000` (HTTP)
- Mixed Content 에러 발생

## 해결: CloudFront 사용

### 1단계: CloudFront Distribution 생성

AWS Console > CloudFront > Create distribution:

#### Origin settings:
- **Origin domain**: `a3c22a2b065a64df888bad01f3cffa1a-c1fe9d883c1c6510.elb.us-east-1.amazonaws.com`
- **Protocol**: `HTTP only`
- **HTTP port**: `8000`
- **Origin path**: 비워두기

#### Default cache behavior:
- **Viewer protocol policy**: `Redirect HTTP to HTTPS`
- **Allowed HTTP methods**: `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`
- **Cache policy**: `CachingDisabled` (API이므로 캐싱 비활성화)
- **Origin request policy**: `AllViewer`

#### Settings:
- **Alternate domain names (CNAMEs)**: `journal.aws11.shop`
- **Custom SSL certificate**: `*.aws11.shop` 인증서 선택
- **Supported HTTP versions**: `HTTP/2`

#### 생성 클릭

### 2단계: Route 53 업데이트

Route 53 > aws11.shop 호스팅 영역:

1. `journal` 레코드 생성 (또는 수정)
2. 설정:
   - **Record name**: `journal`
   - **Record type**: `A`
   - **Alias**: `예`
   - **Route traffic to**: `Alias to CloudFront distribution`
   - **Distribution**: 방금 생성한 CloudFront 선택

### 3단계: JavaScript 코드 업데이트

```javascript
// 변경 전
const API_BASE_URL = 'http://journal.aws11.shop:8000';

// 변경 후
const API_BASE_URL = 'https://journal.aws11.shop';
```

### 4단계: 테스트

```
https://journal.aws11.shop/health
https://journal.aws11.shop/docs
```

## 장점

- ✅ HTTPS 지원 (Mixed Content 해결)
- ✅ 포트 번호 불필요 (443 기본)
- ✅ SSL 인증서 자동 관리
- ✅ 글로벌 CDN (빠른 응답)
- ✅ DDoS 방어

## 비용

- CloudFront: 데이터 전송량 기준
  - 첫 10TB: $0.085/GB
  - HTTP 요청: $0.0075 per 10,000 requests
- 예상: 월 $5-20 (트래픽에 따라)

## 대안: ALB + ACM

ALB를 사용하면 SSL을 직접 종료할 수 있지만, ALB Controller 설치가 필요합니다.

## 주의사항

CloudFront 배포 후 전파까지 10-15분 소요됩니다.
