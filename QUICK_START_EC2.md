# ⚡ EC2 빠른 배포 가이드 (AWS RDS + ElastiCache 사용)

## 📋 사전 준비 (AWS 콘솔에서)

### 1. AWS RDS PostgreSQL 생성
1. AWS 콘솔 → RDS → 데이터베이스 생성
2. **엔진 옵션**: PostgreSQL
3. **템플릿**: 프리 티어 (테스트용) 또는 프로덕션
4. **DB 인스턴스 식별자**: `stocklab-db`
5. **마스터 사용자 이름**: `stocklabadmin` (기억할 것!)
6. **마스터 암호**: 안전한 비밀번호 설정 (기억할 것!)
7. **퍼블릭 액세스**: 예 (EC2에서 접근하려면 필요)
8. **VPC 보안 그룹**: 새로 생성 또는 기존 선택
   - 인바운드 규칙: PostgreSQL (5432) - EC2 보안 그룹에서 접근 허용
9. **초기 데이터베이스 이름**: `stock_lab_investment_db`
10. 생성 후 **엔드포인트** 복사 (예: `stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com`)

### 2. AWS ElastiCache Redis 생성
1. AWS 콘솔 → ElastiCache → Redis 클러스터 생성
2. **클러스터 모드**: 비활성화됨 (간단한 구성)
3. **이름**: `stocklab-redis`
4. **노드 유형**: cache.t3.micro (프리 티어) 또는 cache.t3.small
5. **포트**: 6379 (기본값)
6. **서브넷 그룹**: EC2와 동일한 VPC 선택
7. **보안 그룹**: Redis (6379) - EC2 보안 그룹에서 접근 허용
8. 생성 후 **기본 엔드포인트** 복사 (예: `stocklab-redis.xxxxx.apn2.cache.amazonaws.com`)

### 3. 보안 그룹 설정 확인
EC2 보안 그룹 인바운드 규칙:
- **22** (SSH)
- **3000** (Frontend)
- **8000** (Backend)

RDS 보안 그룹 인바운드 규칙:
- **5432** (PostgreSQL) - 소스: EC2 보안 그룹

ElastiCache 보안 그룹 인바운드 규칙:
- **6379** (Redis) - 소스: EC2 보안 그룹

---

## 1️⃣ EC2에서 프로젝트 Clone

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 Clone
git clone <your-repo-url> Stock-Lab-Demo
cd Stock-Lab-Demo
```

---

## 2️⃣ 환경 변수 설정 (3개 파일)

### 📄 파일 1: 루트 `.env`
```bash
# .env.ec2를 .env로 복사
cp .env.ec2 .env

# EC2 퍼블릭 IP로 수정
nano .env
```

**수정할 곳 (1줄):**
```bash
# 13번째 줄: YOUR_EC2_IP를 실제 EC2 퍼블릭 IP로 변경
NEXT_PUBLIC_API_BASE_URL=http://3.38.123.456:8000/api/v1
```

**저장: Ctrl+O → Enter → Ctrl+X**

---

### 📄 파일 2: 백엔드 `.env`
```bash
# .env.ec2를 .env로 복사
cp SL-Back-end/.env.ec2 SL-Back-end/.env

# RDS, ElastiCache, CORS 설정 수정
nano SL-Back-end/.env
```

**수정할 곳 (4줄):**

```bash
# 9번째 줄: RDS 엔드포인트, 사용자명, 비밀번호
DATABASE_URL=postgresql+asyncpg://stocklabadmin:YOUR_PASSWORD@stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db

# 10번째 줄: 동일하게 수정
DATABASE_SYNC_URL=postgresql://stocklabadmin:YOUR_PASSWORD@stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db

# 19번째 줄: ElastiCache 엔드포인트
REDIS_URL=redis://stocklab-redis.xxxxx.apn2.cache.amazonaws.com:6379/0

# 20번째 줄: ElastiCache 엔드포인트 (동일)
REDIS_HOST=stocklab-redis.xxxxx.apn2.cache.amazonaws.com

# 42번째 줄: CORS - EC2 IP 추가
BACKEND_CORS_ORIGINS=["http://3.38.123.456:3000"]
```

**저장: Ctrl+O → Enter → Ctrl+X**

---

### 📄 파일 3: docker-compose 수정
Docker Compose에서 PostgreSQL과 Redis 컨테이너를 제거합니다.

```bash
nano docker-compose.yml
```

**수정 내용:**
```yaml
# postgres, redis, pgadmin, redis-commander 서비스 전체 삭제
# backend와 frontend만 남김

version: '3.8'

services:
  backend:
    build:
      context: ./SL-Back-end
      dockerfile: Dockerfile
    container_name: sl_backend_dev
    env_file:
      - ./SL-Back-end/.env
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - ./SL-Back-end:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - quant_network

  frontend:
    build:
      context: ./SL-Front-End
      dockerfile: Dockerfile.dev
    container_name: sl_frontend_dev
    environment:
      NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000/api/v1}
      API_BASE_URL: ${API_BASE_URL:-http://backend:8000/api/v1}
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    depends_on:
      - backend
    volumes:
      - ./SL-Front-End:/app
      - /app/node_modules
      - /app/.next
    networks:
      - quant_network

networks:
  quant_network:
    driver: bridge
```

**저장: Ctrl+O → Enter → Ctrl+X**

---

## 3️⃣ RDS 데이터베이스 초기화

### 방법 1: 로컬에서 마이그레이션 (권장)
```bash
# 로컬 DB 백업
pg_dump -U stocklabadmin -d stock_lab_investment_db > backup.sql

# RDS로 복원
psql -h stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com -U stocklabadmin -d stock_lab_investment_db < backup.sql
```

### 방법 2: 새로 시작 (테스트용)
```bash
# RDS에 직접 접속
psql -h stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com -U stocklabadmin -d stock_lab_investment_db

# 테이블은 백엔드 첫 실행 시 자동 생성됨 (SQLAlchemy)
```

---

## 4️⃣ Docker 실행

```bash
# Docker Compose로 백엔드 + 프론트엔드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

---

## 5️⃣ 접속 확인

### 브라우저에서:
- **프론트엔드**: `http://<EC2_IP>:3000`
- **백엔드 API 문서**: `http://<EC2_IP>:8000/docs`

### 터미널에서:
```bash
# 컨테이너 상태 확인
docker-compose ps

# 백엔드 로그
docker-compose logs -f backend

# 프론트엔드 로그
docker-compose logs -f frontend
```

---

## 6️⃣ RDS 연결 확인

```bash
# RDS에 직접 접속 (비밀번호 입력)
psql -h stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com -U stocklabadmin -d stock_lab_investment_db

# 테이블 확인
\dt

# 사용자 확인
SELECT email, nickname FROM users;

# 종료
\q
```

---

## 🔥 수정 요약

수정한 파일 3개:
1. ✅ `.env` - EC2 IP (1줄)
2. ✅ `SL-Back-end/.env` - RDS, ElastiCache, CORS (5줄)
3. ✅ `docker-compose.yml` - PostgreSQL, Redis 제거

실행:
```bash
docker-compose up -d --build
```

---

## 📝 EC2 IP 확인

### EC2 콘솔에서:
1. EC2 대시보드 → 인스턴스 클릭
2. "퍼블릭 IPv4 주소" 복사

### 터미널에서:
```bash
curl http://checkip.amazonaws.com
```

---

## 📊 RDS/ElastiCache 엔드포인트 확인

### RDS 엔드포인트:
1. RDS 콘솔 → 데이터베이스 → `stocklab-db` 클릭
2. **엔드포인트** 복사 (예: `stocklab-db.xxxxx.ap-northeast-2.rds.amazonaws.com`)

### ElastiCache 엔드포인트:
1. ElastiCache 콘솔 → Redis → `stocklab-redis` 클릭
2. **기본 엔드포인트** 복사 (예: `stocklab-redis.xxxxx.apn2.cache.amazonaws.com`)

---

## 🛠️ 유용한 명령어

```bash
# 재시작
docker-compose restart

# 중지
docker-compose down

# 로그 보기
docker-compose logs -f backend
docker-compose logs -f frontend

# 컨테이너 상태
docker-compose ps

# RDS 접속
psql -h <RDS_ENDPOINT> -U stocklabadmin -d stock_lab_investment_db
```

---

## 🚨 문제 해결

### "RDS 연결 안됨"
```bash
# 1. 보안 그룹 확인
# RDS 보안 그룹 인바운드에 EC2 보안 그룹 허용되었는지 확인

# 2. 엔드포인트 확인
nano SL-Back-end/.env
# DATABASE_URL에 RDS 엔드포인트가 맞는지 확인

# 3. 비밀번호 확인
# RDS 생성 시 설정한 비밀번호와 일치하는지 확인

# 4. 백엔드 재시작
docker-compose restart backend
```

### "ElastiCache 연결 안됨"
```bash
# 1. 보안 그룹 확인
# ElastiCache 보안 그룹 인바운드에 EC2 보안 그룹 허용

# 2. 엔드포인트 확인
nano SL-Back-end/.env
# REDIS_URL에 ElastiCache 엔드포인트가 맞는지 확인

# 3. VPC 확인
# EC2와 ElastiCache가 같은 VPC에 있는지 확인

# 4. 백엔드 재시작
docker-compose restart backend
```

### "CORS 에러"
```bash
nano SL-Back-end/.env
# BACKEND_CORS_ORIGINS에 EC2 IP 확인
docker-compose restart backend
```

### "API 호출 안됨"
```bash
# .env 파일 확인
cat .env | grep NEXT_PUBLIC_API_BASE_URL
# EC2 IP가 맞는지 확인

# 프론트엔드 재시작
docker-compose restart frontend
```

---

## 💰 예상 비용 (월)

| 항목 | 스펙 | 비용 |
|------|------|------|
| EC2 | t3.small | ~$15/월 |
| RDS PostgreSQL | db.t3.micro | ~$15/월 (Free Tier 1년) |
| ElastiCache Redis | cache.t3.micro | ~$15/월 |
| **총합** | - | **$45/월** (Free Tier: $15/월) |

---

## ✅ 장점 (로컬 DB/Redis 대비)

- ✅ **Auto Scaling 가능** (데이터 일관성 보장)
- ✅ **고가용성** (자동 백업, Multi-AZ)
- ✅ **성능 향상** (관리형 서비스 최적화)
- ✅ **데이터 안전** (자동 백업, 스냅샷)
- ✅ **확장 용이** (Read Replica, 클러스터링)

---

## 💡 다음 단계

현재 구성으로 **Auto Scaling 가능**합니다!

다음 단계:
1. ✅ ALB (Application Load Balancer) 추가
2. ✅ Auto Scaling Group 생성
3. ✅ Lambda + EventBridge로 스케줄러 분리

자세한 내용: `AUTO_SCALING_ISSUES.md` 참고

---

## 📖 더 자세한 가이드

- 전체 문서: `EC2_DEPLOYMENT_GUIDE.md`
- Auto Scaling: `AUTO_SCALING_ISSUES.md`
