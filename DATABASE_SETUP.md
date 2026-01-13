# PostgreSQL 데이터베이스 설정

## 1. 의존성 설치

```bash
pip install -r requirements.txt
```

## 2. PostgreSQL 설치 및 데이터베이스 생성

```sql
-- PostgreSQL에 접속 후 데이터베이스 생성
CREATE DATABASE chatdb;
CREATE USER chatuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chatdb TO chatuser;
```

## 3. 환경변수 설정

`.env` 파일을 수정하여 실제 데이터베이스 정보를 입력:

### 방법 1: 전체 URL 사용 (권장)
```
DATABASE_URL=postgresql://chatuser:your_password@localhost:5432/chatdb
```

### 방법 2: 개별 환경변수 사용
```
# DATABASE_URL을 주석처리하고 아래 사용
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatdb
DB_USER=chatuser
DB_PASSWORD=your_password
```

## 4. 애플리케이션 실행

```bash
uvicorn main:app --reload
```

## 5. API 테스트

- Swagger UI: http://localhost:8000/journal/docs
- 채팅 메시지 조회: GET /journal/messages
- 메시지 생성: POST /journal/messages

## 주의사항

- `.env` 파일은 git에 커밋되지 않습니다 (보안상 안전)
- `.env.example` 파일을 참고하여 설정하세요
- 실제 운영환경에서는 환경변수를 직접 설정하는 것을 권장합니다