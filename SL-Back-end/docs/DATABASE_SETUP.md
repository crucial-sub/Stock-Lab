# 데이터베이스 설정 가이드

## 문제 상황
```
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation
```

이 에러는 다음 중 하나의 이유로 발생합니다:
1. PostgreSQL 서버가 실행되지 않음
2. 데이터베이스가 존재하지 않음
3. 테이블 스키마가 코드와 맞지 않음 (Integer ID → UUID 변경)

---

## 1. PostgreSQL 서버 시작

### Windows

#### 방법 1: Services (서비스) 사용
1. `Win + R` → `services.msc` 입력
2. "postgresql" 서비스 찾기
3. 우클릭 → "시작" 선택

#### 방법 2: 명령어 사용
```bash
# PostgreSQL이 설치된 경로에서 실행
"C:/Program Files/PostgreSQL/16/bin/pg_ctl" start -D "C:/Program Files/PostgreSQL/16/data"
```

#### 방법 3: pgAdmin 사용
1. pgAdmin 4 실행
2. Servers → PostgreSQL 16 → 우클릭 → Connect

### 서버 상태 확인
```bash
# psql 접속 시도
psql -U postgres -d quant_investment_db

# 또는
psql -U postgres -h localhost -p 5432
```

---

## 2. 데이터베이스 생성 (필요한 경우)

```bash
# psql에 postgres 계정으로 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE quant_investment_db;

# 데이터베이스 목록 확인
\l

# 특정 데이터베이스로 전환
\c quant_investment_db

# 종료
\q
```

---

## 3. Users 테이블 UUID 마이그레이션

### ⚠️ 주의사항
- **기존 데이터는 모두 삭제됩니다!**
- 프로덕션 환경에서는 백업 필수!

### 마이그레이션 실행

#### 방법 1: psql 명령어 사용
```bash
# SL-Back-end 디렉토리에서 실행
psql -U postgres -d quant_investment_db -f migrate_users_to_uuid.sql
```

#### 방법 2: SQL 파일 직접 복사
1. `migrate_users_to_uuid.sql` 파일 내용 복사
2. psql 또는 pgAdmin 쿼리 도구에서 실행

#### 방법 3: pgAdmin 사용
1. pgAdmin 4 실행
2. Servers → PostgreSQL 16 → Databases → quant_investment_db
3. 우클릭 → Query Tool
4. `migrate_users_to_uuid.sql` 파일 열기 (File → Open)
5. F5 또는 실행 버튼 클릭

### 마이그레이션 확인
```sql
-- 테이블 구조 확인
\d users

-- 또는
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- UUID 확장 확인
SELECT * FROM pg_extension WHERE extname = 'uuid-ossp';
```

예상 결과:
```
 column_name     | data_type                   | is_nullable | column_default
-----------------+-----------------------------+-------------+------------------
 id              | uuid                        | NO          | gen_random_uuid()
 name            | character varying           | NO          |
 email           | character varying           | NO          |
 phone_number    | character varying           | NO          |
 hashed_password | character varying           | NO          |
 is_active       | boolean                     | NO          | true
 is_superuser    | boolean                     | NO          | false
 created_at      | timestamp with time zone    | NO          | now()
 updated_at      | timestamp with time zone    | NO          | now()
```

---

## 4. 연결 정보 확인

`.env` 파일에서 데이터베이스 연결 정보를 확인하세요:

```env
DATABASE_URL=postgresql+asyncpg://postgres:gudgh@localhost:5432/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:gudgh@localhost:5432/quant_investment_db
```

### 연결 정보
- **호스트**: localhost
- **포트**: 5432
- **사용자**: postgres
- **비밀번호**: gudgh
- **데이터베이스**: quant_investment_db

### 연결 테스트
```bash
# psql로 연결 테스트
psql -U postgres -h localhost -p 5432 -d quant_investment_db

# 비밀번호 입력: gudgh
```

---

## 5. 서버 재시작

마이그레이션 완료 후 FastAPI 서버를 재시작하세요:

```bash
# Ctrl+C로 서버 중지 후
venv/Scripts/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 6. 테스트

### Swagger UI에서 테스트
1. 브라우저에서 `http://localhost:8000/docs` 접속
2. `POST /api/v1/auth/register` 엔드포인트 선택
3. 테스트 데이터 입력:
```json
{
  "name": "테스트유저",
  "email": "test@example.com",
  "phone_number": "01012345678",
  "password": "password123"
}
```
4. Execute 클릭

### 예상 응답 (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "테스트유저",
  "email": "test@example.com",
  "phone_number": "01012345678",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-05T12:00:00Z"
}
```

---

## 7. Redis 설정 (선택사항)

Redis 연결 실패는 캐시 기능에만 영향을 미치며, 앱은 정상 작동합니다.

Redis를 사용하려면:

### Windows에서 Redis 설치
```bash
# Chocolatey 사용
choco install redis-64

# 또는 WSL 사용
wsl
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### Redis 서버 시작
```bash
redis-server
```

### Redis 연결 확인
```bash
redis-cli ping
# 응답: PONG
```

---

## 문제 해결

### 1. "database does not exist" 에러
```bash
psql -U postgres
CREATE DATABASE quant_investment_db;
\q
```

### 2. "password authentication failed" 에러
- `.env` 파일의 비밀번호 확인
- PostgreSQL 비밀번호 재설정:
```bash
psql -U postgres
ALTER USER postgres WITH PASSWORD 'gudgh';
```

### 3. "connection refused" 에러
- PostgreSQL 서버가 실행 중인지 확인
- 방화벽 설정 확인
- `pg_hba.conf` 파일에서 localhost 접근 허용 확인

### 4. "role does not exist" 에러
```bash
# postgres 계정으로 접속
psql -U postgres
CREATE USER postgres WITH PASSWORD 'gudgh';
ALTER USER postgres WITH SUPERUSER;
```

### 5. UUID 확장 에러
```sql
-- psql에서 실행
\c quant_investment_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## 빠른 설정 체크리스트

- [ ] PostgreSQL 서버 실행 중
- [ ] `quant_investment_db` 데이터베이스 존재
- [ ] UUID 확장 설치됨
- [ ] Users 테이블이 UUID로 생성됨
- [ ] `.env` 파일의 연결 정보 정확함
- [ ] FastAPI 서버 재시작
- [ ] Swagger UI에서 회원가입 테스트 성공

---

## 추가 도움말

### PostgreSQL 기본 명령어
```sql
-- 데이터베이스 목록
\l

-- 테이블 목록
\dt

-- 테이블 구조 확인
\d users

-- 데이터 조회
SELECT * FROM users;

-- 데이터 삭제
DELETE FROM users;

-- 테이블 삭제
DROP TABLE users;

-- 종료
\q
```

### 모든 것을 처음부터
```bash
# 1. PostgreSQL 접속
psql -U postgres

# 2. 데이터베이스 재생성
DROP DATABASE IF EXISTS quant_investment_db;
CREATE DATABASE quant_investment_db;
\c quant_investment_db

# 3. UUID 확장 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# 4. 종료
\q

# 5. 마이그레이션 스크립트 실행
psql -U postgres -d quant_investment_db -f migrate_users_to_uuid.sql

# 6. 서버 재시작
venv/Scripts/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 문의

문제가 계속되면 다음 정보를 함께 제공해주세요:
- PostgreSQL 버전: `psql --version`
- 서버 로그: 콘솔의 전체 에러 메시지
- `.env` 파일의 DATABASE_URL (비밀번호 제외)
- 테이블 구조: `\d users` 결과
