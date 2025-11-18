# 🚀 EC2 배포 가이드

## 1. EC2 서버 준비

### 1.1 필수 설치 항목
```bash
# Docker 설치
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치 (없는 경우)
sudo yum install -y git
```

### 1.2 보안 그룹 설정
EC2 인스턴스의 보안 그룹에서 다음 포트를 열어주세요:
- **3000** (Frontend)
- **8000** (Backend API)
- **22** (SSH)

---

## 2. 프로젝트 Clone 및 환경 설정

### 2.1 프로젝트 Clone
```bash
cd ~
git clone <your-repo-url> Stock-Lab-Demo
cd Stock-Lab-Demo
```

### 2.2 환경 변수 설정

#### 📁 루트 디렉토리 `.env` 파일
```bash
# .env.ec2 파일을 .env로 복사
cp .env.ec2 .env

# EC2 퍼블릭 IP 또는 도메인으로 수정
nano .env
```

**수정할 내용:**
```bash
# EC2 퍼블릭 IP로 변경 (예: 3.38.123.456)
NEXT_PUBLIC_API_BASE_URL=http://3.38.123.456:8000/api/v1
```

#### 📁 백엔드 `.env` 파일
```bash
# SL-Back-end/.env.ec2 파일을 .env로 복사
cp SL-Back-end/.env.ec2 SL-Back-end/.env

# CORS 설정 수정
nano SL-Back-end/.env
```

**수정할 내용:**
```bash
# EC2 IP로 변경
BACKEND_CORS_ORIGINS=["http://3.38.123.456:3000","http://localhost:3000"]

# 프로덕션 배포 시 DEBUG 비활성화
DEBUG=false

# SECRET_KEY 재생성 (선택사항이지만 권장)
# 생성: openssl rand -hex 32
SECRET_KEY="새로운_시크릿_키"
```

---

## 3. Docker 실행

### 3.1 기본 실행
```bash
# Docker Compose로 모든 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3.2 개별 서비스 재시작
```bash
# 백엔드만 재시작
docker-compose restart backend

# 프론트엔드만 재시작
docker-compose restart frontend

# 전체 재시작
docker-compose restart
```

### 3.3 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 특정 컨테이너 로그 보기
docker-compose logs backend
docker-compose logs frontend
```

---

## 4. 데이터베이스 초기화

### 4.1 PostgreSQL 접속
```bash
docker exec -it sl_postgres_dev psql -U stocklabadmin -d stock_lab_investment_db
```

### 4.2 테이블 생성 확인
```sql
-- 테이블 목록 확인
\dt

-- 사용자 확인
SELECT email, nickname FROM users;
```

---

## 5. 접속 확인

### 5.1 브라우저에서 확인
- **프론트엔드**: `http://<EC2_PUBLIC_IP>:3000`
- **백엔드 API**: `http://<EC2_PUBLIC_IP>:8000/docs`

### 5.2 API Health Check
```bash
# 백엔드 헬스체크
curl http://localhost:8000/api/v1/health

# 프론트엔드 접속 확인
curl http://localhost:3000
```

---

## 6. 트러블슈팅

### 6.1 포트가 이미 사용 중인 경우
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 6.2 Docker 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 컨테이너 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 6.3 데이터베이스 연결 오류
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# PostgreSQL 로그 확인
docker-compose logs postgres

# 데이터베이스 재시작
docker-compose restart postgres
```

### 6.4 CORS 에러
```bash
# SL-Back-end/.env 파일에서 CORS 설정 확인
nano SL-Back-end/.env

# BACKEND_CORS_ORIGINS에 프론트엔드 URL 추가
BACKEND_CORS_ORIGINS=["http://YOUR_EC2_IP:3000"]

# 백엔드 재시작
docker-compose restart backend
```

---

## 7. 환경 변수 요약

### 필수 수정 항목

| 파일 | 변수명 | 설명 | 예시 |
|------|--------|------|------|
| `.env` | `NEXT_PUBLIC_API_BASE_URL` | 프론트엔드에서 백엔드 API 호출 URL | `http://3.38.123.456:8000/api/v1` |
| `SL-Back-end/.env` | `BACKEND_CORS_ORIGINS` | CORS 허용 URL | `["http://3.38.123.456:3000"]` |

### 선택 수정 항목 (보안 강화)

| 파일 | 변수명 | 설명 |
|------|--------|------|
| `SL-Back-end/.env` | `SECRET_KEY` | JWT 암호화 키 (프로덕션은 재생성 권장) |
| `SL-Back-end/.env` | `DEBUG` | 디버그 모드 (`false` 권장) |
| `.env` | `POSTGRES_PASSWORD` | PostgreSQL 비밀번호 변경 권장 |

---

## 8. 간단한 배포 스크립트

아래 스크립트를 `deploy.sh`로 저장하고 사용하세요:

```bash
#!/bin/bash

# EC2 배포 자동화 스크립트
echo "🚀 Stock-Lab 배포 시작..."

# 1. Git Pull
echo "📦 최신 코드 받아오기..."
git pull origin main

# 2. .env 파일 복사 (처음 1회만)
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성..."
    cp .env.ec2 .env
    echo "⚠️  .env 파일을 수정해주세요 (EC2 IP 설정)"
    exit 1
fi

if [ ! -f SL-Back-end/.env ]; then
    echo "📝 백엔드 .env 파일 생성..."
    cp SL-Back-end/.env.ec2 SL-Back-end/.env
    echo "⚠️  SL-Back-end/.env 파일을 수정해주세요 (CORS 설정)"
    exit 1
fi

# 3. Docker Compose 실행
echo "🐳 Docker 컨테이너 시작..."
docker-compose down
docker-compose up -d --build

# 4. 로그 확인
echo "📋 서비스 시작 대기 중..."
sleep 10
docker-compose ps

echo "✅ 배포 완료!"
echo "🌐 프론트엔드: http://$(curl -s http://checkip.amazonaws.com):3000"
echo "🔧 백엔드 API: http://$(curl -s http://checkip.amazonaws.com):8000/docs"
```

**사용법:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 9. AWS 관련 설정 (이미 포함됨)

현재 `.env` 파일에는 다음 AWS 설정이 포함되어 있습니다:
- ✅ AWS Access Key
- ✅ Bedrock LLM 설정 (Claude 3 Haiku)
- ✅ Knowledge Base 설정

**추가 작업 불필요** - 그대로 사용하시면 됩니다.

---

## 10. 자주 묻는 질문 (FAQ)

### Q1: 도메인을 사용하고 싶어요
A: Route 53에서 도메인 설정 후, `.env`의 IP를 도메인으로 변경하세요.

### Q2: HTTPS를 적용하고 싶어요
A: Nginx + Let's Encrypt 또는 AWS ALB를 사용하세요.

### Q3: 데이터베이스를 AWS RDS로 변경하고 싶어요
A: `SL-Back-end/.env`의 `DATABASE_URL`을 RDS 엔드포인트로 변경하세요.

### Q4: Redis를 AWS ElastiCache로 변경하고 싶어요
A: `SL-Back-end/.env`의 `REDIS_URL`을 ElastiCache 엔드포인트로 변경하세요.

---

## 문제 발생 시

로그 전체 확인:
```bash
docker-compose logs -f --tail=100
```

특정 서비스만:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```
