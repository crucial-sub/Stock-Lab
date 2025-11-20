# EC2 배포 단계별 가이드 (Clone 방식)

이 문서는 EC2 인스턴스에서 처음부터 프로젝트를 클론하고 배포하는 전체 과정을 안내합니다.

## 📋 사전 준비사항

### AWS 리소스 준비 완료 확인
- [ ] EC2 인스턴스 실행 중
- [ ] RDS PostgreSQL 생성 및 엔드포인트 확인
- [ ] ElastiCache Redis 클러스터 생성 및 엔드포인트 확인
- [ ] Security Groups 설정 완료:
  - RDS: EC2 보안 그룹에서 포트 5432 허용
  - ElastiCache: EC2 보안 그룹에서 포트 6379 허용
  - EC2: 외부에서 포트 8000, 3000 허용

### 필요한 정보 준비
다음 정보를 메모장에 미리 준비하세요:

```
1. RDS 정보:
   - 엔드포인트: ___________________________
   - 포트: 5432
   - 사용자명: ___________________________
   - 비밀번호: ___________________________
   - 데이터베이스명: stock_lab_investment_db

2. ElastiCache Redis 정보:
   - 엔드포인트: ___________________________
   - 포트: 6379
   - 비밀번호 (있다면): ___________________________

3. EC2 정보:
   - 퍼블릭 IP: ___________________________
   - SSH Key 위치: ___________________________

4. 외부 API:
   - OpenDart API Key: ___________________________
```

---

## 1단계: 로컬에서 코드 Push

### 1.1 변경사항 커밋

```bash
# 현재 변경사항 확인
git status

# 커밋
git commit -m "Feat: EC2 배포 환경 설정 및 자동화 스크립트 추가

- 환경 변수 검증 로직 추가 (config.py)
- .env.example 템플릿 업데이트
- EC2 배포 자동화 스크립트 (setup-ec2-env.sh)
- 배포 가이드 문서 추가 (DEPLOYMENT_GUIDE.md)
- docker-compose.prod.yml 리소스 제한 및 최적화
- 민감 정보 Git 추적 제거 (.env 파일)
- .gitignore 강화

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 1.2 브랜치 Push 및 병합

```bash
# 현재 브랜치를 원격에 push
git push origin PROJ-97-ec2

# (옵션 A) Pull Request 생성 후 main에 병합
# GitHub에서 Pull Request 생성 → 리뷰 → Merge

# (옵션 B) 로컬에서 직접 main에 병합
git checkout main
git pull origin main
git merge PROJ-97-ec2
git push origin main
```

---

## 2단계: EC2 접속 및 환경 준비

### 2.1 EC2 인스턴스 접속

```bash
# SSH로 EC2 접속
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP

# 예시:
# ssh -i ~/Downloads/my-ec2-key.pem ubuntu@43.203.206.70
```

### 2.2 시스템 업데이트

```bash
# 패키지 목록 업데이트
sudo apt update && sudo apt upgrade -y
```

### 2.3 Docker 설치

```bash
# Docker 설치 스크립트 다운로드 및 실행
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# Docker 서비스 시작 및 자동 시작 설정
sudo systemctl start docker
sudo systemctl enable docker

# Docker 버전 확인
docker --version
```

### 2.4 Docker Compose 설치

```bash
# Docker Compose 최신 버전 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 실행 권한 부여
sudo chmod +x /usr/local/bin/docker-compose

# Docker Compose 버전 확인
docker-compose --version
```

### 2.5 Git 설치 (이미 설치되어 있을 수 있음)

```bash
# Git 설치
sudo apt install git -y

# Git 버전 확인
git --version
```

### 2.6 재로그인 (Docker 그룹 적용)

```bash
# 로그아웃
exit

# 다시 SSH 접속
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP

# Docker 권한 확인
docker ps
# 에러 없이 실행되어야 함
```

---

## 3단계: 프로젝트 클론

### 3.1 Git 클론

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 예시:
# git clone https://github.com/Krafton-Jungle-10-Final-Project/Stock-Lab-Demo.git

# 프로젝트 디렉토리로 이동
cd Stock-Lab-Demo

# main 브랜치로 전환 (이미 main일 수 있음)
git checkout main
git pull origin main

# 파일 확인
ls -la
```

---

## 4단계: 환경 변수 설정

### 4.1 자동 설정 스크립트 사용 (추천)

```bash
# 스크립트 실행 권한 부여
chmod +x scripts/setup-ec2-env.sh

# 스크립트 실행
./scripts/setup-ec2-env.sh
```

**스크립트가 물어보는 정보:**

1. **RDS 엔드포인트**: `your-rds.rds.amazonaws.com` 입력
2. **RDS 포트**: 5432 (기본값 사용)
3. **RDS 사용자명**: `stocklabadmin` 입력
4. **RDS 비밀번호**: 비밀번호 입력 (화면에 표시되지 않음)
5. **데이터베이스명**: `stock_lab_investment_db` (기본값 사용)
6. **Redis 엔드포인트**: `your-redis.cache.amazonaws.com` 입력
7. **Redis 포트**: 6379 (기본값 사용)
8. **Redis 비밀번호**: 없으면 엔터
9. **EC2 IP**: EC2 퍼블릭 IP 입력
10. **DEBUG 모드**: `false` (기본값 사용)
11. **로그 레벨**: `INFO` (기본값 사용)
12. **OpenDart API Key**: API 키 입력

스크립트가 완료되면 다음 파일들이 자동 생성됩니다:
- `SL-Back-end/.env`
- `.env.production`
- `deployment-summary.txt`

### 4.2 수동 설정 (스크립트를 사용하지 않는 경우)

```bash
# Backend .env 파일 생성
cd ~/Stock-Lab-Demo/SL-Back-end
cp .env.example .env
nano .env
```

다음 내용을 수정하세요:

```bash
# 배포 환경
DEPLOYMENT_ENV=ec2

# RDS 정보 (실제 값으로 변경)
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db
DATABASE_SYNC_URL=postgresql://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db

# Redis 정보 (실제 값으로 변경)
REDIS_URL=redis://REDIS_ENDPOINT:6379/0
REDIS_HOST=REDIS_ENDPOINT
REDIS_PORT=6379

# SECRET_KEY 생성
SECRET_KEY=$(openssl rand -hex 32)

# 디버그 모드 끄기
DEBUG=false

# CORS 설정 (EC2 IP로 변경)
BACKEND_CORS_ORIGINS=["http://YOUR_EC2_IP:3000"]

# API Key
DART_API_KEY=YOUR_DART_API_KEY
```

Ctrl+O (저장), Ctrl+X (종료)

```bash
# Root .env.production 파일 생성
cd ~/Stock-Lab-Demo
cp .env.example .env.production
nano .env.production
```

다음 내용을 수정하세요:

```bash
# RDS 연결 정보
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db
DATABASE_SYNC_URL=postgresql://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db

# Frontend 환경 변수
NEXT_PUBLIC_API_BASE_URL=http://YOUR_EC2_IP:8000/api/v1

# 포트 설정
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

---

## 5단계: 연결 테스트 (선택사항이지만 권장)

### 5.1 RDS 연결 테스트

```bash
# PostgreSQL 클라이언트 설치
sudo apt install postgresql-client -y

# RDS 연결 테스트
psql "postgresql://USERNAME:PASSWORD@RDS_ENDPOINT:5432/stock_lab_investment_db"

# 성공하면 postgres 프롬프트가 나타남
# \q 로 종료
```

### 5.2 Redis 연결 테스트

```bash
# Redis CLI 설치
sudo apt install redis-tools -y

# Redis 연결 테스트
redis-cli -h REDIS_ENDPOINT ping

# 응답: PONG
```

---

## 6단계: Docker 배포

### 6.1 이미지 빌드 및 컨테이너 실행

```bash
# 프로젝트 루트 디렉토리로 이동
cd ~/Stock-Lab-Demo

# Docker Compose로 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d --build
```

**예상 소요 시간**: 5-10분 (첫 빌드 시)

### 6.2 진행 상황 확인

```bash
# 실시간 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# Ctrl+C로 로그 종료 (컨테이너는 계속 실행됨)
```

### 6.3 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 예상 출력:
# CONTAINER ID   IMAGE                    STATUS         PORTS
# abc123...      sl_backend_prod          Up 3 minutes   0.0.0.0:8000->8000/tcp
# def456...      sl_frontend_prod         Up 2 minutes   0.0.0.0:3000->3000/tcp
```

---

## 7단계: 배포 확인

### 7.1 Health Check (EC2 내부)

```bash
# Backend Health Check
curl http://localhost:8000/health

# 예상 응답:
# {"status":"healthy","database":"connected","redis":"connected"}

# Frontend Health Check
curl http://localhost:3000

# HTML 응답이 나오면 성공
```

### 7.2 외부 접근 테스트 (로컬 PC에서)

브라우저를 열고 다음 URL에 접속:

1. **Frontend**: `http://YOUR_EC2_IP:3000`
   - 정상 작동하면 웹페이지가 보임

2. **Backend API Docs**: `http://YOUR_EC2_IP:8000/docs`
   - Swagger UI가 보이면 성공

3. **Backend Health**: `http://YOUR_EC2_IP:8000/health`
   - JSON 응답 확인

### 7.3 로그 확인

```bash
# Backend 로그
docker logs sl_backend_prod --tail 100

# Frontend 로그
docker logs sl_frontend_prod --tail 100

# 모든 로그 실시간 확인
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 8단계: 배포 완료 후 작업

### 8.1 자동 시작 설정 확인

```bash
# Docker 서비스가 부팅 시 자동 시작되는지 확인
sudo systemctl is-enabled docker

# 출력: enabled
```

컨테이너는 `restart: unless-stopped` 정책으로 설정되어 있어 EC2 재부팅 시 자동으로 재시작됩니다.

### 8.2 보안 설정 확인

**AWS Console에서 확인:**

1. **EC2 보안 그룹**:
   - 인바운드: 8000, 3000 포트 허용
   - 소스: 필요한 IP만 허용 (0.0.0.0/0은 개발 중에만)

2. **RDS 보안 그룹**:
   - 인바운드: 5432 포트
   - 소스: EC2 보안 그룹만 허용

3. **ElastiCache 보안 그룹**:
   - 인바운드: 6379 포트
   - 소스: EC2 보안 그룹만 허용

### 8.3 모니터링 설정 (선택사항)

```bash
# 디스크 사용량 확인
df -h

# 메모리 사용량 확인
free -h

# 컨테이너 리소스 사용량 확인
docker stats

# Ctrl+C로 종료
```

---

## 9단계: 업데이트 방법 (나중에 코드 변경 시)

### 9.1 코드 업데이트 프로세스

```bash
# EC2 접속
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 프로젝트 디렉토리로 이동
cd ~/Stock-Lab-Demo

# 최신 코드 Pull
git pull origin main

# 컨테이너 재빌드 및 재시작
docker-compose -f docker-compose.prod.yml up -d --build

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 유용한 명령어 모음

```bash
# === 컨테이너 관리 ===
# 전체 재시작
docker-compose -f docker-compose.prod.yml restart

# 특정 서비스만 재시작
docker-compose -f docker-compose.prod.yml restart backend

# 컨테이너 중지
docker-compose -f docker-compose.prod.yml down

# 컨테이너 중지 및 볼륨 삭제
docker-compose -f docker-compose.prod.yml down -v

# === 로그 관리 ===
# 로그 실시간 확인
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그만
docker logs sl_backend_prod -f

# 최근 100줄만
docker logs sl_backend_prod --tail 100

# === 디버깅 ===
# 컨테이너 내부 접속
docker exec -it sl_backend_prod bash

# 환경 변수 확인
docker exec sl_backend_prod env

# === 정리 ===
# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a

# 볼륨 포함 전체 정리 (주의!)
docker system prune -a --volumes
```

---

## 문제 해결

### 문제 1: 컨테이너가 계속 재시작됨

```bash
# 로그 확인
docker logs sl_backend_prod --tail 200

# 일반적인 원인:
# - 환경 변수 오류 → .env 파일 확인
# - RDS 연결 실패 → 보안 그룹 확인
# - Redis 연결 실패 → ElastiCache 엔드포인트 확인
```

### 문제 2: 외부에서 접근 안됨

```bash
# 포트 확인
sudo netstat -tuln | grep -E ':(8000|3000)'

# 방화벽 확인 (ufw 사용 시)
sudo ufw status

# EC2 보안 그룹 인바운드 규칙 확인 (AWS Console)
```

### 문제 3: 데이터베이스 연결 실패

```bash
# RDS 연결 테스트
nc -zv RDS_ENDPOINT 5432

# 실패 시:
# 1. RDS 보안 그룹에 EC2 보안 그룹 추가
# 2. .env 파일의 DATABASE_URL 확인
# 3. RDS 엔드포인트 오타 확인
```

### 문제 4: Redis 연결 실패

```bash
# Redis 연결 테스트
redis-cli -h REDIS_ENDPOINT ping

# 실패 시:
# 1. ElastiCache 보안 그룹에 EC2 보안 그룹 추가
# 2. .env 파일의 REDIS_HOST 확인
# 3. ElastiCache 엔드포인트 오타 확인
```

더 자세한 문제 해결은 `DEPLOYMENT_GUIDE.md`를 참고하세요.

---

## 체크리스트

### 배포 전
- [ ] AWS 리소스 (EC2, RDS, ElastiCache) 생성 완료
- [ ] Security Groups 설정 완료
- [ ] 로컬에서 코드 push 완료
- [ ] RDS, ElastiCache 엔드포인트 메모 준비

### EC2 설정
- [ ] EC2 접속 성공
- [ ] Docker 설치 완료
- [ ] Docker Compose 설치 완료
- [ ] Git 설치 완료
- [ ] 프로젝트 클론 완료

### 환경 설정
- [ ] 환경 변수 설정 완료 (자동 또는 수동)
- [ ] RDS 연결 테스트 성공
- [ ] Redis 연결 테스트 성공

### 배포
- [ ] Docker 이미지 빌드 성공
- [ ] 컨테이너 실행 성공
- [ ] Health Check 성공
- [ ] 외부 접근 테스트 성공

---

## 추가 도움말

**문서 참고:**
- 상세 가이드: `DEPLOYMENT_GUIDE.md`
- 환경 변수 템플릿: `SL-Back-end/.env.example`

**문제 발생 시:**
1. 로그 확인: `docker-compose logs -f`
2. 환경 변수 확인: `cat SL-Back-end/.env`
3. 연결 테스트: `curl http://localhost:8000/health`

배포 성공을 기원합니다! 🚀
