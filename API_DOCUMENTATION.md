# Journal API 명세서

## 개요
일기 및 메시지 관리를 위한 FastAPI 기반 백엔드 서비스입니다.
- **메시지**: 일일 기록을 위한 짧은 텍스트 (DB만 저장)
- **히스토리**: 요약된 일기 내용 (DB + S3 저장)
- **Flow**: Bedrock Flow를 통한 지능형 분류 및 처리
- **요약**: AI 기반 메시지 요약 기능

---

## 1. Messages API (`/messages`)

### 1.1 메시지 생성
```http
POST /messages
Content-Type: application/json

{
  "user_id": "user_001",
  "content": "오늘 아침 7시에 기상했다"
}
```

**응답:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_001", 
  "content": "오늘 아침 7시에 기상했다",
  "created_at": "2026-01-01T10:30:00Z"
}
```

### 1.2 메시지 조회 (오늘 날짜만)
```http
GET /messages?user_id=user_001&limit=100&offset=0
```

**응답:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_001",
    "content": "오늘 아침 7시에 기상했다", 
    "created_at": "2026-01-01T10:30:00Z"
  }
]
```

### 1.3 메시지 내용만 조회 (콤마 구분)
```http
GET /messages/content?user_id=user_001
```

**응답:**
```json
{
  "contents": "7시 기상, 아침 운동, 회사 출근, 점심 회의"
}
```

### 1.4 전체 메시지 조회 (디버그용)
```http
GET /messages/debug/all?user_id=user_001
```

### 1.5 메시지 날짜 정보 확인 (디버그용)
```http
GET /messages/debug/dates
```

### 1.6 특정 메시지 조회
```http
GET /messages/{message_id}
```

### 1.7 메시지 삭제
```http
DELETE /messages/{message_id}
```

---

## 2. History API (`/history`)

### 2.1 히스토리 생성/업데이트
```http
POST /history
Content-Type: application/json

{
  "user_id": "user_001",
  "content": "오늘은 일찍 일어나서 운동을 했다. 회사에서 중요한 회의가 있었고...",
  "record_date": "2026-01-01",
  "tags": ["운동", "회의"],
  "s3_key": "https://example.com/image.jpg"
}
```

**응답:**
```json
{
  "id": 1,
  "user_id": "user_001",
  "content": "오늘은 일찍 일어나서...",
  "record_date": "2026-01-01", 
  "tags": ["운동", "회의"],
  "s3_key": "https://example.com/image.jpg",
  "text_url": "https://bucket.s3.amazonaws.com/user_001/history/2026/01/2026-01-01.txt"
}
```

### 2.2 히스토리 조회
```http
GET /history?user_id=user_001&start_date=2026-01-01&end_date=2026-01-31&tags=운동,회의&limit=100&offset=0
```

### 2.3 키워드 검색
```http
GET /history/search?user_id=user_001&q=운동&limit=100&offset=0
```

**응답:**
```json
[
  {
    "id": 1,
    "user_id": "user_001",
    "content": "오늘은 일찍 일어나서 운동을 했다...",
    "record_date": "2026-01-01",
    "tags": ["운동", "회의"],
    "s3_key": "https://example.com/image.jpg",
    "text_url": "https://bucket.s3.amazonaws.com/user_001/history/2026/01/2026-01-01.txt"
  }
]
```

### 2.4 태그로 검색
```http
GET /history/tags?user_id=user_001&tags=운동,회의&limit=100&offset=0
```

### 2.5 날짜 범위로 조회
```http
GET /history/date-range?user_id=user_001&start_date=2026-01-01&end_date=2026-01-31&limit=100&offset=0
```

### 2.6 모든 태그 목록 조회
```http
GET /history/tags/list?user_id=user_001
```

**응답:**
```json
{
  "user_id": "user_001",
  "tags": ["개발", "운동", "회의", "학습"],
  "count": 4
}
```

### 2.7 날짜별 S3 키 확인
```http
GET /history/check-s3-by-date?user_id=user_001&record_date=2026-01-01
```

### 2.7 날짜별 S3 키 확인
```http
GET /history/check-s3-by-date?user_id=user_001&record_date=2026-01-01
```

**응답:**
```json
{
  "found": true,
  "history_id": 1,
  "has_s3_key": true,
  "s3_key": "https://example.com/image.jpg"
}
```

### 2.8 특정 히스토리 조회
```http
GET /history/{history_id}
```

### 2.9 히스토리 수정
```http
PUT /history/{history_id}
```

### 2.10 S3 키 확인
```http
GET /history/{history_id}/check-s3
```

### 2.11 S3 텍스트 내용 조회
```http
GET /history/{history_id}/s3-content
```

### 2.12 히스토리 삭제
```http
DELETE /history/{history_id}
```

**참고:** 히스토리 삭제 시 DB 레코드와 함께 S3의 텍스트 파일(text_url)과 이미지 파일(s3_key)도 자동으로 삭제됩니다.

---

## 3. Flow API (`/process`, `/test`)

### 3.1 지능형 메시지 처리
```http
POST /process
Content-Type: application/json

{
  "user_id": "user_001",
  "content": "7시에 기상했다",
  "record_date": "2026-01-01",
  "tags": ["일상"],
  "s3_key": "https://example.com/image.jpg"
}
```

**데이터인 경우 응답:**
```json
{
  "type": "data",
  "content": "",
  "message": "메시지가 저장되었습니다.",
  "history_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**참고:** 데이터로 판단된 경우 메시지만 저장하고 content는 빈 문자열로 반환됩니다.

**질문인 경우 응답:**
```json
{
  "type": "answer", 
  "content": "2026년 1월 1일에 오전 7시에 일어났습니다.",
  "message": "질문에 대한 답변입니다."
}
```

### 3.2 Flow 테스트
```http
POST /test?content=오늘 몇시에 일어났어?
```

**응답:**
```json
{
  "input": "오늘 몇시에 일어났어?",
  "node_name": "Answer_return",
  "content": "2026년 1월 1일에 오전 7시에 일어났습니다.",
  "is_question": true
}
```

---

## 4. Summary API (`/summary`)

### 4.1 요약 생성 (POST)
```http
POST /summary
Content-Type: application/json

{
  "user_id": "user_001",
  "s3_key": "https://example.com/image.jpg"
}
```

**응답:**
```json
{
  "summary": "오늘은 일찍 일어나서 운동을 하고 회사에 갔다. 중요한 회의가 있었고...",
  "message_count": 5,
  "s3_key": "https://example.com/image.jpg"
}
```

### 4.2 요약 조회 (GET)
```http
GET /summary/user_001?date=2026-01-01&s3_key=https://example.com/image.jpg
```

### 4.3 오늘 요약 존재 확인
```http
GET /summary/check/user_001
```

**응답:**
```json
{
  "exists": true,
  "id": 123,
  "record_date": "2026-01-01",
  "summary": "오늘은 일찍 일어나서...",
  "s3_key": "https://example.com/image.jpg"
}
```

---

## 5. 에러 응답

### 5.1 공통 에러 형식
```json
{
  "detail": "에러 메시지"
}
```

### 5.2 주요 에러 코드
- **400**: 잘못된 요청 (유효하지 않은 데이터)
- **404**: 리소스를 찾을 수 없음
- **500**: 서버 내부 오류 (AI 처리 실패, S3 오류 등)

---

## 6. 환경 설정

### 6.1 필수 환경변수
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=journal_db
DB_USER=username
DB_PASSWORD=password

# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# S3
S3_BUCKET_NAME=your-bucket-name

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Bedrock Flow
BEDROCK_FLOW_ARN=arn:aws:bedrock:us-east-1:account:flow/FLOWID
BEDROCK_FLOW_ALIAS=TSTALIASID
```

### 6.2 서버 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 7. 주요 특징

### 7.1 데이터 분류
- **Flow API**: Bedrock Flow를 통해 입력을 자동으로 "데이터" 또는 "질문"으로 분류
- **데이터**: 메시지 테이블에 저장, content는 빈 문자열로 반환
- **질문**: 저장하지 않고 답변만 반환
- **current_date**: Flow 호출 시 현재 날짜를 함께 전송하여 날짜 기반 처리 지원

### 7.2 저장 방식
- **메시지**: PostgreSQL DB만 저장
- **히스토리**: PostgreSQL DB + S3 텍스트 파일 저장
- **이미지**: S3 URL을 s3_key에 저장
- **텍스트**: S3 텍스트 파일 URL을 text_url에 저장
- **삭제**: 히스토리 삭제 시 DB와 S3 파일(text_url, s3_key) 모두 삭제

### 7.3 시간대 처리
- 모든 날짜 필터링은 한국 시간(KST, UTC+9) 기준
- 메시지 조회 시 오늘 날짜만 반환 (KST 기준)

### 7.4 AI 기능
- **요약**: Claude를 통한 메시지 자동 요약
- **분류**: Bedrock Flow를 통한 지능형 입력 분류
- **답변**: 질문에 대한 자동 응답 생성

### 7.5 검색 기능
- **키워드 검색**: content 필드에서 키워드 검색 (대소문자 구분 없음)
- **태그 검색**: 하나 이상의 태그로 히스토리 필터링
- **날짜 범위 검색**: 시작일과 종료일 사이의 히스토리 조회
- **태그 목록**: 사용자의 모든 고유 태그 목록 조회