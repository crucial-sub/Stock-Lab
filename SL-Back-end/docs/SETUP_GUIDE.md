# SL-Back-Test 백엔드 설정 가이드

## 🚨 Python 버전 호환성 문제 해결

현재 Python 3.13을 사용 중이신데, numpy와 일부 패키지들이 아직 Python 3.13을 완전히 지원하지 않습니다.

### 해결 방법 1: Python 3.11 사용 (권장)

```bash
# 1. Python 3.11 설치 (Homebrew 사용)
brew install python@3.11

# 2. 가상환경 생성
python3.11 -m venv venv

# 3. 가상환경 활성화
source venv/bin/activate

# 4. pip 업그레이드
pip install --upgrade pip setuptools wheel

# 5. 의존성 설치
pip install -r requirements_stable.txt
```

### 해결 방법 2: Python 3.13 호환 패키지 설치

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 2. pip 업그레이드
pip install --upgrade pip setuptools wheel

# 3. 호환 가능한 패키지만 먼저 설치
pip install -r requirements_minimal.txt

# 4. numpy를 소스에서 빌드 (시간이 오래 걸림)
pip install numpy --no-binary :all: --no-cache-dir
```

## 📦 필수 패키지 설치 파일 생성

### requirements_stable.txt (Python 3.11용)
```txt
# FastAPI Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Data Processing
pandas==2.1.4
numpy==1.24.3
polars==0.20.0
pyarrow==14.0.0

# Caching
redis==5.0.1
aiocache==0.12.2

# API Utilities
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Logging
loguru==0.7.2

# JSON
orjson==3.9.12
ujson==5.9.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

### requirements_minimal.txt (Python 3.13 최소 설치용)
```txt
# FastAPI Core Only
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Basic Database
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.25
psycopg2-binary==2.9.9

# Minimal Data Processing
polars==1.15.0

# Caching
redis==5.0.1

# Utilities
python-dotenv==1.0.0
orjson==3.9.12
httpx==0.26.0
```

## 🐳 Docker를 사용한 환경 설정 (권장)

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      POSTGRES_DB: quant_investment_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres123@postgres:5432/quant_investment_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements_stable.txt .
RUN pip install --no-cache-dir -r requirements_stable.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🚀 빠른 시작 명령어

### 옵션 1: Docker 사용 (가장 쉬움)
```bash
cd SL-Back-Test

# Docker Compose로 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# API 문서 접속
open http://localhost:8000/docs
```

### 옵션 2: Python 3.11 로컬 설치
```bash
cd SL-Back-Test

# Python 3.11 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate

# 안정적인 패키지 설치
pip install -r requirements_stable.txt

# PostgreSQL과 Redis가 실행 중인지 확인
brew services start postgresql@15
brew services start redis

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 옵션 3: 최소 설치 (Python 3.13)
```bash
cd SL-Back-Test

# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 최소 패키지만 설치
pip install -r requirements_minimal.txt

# 서버 실행 (일부 기능 제한)
uvicorn app.main:app --reload --port 8000
```

## ✅ 설치 확인

```bash
# 1. API 헬스체크
curl http://localhost:8000/health

# 2. API 문서 확인
open http://localhost:8000/docs

# 3. 데이터베이스 연결 테스트
curl http://localhost:8000/api/v1/factors/list

# 4. Frontend 연동 테스트
cd ../SL-Front-End
npm run dev
# http://localhost:3000 접속
```

## 🔧 문제 해결

### 1. numpy 빌드 실패
```bash
# Xcode Command Line Tools 설치
xcode-select --install

# brew로 필요한 라이브러리 설치
brew install openblas gfortran

# numpy 재설치
pip install numpy --no-binary numpy --no-cache-dir
```

### 2. PostgreSQL 연결 실패
```bash
# PostgreSQL 상태 확인
brew services list | grep postgresql

# PostgreSQL 시작
brew services start postgresql@15

# 데이터베이스 생성
createdb quant_investment_db
```

### 3. Redis 연결 실패
```bash
# Redis 상태 확인
brew services list | grep redis

# Redis 시작
brew services start redis

# Redis 연결 테스트
redis-cli ping
```

## 📝 환경 변수 설정

`.env` 파일이 이미 설정되어 있습니다:
- DATABASE_URL: PostgreSQL 연결 정보
- REDIS_URL: Redis 캐시 서버
- BACKEND_CORS_ORIGINS: Frontend URL (http://localhost:3000)

## 🎯 다음 단계

1. 백엔드 서버 시작 확인
2. Frontend 서버와 연동 테스트
3. 백테스트 기능 실행 테스트

---

최종 업데이트: 2025-11-04