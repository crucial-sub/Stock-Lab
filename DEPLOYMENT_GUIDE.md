# Stock Lab EC2 배포 가이드

이 문서는 Stock Lab 프로젝트를 AWS EC2에 안정적으로 배포하는 방법을 안내합니다.

## 목차
1. [사전 준비사항](#사전-준비사항)
2. [환경 변수 설정](#환경-변수-설정)
3. [EC2 배포 단계](#ec2-배포-단계)
4. [배포 확인](#배포-확인)
5. [문제 해결](#문제-해결)

---

## 사전 준비사항

### AWS 리소스
- ✅ **EC2 인스턴스** (Ubuntu 20.04 이상 권장)
- ✅ **RDS PostgreSQL** 인스턴스
- ✅ **ElastiCache Redis** 클러스터
- ✅ **Security Groups** 설정 완료
  - RDS: EC2 보안 그룹에서 5432 포트 접근 허용
  - ElastiCache: EC2 보안 그룹에서 6379 포트 접근 허용
  - EC2: 외부에서 8000(Backend), 3000(Frontend) 포트 접근 허용

### 로컬 준비
```bash
# Docker & Docker Compose 설치 확인
docker --version
docker-compose --version

# Git 리포지토리 클론
git clone <your-repo-url>
cd Stock-Lab-Demo
```

---

## 환경 변수 설정

### 1. Backend 환경 변수 설정

```bash
# 백엔드 디렉토리로 이동
cd SL-Back-end

# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 vim .env
```

**필수 설정 항목:**

```bash
# 배포 환경 설정
DEPLOYMENT_ENV=ec2

# RDS 데이터베이스 연결 정보
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db
DATABASE_SYNC_URL=postgresql://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db

# ElastiCache Redis 연결 정보
REDIS_URL=redis://YOUR_ELASTICACHE_ENDPOINT:6379/0
REDIS_HOST=YOUR_ELASTICACHE_ENDPOINT
REDIS_PORT=6379

# 보안 설정 (반드시 새로운 키 생성)
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False

# CORS 설정 (EC2 IP 또는 도메인으로 변경)
BACKEND_CORS_ORIGINS=["http://YOUR_EC2_IP:3000","http://YOUR_DOMAIN.com"]

# OpenDart API Key
DART_API_KEY=YOUR_DART_API_KEY
```

### 2. 루트 환경 변수 설정

```bash
# 프로젝트 루트로 이동
cd ..

# .env.production 파일 편집
nano .env.production
```

**필수 설정 항목:**

```bash
# RDS 연결 정보
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db
DATABASE_SYNC_URL=postgresql://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db

# Frontend 환경 변수
NEXT_PUBLIC_API_BASE_URL=http://YOUR_EC2_IP:8000/api/v1

# Backend 포트
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### 3. SECRET_KEY 생성하기

```bash
# 새로운 SECRET_KEY 생성
openssl rand -hex 32

# 출력된 값을 복사하여 .env 파일의 SECRET_KEY에 붙여넣기
```

---

## EC2 배포 단계

### 1. EC2 인스턴스 접속

```bash
# SSH를 통해 EC2 접속
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 또는 EC2 Instance Connect 사용
```

### 2. EC2에 필수 소프트웨어 설치

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo apt install git -y

# 재로그인 (Docker 그룹 적용)
exit
# 다시 SSH 접속
```

### 3. 프로젝트 배포

```bash
# 프로젝트 클론
cd ~
git clone <your-repo-url>
cd Stock-Lab-Demo

# 환경 변수 파일 생성
cp SL-Back-end/.env.example SL-Back-end/.env

# .env 파일 편집 (위의 환경 변수 설정 참고)
nano SL-Back-end/.env
nano .env.production

# Docker 이미지 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d --build

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. 환경 설정 스크립트 사용 (선택사항)

프로젝트에 포함된 스크립트를 사용하면 더 쉽게 설정할 수 있습니다:

```bash
# 환경 설정 스크립트 실행
chmod +x scripts/setup-ec2-env.sh
./scripts/setup-ec2-env.sh

# 스크립트가 대화형으로 필요한 정보를 요청합니다:
# - RDS 엔드포인트
# - ElastiCache 엔드포인트
# - EC2 퍼블릭 IP
# 등등...
```

---

## 배포 확인

### 1. 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 예상 출력:
# CONTAINER ID   IMAGE                    STATUS         PORTS
# abc123def456   sl_backend_prod          Up 2 minutes   0.0.0.0:8000->8000/tcp
# def456ghi789   sl_frontend_prod         Up 1 minute    0.0.0.0:3000->3000/tcp
```

### 2. Health Check

```bash
# Backend Health Check
curl http://localhost:8000/health

# 예상 응답:
# {"status":"healthy","database":"connected","redis":"connected"}

# Frontend Health Check
curl http://localhost:3000
```

### 3. 로그 확인

```bash
# Backend 로그
docker logs sl_backend_prod --tail 100 -f

# Frontend 로그
docker logs sl_frontend_prod --tail 100 -f

# 모든 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. 외부에서 접근 테스트

브라우저에서 다음 URL로 접근:
- Frontend: `http://YOUR_EC2_IP:3000`
- Backend API: `http://YOUR_EC2_IP:8000/docs` (Swagger UI)

---

## 문제 해결

### 1. 환경 변수 오류

**증상:** 애플리케이션 시작 실패, "CONFIGURATION ERRORS" 메시지

**해결방법:**
```bash
# 환경 변수 확인
cat SL-Back-end/.env

# 누락되거나 잘못된 값이 있는지 확인
# 특히 다음 항목들:
# - DATABASE_URL (YOUR_DB, YOUR_RDS 같은 플레이스홀더가 있으면 안됨)
# - SECRET_KEY (기본값이 아닌 실제 생성한 키 사용)
# - REDIS_HOST (YOUR_ELASTICACHE 같은 플레이스홀더가 있으면 안됨)

# 수정 후 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart
```

### 2. 데이터베이스 연결 실패

**증상:** "could not connect to database" 오류

**해결방법:**
```bash
# 1. RDS 보안 그룹 확인
# - EC2의 보안 그룹이 RDS 인바운드 규칙에 추가되어 있는지 확인

# 2. 네트워크 연결 테스트
nc -zv YOUR_RDS_ENDPOINT 5432

# 3. RDS 엔드포인트와 자격 증명 확인
# - .env 파일의 DATABASE_URL이 올바른지 확인

# 4. Docker 내부에서 연결 테스트
docker exec -it sl_backend_prod bash
apt-get update && apt-get install -y postgresql-client
psql "postgresql://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db"
```

### 3. Redis 연결 실패

**증상:** "Error connecting to Redis" 메시지

**해결방법:**
```bash
# 1. ElastiCache 보안 그룹 확인
# - EC2의 보안 그룹이 ElastiCache 인바운드 규칙에 추가되어 있는지 확인

# 2. Redis 엔드포인트 확인
# AWS Console > ElastiCache > Redis clusters에서 엔드포인트 복사

# 3. 연결 테스트
nc -zv YOUR_ELASTICACHE_ENDPOINT 6379

# 4. Docker 내부에서 연결 테스트
docker exec -it sl_backend_prod bash
apt-get update && apt-get install -y redis-tools
redis-cli -h YOUR_ELASTICACHE_ENDPOINT ping
# 응답: PONG
```

### 4. CORS 오류

**증상:** 브라우저 콘솔에 "CORS policy" 오류

**해결방법:**
```bash
# .env 파일의 BACKEND_CORS_ORIGINS 수정
BACKEND_CORS_ORIGINS=["http://YOUR_EC2_IP:3000","http://YOUR_DOMAIN.com"]

# 또는 개발 중에는 모든 origin 허용 (프로덕션에서는 권장하지 않음)
BACKEND_CORS_ORIGINS=["*"]

# 수정 후 재시작
docker-compose -f docker-compose.prod.yml restart backend
```

### 5. 포트 접근 불가

**증상:** 외부에서 접근 시 "Connection refused" 또는 타임아웃

**해결방법:**
```bash
# 1. EC2 보안 그룹 확인
# - 인바운드 규칙에 8000, 3000 포트가 열려있는지 확인
# - 소스: 0.0.0.0/0 (모든 IP) 또는 필요한 IP 범위

# 2. 방화벽 확인 (ufw 사용 시)
sudo ufw status
sudo ufw allow 8000
sudo ufw allow 3000

# 3. 포트 사용 확인
sudo netstat -tuln | grep -E ':(8000|3000)'
```

### 6. 컨테이너 재시작 반복

**증상:** `docker ps`에서 컨테이너가 계속 재시작됨

**해결방법:**
```bash
# 로그 확인
docker logs sl_backend_prod --tail 200

# Health check 실패 확인
docker inspect sl_backend_prod | grep -A 10 Health

# 환경 변수 문제일 가능성이 높음 - .env 파일 재확인
cat SL-Back-end/.env

# 문제 수정 후 재배포
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 유용한 명령어

```bash
# 전체 재배포 (이미지 재빌드)
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

# 특정 서비스만 재시작
docker-compose -f docker-compose.prod.yml restart backend

# 컨테이너 내부 접속
docker exec -it sl_backend_prod bash

# 디스크 공간 정리
docker system prune -a --volumes

# 환경 변수 확인 (컨테이너 내부)
docker exec sl_backend_prod env | grep DATABASE_URL
```

---

## 보안 권장사항

1. **SECRET_KEY**: 절대 기본값 사용 금지, 매번 새로 생성
2. **.env 파일**: Git에 커밋하지 않기 (이미 .gitignore에 포함됨)
3. **RDS/Redis**: 프로덕션에서는 퍼블릭 액세스 비활성화
4. **EC2 보안 그룹**: 필요한 포트만 최소한으로 개방
5. **CORS**: 프로덕션에서는 특정 도메인만 허용 (와일드카드 사용 금지)
6. **DEBUG 모드**: EC2 배포 시 반드시 `DEBUG=False` 설정

---

## 추가 자료

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [AWS RDS 연결 가이드](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.html)
- [AWS ElastiCache 가이드](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)

---

## 지원

문제가 지속되면 다음 정보를 포함하여 이슈를 등록해주세요:
- 에러 메시지 전체
- `docker logs` 출력
- `.env` 파일 (민감 정보 제외)
- EC2 인스턴스 타입 및 리전
