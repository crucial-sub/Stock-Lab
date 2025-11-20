# EC2 배포 가이드

## 🚀 빠른 배포 (자동)

EC2 인스턴스에 SSH 접속 후:

```bash
cd ~/Stock-Lab
git pull origin main
./deploy-to-ec2.sh
```

---

## 📋 수동 배포 단계별 가이드

### 1. SSH 접속

```bash
ssh ubuntu@54.180.34.167
cd ~/Stock-Lab
```

### 2. 최신 코드 가져오기

```bash
git pull origin main
```

### 3. 환경 변수 설정

```bash
# EC2용 환경 변수 파일을 .env로 복사
cp .env.ec2 .env
```

### 4. 도커 컨테이너 재시작

```bash
# 기존 컨테이너 중지
docker compose down

# 캐시 없이 다시 빌드 (환경 변수 변경 시 필수)
docker compose build --no-cache

# 컨테이너 시작
docker compose up -d
```

### 5. 배포 확인

```bash
# 컨테이너 상태 확인
docker compose ps

# 백엔드 환경 변수 확인 (DATABASE_URL이 RDS를 가리키는지 확인)
docker exec sl_backend printenv | grep DATABASE_URL

# 백엔드 로그 확인
docker logs -f sl_backend

# 프론트엔드 로그 확인
docker logs -f sl_frontend
```

**예상 결과:**
```
DATABASE_URL=postgresql+asyncpg://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db
```

❌ 만약 `postgres:5432`가 나오면 환경 변수 설정이 잘못된 것입니다.

---

## 🔍 접속 URL

배포 후 다음 URL에서 확인:

- **Frontend:** http://54.180.34.167:3000
- **Backend API Docs:** http://54.180.34.167:8000/docs
- **Backend Health:** http://54.180.34.167:8000/health

---

## 🐛 트러블슈팅

### DATABASE_URL이 여전히 postgres:5432인 경우

1. `.env` 파일 확인:
   ```bash
   cat .env | grep DATABASE_URL
   ```

2. `.env.ec2` 파일이 있는지 확인:
   ```bash
   ls -la .env.ec2
   ```

3. `.env.ec2`를 `.env`로 다시 복사:
   ```bash
   cp .env.ec2 .env
   ```

4. **중요:** `--no-cache`로 다시 빌드해야 함:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

### CORS 에러가 발생하는 경우

`SL-Back-end/.env.local` 파일에서 CORS 설정 확인:

```bash
cat SL-Back-end/.env.local | grep CORS
```

예상 결과:
```
BACKEND_CORS_ORIGINS=["http://54.180.34.167:3000","http://localhost:3000"]
```

### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker logs sl_backend
docker logs sl_frontend

# 헬스체크 확인
docker inspect sl_backend | grep -A 10 "Health"
```

---

## 📝 환경 변수 우선순위

Docker Compose는 다음 순서로 환경 변수를 로드합니다 (높은 우선순위부터):

1. **docker-compose.yml의 environment 섹션** ⬅️ **가장 높음**
2. 루트 `.env` 파일
3. `env_file`로 지정된 파일 (`.env.local`)

**중요:** 
- `docker-compose.yml`의 `environment` 섹션에 기본값이 있으면 `.env` 파일의 값을 무시합니다.
- 현재 설정은 `docker-compose.yml`에서 `${DATABASE_URL}` 형식으로 되어 있어, 루트 `.env` 파일에서 오버라이드 가능합니다.

---

## 🔐 보안 주의사항

- `.env` 파일에는 민감한 정보(DB 비밀번호, AWS 키)가 포함되어 있습니다.
- Git에 커밋되지 않도록 `.gitignore`에 등록되어 있는지 확인하세요.
- EC2에서는 `.env.ec2`를 `.env`로 복사하여 사용합니다.

---

## 🎯 성능 최적화 적용 사항

다음 최적화가 이미 적용되어 있습니다:

1. ✅ **데이터베이스 커넥션 풀 증가** (50 connections, max overflow 100)
2. ✅ **백테스트 쿼리 최적화 인덱스** (7개 인덱스 추가)
3. ✅ **Redis 캐시 TTL 무제한** (영구 캐싱)
4. ✅ **Polars 멀티프로세싱 최적화** (spawn context)

---

## 📞 문제 발생 시

1. 백엔드 로그 확인: `docker logs -f sl_backend`
2. 프론트엔드 로그 확인: `docker logs -f sl_frontend`
3. 환경 변수 확인: `docker exec sl_backend printenv`
4. 컨테이너 상태 확인: `docker compose ps`
