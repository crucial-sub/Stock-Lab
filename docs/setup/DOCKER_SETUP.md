# Docker 기반 개발 환경 설정 가이드

## 목차
1. [개요](#개요)
2. [사전 요구사항](#사전-요구사항)
3. [프로젝트 구조](#프로젝트-구조)
4. [환경 변수 설정](#환경-변수-설정)
5. [개발 환경 실행](#개발-환경-실행)
6. [프로덕션 환경 실행](#프로덕션-환경-실행)
7. [유용한 명령어](#유용한-명령어)
8. [트러블슈팅](#트러블슈팅)

## 개요

이 프로젝트는 Docker를 사용하여 모든 팀원이 동일한 개발 환경에서 작업할 수 있도록 구성되었습니다.

### 서비스 구성
- **PostgreSQL**: 메인 데이터베이스 (Port: 5432)
- **Redis**: 캐싱 서버 (Port: 6379)
- **Backend (FastAPI)**: Python 백엔드 API (Port: 8000)
- **Frontend (Next.js)**: React 프론트엔드 (Port: 3000)
- **Redis Commander**: Redis 관리 도구 (Port: 8081) - 개발 환경에만 포함
- **pgAdmin**: PostgreSQL 관리 도구 (Port: 5050) - 개발 환경에만 포함

## 사전 요구사항

### 필수 설치 항목
- Docker Desktop (최신 버전)
  - macOS: https://docs.docker.com/desktop/install/mac-install/
  - Windows: https://docs.docker.com/desktop/install/windows-install/
  - Linux: https://docs.docker.com/desktop/install/linux-install/
- Docker Compose (Docker Desktop에 포함됨)

### 시스템 요구사항
- RAM: 최소 8GB (권장 16GB)
- 디스크 공간: 최소 10GB

### Docker Desktop 설정
1. Docker Desktop 실행
2. Settings > Resources > Advanced
   - CPUs: 4개 이상 할당
   - Memory: 4GB 이상 할당
   - Swap: 2GB 이상

## 프로젝트 구조

```
Stack-Lab-Demo/
├── SL-Back-end/
│   ├── app/                    # FastAPI 애플리케이션 코드
│   ├── Dockerfile              # 프로덕션용 Dockerfile
│   ├── Dockerfile.dev          # 개발용 Dockerfile (Hot-reload)
│   ├── requirements.txt        # Python 의존성
│   ├── .env                    # 백엔드 환경 변수 (git에 미포함)
│   ├── .env.example            # 환경 변수 예시
│   └── .dockerignore           # Docker 빌드 제외 파일
├── SL-Front-End/
│   ├── src/                    # Next.js 소스 코드
│   ├── Dockerfile              # 프로덕션용 Dockerfile
│   ├── Dockerfile.dev          # 개발용 Dockerfile (Hot-reload)
│   ├── package.json            # Node.js 의존성
│   ├── .env.local              # 프론트엔드 환경 변수 (git에 미포함)
│   ├── .env.example            # 환경 변수 예시
│   └── .dockerignore           # Docker 빌드 제외 파일
├── docker-compose.yml          # 프로덕션 환경 구성
├── docker-compose.dev.yml      # 개발 환경 구성 (Hot-reload)
├── .env                        # 루트 환경 변수 (git에 미포함)
├── .env.example                # 루트 환경 변수 예시
└── DOCKER_SETUP.md             # 이 문서
```

## 환경 변수 설정

### 1. 루트 레벨 환경 변수
```bash
# .env.example을 .env로 복사
cp .env.example .env
```

필요시 `.env` 파일을 수정하여 포트 번호나 데이터베이스 설정을 변경할 수 있습니다.

### 2. 백엔드 환경 변수
```bash
# SL-Back-end/.env.example을 .env로 복사
cp SL-Back-end/.env.example SL-Back-end/.env
```

**중요**: `SECRET_KEY`는 반드시 변경해야 합니다:
```bash
# SECRET_KEY 생성 (Python)
python -c "import secrets; print(secrets.token_hex(32))"

# 또는 OpenSSL 사용
openssl rand -hex 32
```

생성된 키를 `SL-Back-end/.env` 파일의 `SECRET_KEY`에 복사하세요.

### 3. 프론트엔드 환경 변수
```bash
# SL-Front-End/.env.example을 .env.local로 복사
cp SL-Front-End/.env.example SL-Front-End/.env.local
```

## 개발 환경 실행

개발 환경은 **Hot-reload** 기능이 활성화되어 있어, 코드를 수정하면 자동으로 반영됩니다.

### 1. 처음 실행 (빌드 포함)
```bash
# 모든 서비스 빌드 및 시작
docker-compose -f docker-compose.dev.yml up --build

# 또는 백그라운드로 실행
docker-compose -f docker-compose.dev.yml up --build -d
```

### 2. 두 번째 실행부터 (빌드 없이)
```bash
# 빌드 없이 시작
docker-compose -f docker-compose.dev.yml up

# 백그라운드로 실행
docker-compose -f docker-compose.dev.yml up -d
```

### 3. 서비스 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Backend Docs (Swagger)**: http://localhost:8000/docs
- **Redis Commander**: http://localhost:8081
- **pgAdmin**: http://localhost:5050
  - Email: `admin@stacklab.com` (`.env`에서 변경 가능)
  - Password: `admin` (`.env`에서 변경 가능)

### 4. 로그 확인
```bash
# 모든 서비스 로그
docker-compose -f docker-compose.dev.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

### 5. 서비스 중지
```bash
# 서비스 중지 (컨테이너 유지)
docker-compose -f docker-compose.dev.yml stop

# 서비스 중지 및 컨테이너 삭제
docker-compose -f docker-compose.dev.yml down

# 볼륨까지 모두 삭제 (데이터 초기화)
docker-compose -f docker-compose.dev.yml down -v
```

## 프로덕션 환경 실행

프로덕션 환경은 최적화된 빌드를 사용합니다.

### 1. 빌드 및 실행
```bash
# 모든 서비스 빌드 및 시작
docker-compose up --build -d

# Redis Commander 제외하고 실행
docker-compose up --build -d --scale redis-commander=0
```

### 2. 서비스 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Backend Docs**: http://localhost:8000/docs

### 3. 서비스 중지
```bash
docker-compose down
```

## 유용한 명령어

### 서비스 관리
```bash
# 특정 서비스만 재시작
docker-compose -f docker-compose.dev.yml restart backend

# 특정 서비스만 빌드
docker-compose -f docker-compose.dev.yml build backend

# 서비스 상태 확인
docker-compose -f docker-compose.dev.yml ps

# 실행 중인 컨테이너 상태 확인
docker ps
```

### 컨테이너 내부 접속
```bash
# Backend 컨테이너 쉘 접속
docker-compose -f docker-compose.dev.yml exec backend bash

# Frontend 컨테이너 쉘 접속
docker-compose -f docker-compose.dev.yml exec frontend sh

# PostgreSQL 접속
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d quant_investment_db

# Redis CLI 접속
docker-compose -f docker-compose.dev.yml exec redis redis-cli
```

### 데이터베이스 관리
```bash
# 데이터베이스 백업
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres quant_investment_db > backup.sql

# 데이터베이스 복원
cat backup.sql | docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres quant_investment_db

# 데이터베이스 초기화
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
```

### 로그 관리
```bash
# 최근 100줄의 로그만 보기
docker-compose -f docker-compose.dev.yml logs --tail=100

# 타임스탬프 포함하여 로그 보기
docker-compose -f docker-compose.dev.yml logs -f -t

# 특정 시간 이후의 로그만 보기
docker-compose -f docker-compose.dev.yml logs --since 2024-01-01T00:00:00
```

### 리소스 관리
```bash
# 사용하지 않는 이미지, 컨테이너 정리
docker system prune -a

# 볼륨 정리
docker volume prune

# 빌드 캐시 정리
docker builder prune -a

# 모든 것 정리 (주의!)
docker system prune -a --volumes
```

## 트러블슈팅

### 1. 포트가 이미 사용 중인 경우
```bash
# 포트 사용 확인 (macOS/Linux)
lsof -i :3000  # Frontend 포트 확인
lsof -i :8000  # Backend 포트 확인
lsof -i :5432  # PostgreSQL 포트 확인

# 포트 사용 확인 (Windows)
netstat -ano | findstr :3000

# 해결 방법 1: 다른 포트 사용
# .env 파일에서 FRONTEND_PORT, BACKEND_PORT, POSTGRES_PORT 변경

# 해결 방법 2: 기존 프로세스 종료
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### 2. 빌드가 실패하는 경우
```bash
# 빌드 캐시 없이 다시 빌드
docker-compose -f docker-compose.dev.yml build --no-cache

# 이미지 삭제 후 재빌드
docker-compose -f docker-compose.dev.yml down --rmi all
docker-compose -f docker-compose.dev.yml up --build
```

### 3. 데이터베이스 연결 실패
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose -f docker-compose.dev.yml ps postgres

# PostgreSQL 로그 확인
docker-compose -f docker-compose.dev.yml logs postgres

# PostgreSQL 헬스체크
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres

# 데이터베이스 재시작
docker-compose -f docker-compose.dev.yml restart postgres
```

### 4. Hot-reload가 작동하지 않는 경우

**Backend (FastAPI)**:
- `Dockerfile.dev`에서 `--reload` 옵션이 있는지 확인
- `docker-compose.dev.yml`에서 볼륨 마운트 확인
```yaml
volumes:
  - ./SL-Back-end/app:/app/app
```

**Frontend (Next.js)**:
- macOS/Windows Docker Desktop의 파일 감시 문제일 수 있음
- `docker-compose.dev.yml`에 환경 변수 추가 확인:
```yaml
environment:
  WATCHPACK_POLLING: "true"
```

### 5. 메모리 부족 오류
```bash
# Docker Desktop 설정에서 메모리 증가
# Settings > Resources > Advanced > Memory: 6GB 이상

# 또는 일부 서비스만 실행
docker-compose -f docker-compose.dev.yml up postgres redis backend
```

### 6. 권한 문제 (Permission denied)
```bash
# macOS/Linux: logs 디렉토리 권한 변경
chmod -R 755 SL-Back-end/logs

# 또는 컨테이너 내부에서 직접 수정
docker-compose -f docker-compose.dev.yml exec backend chmod -R 755 /app/logs
```

### 7. 네트워크 문제
```bash
# 네트워크 재생성
docker-compose -f docker-compose.dev.yml down
docker network prune
docker-compose -f docker-compose.dev.yml up -d
```

## 개발 팁

### 1. 빠른 재시작
개발 중 특정 서비스만 재시작하려면:
```bash
docker-compose -f docker-compose.dev.yml restart backend
```

### 2. Python 패키지 추가
```bash
# 1. requirements.txt 수정
# 2. Backend 컨테이너 재빌드
docker-compose -f docker-compose.dev.yml build backend
docker-compose -f docker-compose.dev.yml up -d backend
```

### 3. Node 패키지 추가
```bash
# 1. package.json 수정
# 2. Frontend 컨테이너 재빌드
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend

# 또는 컨테이너 내에서 직접 설치
docker-compose -f docker-compose.dev.yml exec frontend pnpm install <package-name>
```

### 4. 데이터베이스 마이그레이션
```bash
# Backend 컨테이너에서 Alembic 마이그레이션 실행
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

### 5. 테스트 실행
```bash
# Backend 테스트
docker-compose -f docker-compose.dev.yml exec backend pytest

# Frontend 테스트 (설정된 경우)
docker-compose -f docker-compose.dev.yml exec frontend pnpm test
```

## pgAdmin 데이터베이스 연결 설정

1. http://localhost:5050 접속
2. 로그인 (Email: `admin@stacklab.com`, Password: `admin`)
3. Add New Server 클릭
4. General 탭:
   - Name: Stack Lab DB
5. Connection 탭:
   - Host: `postgres` (Docker 네트워크 내 서비스 이름)
   - Port: `5432`
   - Username: `postgres`
   - Password: `postgres123`
6. Save

## Git에 포함하지 말아야 할 파일

다음 파일들은 `.gitignore`에 추가하세요:
```
.env
SL-Back-end/.env
SL-Front-End/.env.local
```

## 추가 리소스

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Next.js 공식 문서](https://nextjs.org/docs)
