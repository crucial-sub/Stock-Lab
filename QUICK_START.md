# 🚀 Quick Start Guide

Docker를 사용하여 Stack Lab Demo 프로젝트를 5분 안에 시작하세요!

## 📋 사전 준비

1. **Docker Desktop 설치** (아직 설치하지 않았다면)
   - macOS: https://docs.docker.com/desktop/install/mac-install/
   - Windows: https://docs.docker.com/desktop/install/windows-install/

2. **Docker Desktop 실행** 확인
   ```bash
   docker --version
   docker-compose --version
   ```

## 🎯 개발 환경 시작하기 (3단계)

### 1단계: 환경 변수 파일 확인
루트 디렉토리에 이미 `.env` 파일이 생성되어 있습니다.
필요한 경우 포트 번호를 변경하세요.

```bash
# Backend 환경 변수 확인 (선택사항)
cat SL-Back-end/.env

# Frontend 환경 변수 확인 (선택사항)
cat SL-Front-End/.env.local
```

### 2단계: Docker 컨테이너 실행
```bash
# 개발 환경 시작 (Hot-reload 지원)
docker-compose -f docker-compose.dev.yml up --build
```

첫 실행 시 이미지 빌드에 5-10분 정도 소요될 수 있습니다.

### 3단계: 서비스 접속
브라우저에서 다음 주소로 접속하세요:

- **✨ Frontend**: http://localhost:3000
- **🔥 Backend API**: http://localhost:8000
- **📚 API 문서 (Swagger)**: http://localhost:8000/docs
- **🗄️ Redis Commander**: http://localhost:8081
- **🐘 pgAdmin**: http://localhost:5050

## 🛑 서비스 중지하기

```bash
# Ctrl+C를 눌러 서비스 중지

# 또는 다른 터미널에서
docker-compose -f docker-compose.dev.yml down
```

## 🔄 재시작하기

```bash
# 빌드 없이 빠르게 시작
docker-compose -f docker-compose.dev.yml up

# 백그라운드로 실행
docker-compose -f docker-compose.dev.yml up -d
```

## 📝 로그 확인하기

```bash
# 모든 서비스 로그
docker-compose -f docker-compose.dev.yml logs -f

# Backend 로그만
docker-compose -f docker-compose.dev.yml logs -f backend

# Frontend 로그만
docker-compose -f docker-compose.dev.yml logs -f frontend
```

## 🧹 완전히 초기화하기

데이터베이스를 포함한 모든 데이터를 삭제하고 처음부터 시작:

```bash
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up --build
```

## ❓ 문제 해결

### 포트가 이미 사용 중이에요
```bash
# 포트 확인 (macOS/Linux)
lsof -i :3000
lsof -i :8000

# .env 파일에서 포트 번호 변경
```

### 빌드가 실패해요
```bash
# 캐시 없이 재빌드
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up
```

### Hot-reload가 작동하지 않아요
- Docker Desktop이 최신 버전인지 확인하세요
- `docker-compose.dev.yml` 파일의 볼륨 마운트를 확인하세요

## 📖 더 자세한 정보

전체 가이드는 [DOCKER_SETUP.md](./DOCKER_SETUP.md)를 참고하세요.

## 🎓 유용한 명령어

```bash
# 특정 서비스만 재시작
docker-compose -f docker-compose.dev.yml restart backend

# 서비스 상태 확인
docker-compose -f docker-compose.dev.yml ps

# Backend 컨테이너 접속
docker-compose -f docker-compose.dev.yml exec backend bash

# Frontend 컨테이너 접속
docker-compose -f docker-compose.dev.yml exec frontend sh

# PostgreSQL 접속
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d quant_investment_db
```

## 🎉 성공!

모든 서비스가 정상적으로 실행되면 개발을 시작할 수 있습니다!
코드를 수정하면 자동으로 변경사항이 반영됩니다. (Hot-reload)

Happy Coding! 🚀
