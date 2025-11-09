# SSH 터널링을 통한 RDS 로컬 접근 가이드

## 개요

VPC 내부에 있는 RDS에 로컬에서 접근하기 위해 EC2를 점프 서버(bastion host)로 사용하는 SSH 터널링 방법입니다.

```
[로컬 PC] --SSH 터널--> [EC2] --VPC 내부--> [RDS]
```

---

## 1. SSH 터널링 설정

### 방법 1: 단일 명령어로 터널링

```bash
# 기본 형식
ssh -i /path/to/your-key.pem \
    -L 로컬포트:RDS엔드포인트:5432 \
    -N -f \
    ec2-user@EC2-PUBLIC-IP

# 예시 (5433 포트를 로컬에서 사용)
ssh -i ~/.ssh/stock-lab-ec2.pem \
    -L 5433:stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432 \
    -N -f \
    ec2-user@ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com
```

**옵션 설명:**
- `-i`: SSH 키 파일 경로
- `-L`: 로컬 포트 포워딩 (로컬포트:원격호스트:원격포트)
- `-N`: 명령어 실행 없이 포워딩만 수행
- `-f`: 백그라운드 실행

### 방법 2: SSH Config 파일 사용 (권장)

`~/.ssh/config` 파일 생성 또는 편집:

```bash
# SSH Config 파일 편집
vim ~/.ssh/config
```

아래 내용 추가:

```
# Stock Lab EC2 Bastion Host
Host stock-lab-bastion
    HostName ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com
    User ec2-user
    IdentityFile ~/.ssh/stock-lab-ec2.pem
    LocalForward 5433 stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

**사용 방법:**

```bash
# 터널링 시작
ssh stock-lab-bastion

# 또는 백그라운드로 실행
ssh -f -N stock-lab-bastion
```

---

## 2. 로컬 환경 설정

### 2-1. `.env.tunnel` 파일 생성

`SL-Back-end/.env.tunnel` 파일 생성:

```bash
# Database Configuration (SSH Tunnel through EC2 to RDS)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_RDS_PASSWORD@localhost:5433/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:YOUR_RDS_PASSWORD@localhost:5433/quant_investment_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

# Redis Configuration (SSH Tunnel through EC2)
REDIS_URL=redis://localhost:6380/0
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600
CACHE_TTL_SECONDS=3600
CACHE_PREFIX=quant
ENABLE_CACHE=True

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API (Tunnel Mode)
VERSION=1.0.0
DEBUG=True

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Performance Settings
CHUNK_SIZE=10000
MAX_WORKERS=4
ENABLE_QUERY_CACHE=True

# Backtesting Configuration
BACKTEST_MAX_CONCURRENT_JOBS=2
BACKTEST_MEMORY_LIMIT_GB=8

# CORS Settings
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quant_api.log
```

### 2-2. 환경 변수 스위칭 스크립트

`SL-Back-end/scripts/switch-env.sh` 생성:

```bash
#!/bin/bash

ENV_MODE=$1

if [ -z "$ENV_MODE" ]; then
    echo "Usage: ./switch-env.sh [local|tunnel|production]"
    exit 1
fi

case $ENV_MODE in
    local)
        echo "Switching to LOCAL environment..."
        cp .env.local .env
        echo "✅ Using local Docker PostgreSQL (localhost:5432)"
        ;;
    tunnel)
        echo "Switching to TUNNEL environment..."
        cp .env.tunnel .env
        echo "✅ Using RDS via SSH tunnel (localhost:5433)"
        ;;
    production)
        echo "Switching to PRODUCTION environment..."
        cp .env.production .env
        echo "✅ Using production RDS directly"
        ;;
    *)
        echo "Invalid mode: $ENV_MODE"
        echo "Available modes: local, tunnel, production"
        exit 1
        ;;
esac
```

**사용법:**

```bash
chmod +x scripts/switch-env.sh

# 로컬 Docker DB 사용
./scripts/switch-env.sh local

# SSH 터널을 통한 RDS 사용
./scripts/switch-env.sh tunnel

# 프로덕션 RDS 직접 연결
./scripts/switch-env.sh production
```

---

## 3. 터널링 시작 및 테스트

### 3-1. SSH 터널 시작

```bash
# SSH 터널 시작 (백그라운드)
ssh -f -N -i ~/.ssh/stock-lab-ec2.pem \
    -L 5433:stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432 \
    ec2-user@ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com

# 터널이 정상적으로 열렸는지 확인
lsof -ti:5433
# 또는
ps aux | grep "ssh.*5433"
```

### 3-2. PostgreSQL 연결 테스트

```bash
# psql로 연결 테스트
psql -h localhost -p 5433 -U postgres -d quant_investment_db

# Python으로 연결 테스트
python3 << EOF
import asyncio
import asyncpg

async def test_connection():
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='YOUR_RDS_PASSWORD',
        database='quant_investment_db'
    )
    version = await conn.fetchval('SELECT version()')
    print(f"PostgreSQL Version: {version}")
    await conn.close()

asyncio.run(test_connection())
EOF
```

### 3-3. 백엔드 서버 실행

```bash
cd SL-Back-end

# 환경 전환
./scripts/switch-env.sh tunnel

# 백엔드 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. 다중 터널링 (RDS + Redis)

Redis도 함께 터널링하려면:

```bash
# RDS + Redis 동시 터널링
ssh -i ~/.ssh/stock-lab-ec2.pem \
    -L 5433:stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432 \
    -L 6380:stock-lab-redis.xxxxx.cache.amazonaws.com:6379 \
    -N -f \
    ec2-user@ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com
```

또는 SSH Config 파일에 추가:

```
Host stock-lab-bastion
    HostName ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com
    User ec2-user
    IdentityFile ~/.ssh/stock-lab-ec2.pem
    LocalForward 5433 stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432
    LocalForward 6380 stock-lab-redis.xxxxx.cache.amazonaws.com:6379
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

---

## 5. 터널링 관리 스크립트

### 5-1. 터널 시작 스크립트

`SL-Back-end/scripts/start-tunnel.sh`:

```bash
#!/bin/bash

# 설정
SSH_KEY="$HOME/.ssh/stock-lab-ec2.pem"
EC2_HOST="ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com"
RDS_ENDPOINT="stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com"
LOCAL_PORT=5433

# 기존 터널 확인
if lsof -ti:$LOCAL_PORT > /dev/null 2>&1; then
    echo "❌ Port $LOCAL_PORT is already in use"
    echo "Run './scripts/stop-tunnel.sh' to stop existing tunnel"
    exit 1
fi

# 터널 시작
echo "🚀 Starting SSH tunnel to RDS..."
ssh -f -N -i "$SSH_KEY" \
    -L $LOCAL_PORT:$RDS_ENDPOINT:5432 \
    ec2-user@$EC2_HOST

# 확인
sleep 2
if lsof -ti:$LOCAL_PORT > /dev/null 2>&1; then
    echo "✅ SSH tunnel established successfully!"
    echo "📍 RDS accessible at: localhost:$LOCAL_PORT"
    echo ""
    echo "Test connection:"
    echo "  psql -h localhost -p $LOCAL_PORT -U postgres -d quant_investment_db"
else
    echo "❌ Failed to establish SSH tunnel"
    exit 1
fi
```

### 5-2. 터널 중지 스크립트

`SL-Back-end/scripts/stop-tunnel.sh`:

```bash
#!/bin/bash

LOCAL_PORT=5433

# 터널 프로세스 찾기
PID=$(lsof -ti:$LOCAL_PORT)

if [ -z "$PID" ]; then
    echo "ℹ️  No tunnel found on port $LOCAL_PORT"
    exit 0
fi

# 프로세스 종료
echo "🛑 Stopping SSH tunnel (PID: $PID)..."
kill $PID

# 확인
sleep 1
if lsof -ti:$LOCAL_PORT > /dev/null 2>&1; then
    echo "⚠️  Failed to stop tunnel, force killing..."
    kill -9 $PID
fi

echo "✅ SSH tunnel stopped"
```

### 5-3. 터널 상태 확인 스크립트

`SL-Back-end/scripts/check-tunnel.sh`:

```bash
#!/bin/bash

LOCAL_PORT=5433

# 터널 상태 확인
PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo "❌ SSH tunnel is NOT running"
    echo "Run './scripts/start-tunnel.sh' to start tunnel"
    exit 1
else
    echo "✅ SSH tunnel is running (PID: $PID)"
    echo "📍 Port forwarding: localhost:$LOCAL_PORT -> RDS:5432"

    # 프로세스 정보
    echo ""
    echo "Process details:"
    ps -p $PID -o pid,ppid,user,command

    # 연결 테스트 (선택사항)
    echo ""
    read -p "Test database connection? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pg_isready -h localhost -p $LOCAL_PORT
    fi
fi
```

**실행 권한 부여:**

```bash
chmod +x scripts/start-tunnel.sh
chmod +x scripts/stop-tunnel.sh
chmod +x scripts/check-tunnel.sh
```

---

## 6. 개발 워크플로우

### 기존 방식 (비효율)
```
코드 수정 → 커밋 → 푸시 → 배포 → 테스트 → 에러 확인 → 반복...
```

### 새로운 방식 (효율적)
```
1. SSH 터널 시작:
   ./scripts/start-tunnel.sh

2. 환경 전환:
   ./scripts/switch-env.sh tunnel

3. 로컬에서 개발 & 테스트:
   uvicorn app.main:app --reload

4. 실시간 RDS 데이터로 테스트

5. 테스트 완료 후 배포
```

---

## 7. pgAdmin을 통한 GUI 접속

### 7-1. pgAdmin에서 서버 추가

1. pgAdmin 실행
2. Servers 우클릭 → Create → Server
3. General 탭:
   - Name: `Stock Lab RDS (via SSH Tunnel)`
4. Connection 탭:
   - Host: `localhost`
   - Port: `5433`
   - Username: `postgres`
   - Password: `YOUR_RDS_PASSWORD`
5. Advanced 탭:
   - DB restriction: `quant_investment_db`

### 7-2. DBeaver 사용 (권장)

1. New Connection → PostgreSQL
2. Main 탭:
   - Host: `localhost`
   - Port: `5433`
   - Database: `quant_investment_db`
   - Username: `postgres`
   - Password: `YOUR_RDS_PASSWORD`
3. Test Connection

---

## 8. 트러블슈팅

### 문제 1: "Permission denied (publickey)"

**해결:**
```bash
# SSH 키 권한 확인
chmod 400 ~/.ssh/stock-lab-ec2.pem

# SSH 에이전트에 키 추가
ssh-add ~/.ssh/stock-lab-ec2.pem
```

### 문제 2: "Port 5433 already in use"

**해결:**
```bash
# 기존 터널 중지
./scripts/stop-tunnel.sh

# 또는 직접 프로세스 종료
lsof -ti:5433 | xargs kill
```

### 문제 3: "Could not resolve hostname"

**해결:**
```bash
# RDS 엔드포인트 확인
aws rds describe-db-instances \
    --db-instance-identifier stock-lab-rds \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
```

### 문제 4: 터널이 자주 끊김

**해결:**

SSH Config에 KeepAlive 옵션 추가:

```
Host stock-lab-bastion
    ...
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

---

## 9. 보안 고려사항

1. **SSH 키 관리**
   ```bash
   # SSH 키는 절대 git에 커밋하지 말 것
   echo "*.pem" >> .gitignore
   ```

2. **RDS 비밀번호 관리**
   ```bash
   # .env.tunnel 파일도 .gitignore에 추가
   echo ".env.tunnel" >> .gitignore
   ```

3. **터널 사용 후 종료**
   ```bash
   # 작업 완료 후 반드시 터널 종료
   ./scripts/stop-tunnel.sh
   ```

---

## 10. 유용한 명령어 모음

```bash
# 터널 시작
./scripts/start-tunnel.sh

# 터널 상태 확인
./scripts/check-tunnel.sh

# 터널 중지
./scripts/stop-tunnel.sh

# RDS 연결 테스트
psql -h localhost -p 5433 -U postgres -d quant_investment_db -c "SELECT version();"

# 테이블 목록 확인
psql -h localhost -p 5433 -U postgres -d quant_investment_db -c "\dt"

# 백테스트 결과 조회
psql -h localhost -p 5433 -U postgres -d quant_investment_db -c "SELECT * FROM backtests LIMIT 5;"
```

---

이제 로컬에서 배포된 RDS에 접근하여 빠르게 개발하고 테스트할 수 있습니다! 🚀