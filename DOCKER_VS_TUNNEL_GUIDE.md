# Docker 배포 환경 vs SSH 터널링 가이드

## 환경별 RDS 접근 방식

### 🏠 로컬 개발 환경 (당신의 맥북)

**SSH 터널링 사용 ✅**

```
[맥북] --SSH 터널--> [EC2] --VPC 내부--> [RDS]
  ↓
localhost:5433으로 RDS 접근
```

**사용 방법:**
```bash
./scripts/start-tunnel.sh
./scripts/switch-env.sh tunnel
uvicorn app.main:app --reload
```

---

### 🚀 배포 환경 (EC2 Docker 컨테이너)

**VPC 내부 직접 연결 ✅**

```
[EC2 Docker Container] --VPC 내부--> [RDS]
  ↓
RDS 엔드포인트로 직접 접근
```

**이유:**
- EC2가 이미 VPC 내부에 있음
- Docker 컨테이너도 EC2 내부에서 실행
- VPC 내부에서는 RDS 엔드포인트로 직접 접근 가능
- SSH 터널링 불필요!

---

## 환경별 .env 설정

### 1. 로컬 개발 - Docker 사용 (.env.local)

```bash
# 로컬 Docker PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@localhost:5432/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:postgres123@localhost:5432/quant_investment_db
```

**사용:**
```bash
docker-compose up -d
./scripts/switch-env.sh local
uvicorn app.main:app --reload
```

---

### 2. 로컬 개발 - SSH 터널 사용 (.env.tunnel)

```bash
# SSH 터널을 통한 프로덕션 RDS
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_RDS_PASSWORD@localhost:5433/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:YOUR_RDS_PASSWORD@localhost:5433/quant_investment_db
```

**사용:**
```bash
./scripts/start-tunnel.sh
./scripts/switch-env.sh tunnel
uvicorn app.main:app --reload
```

---

### 3. EC2 Docker 배포 환경 (.env)

```bash
# EC2는 VPC 내부에 있으므로 RDS 엔드포인트로 직접 접근
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_RDS_PASSWORD@stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:YOUR_RDS_PASSWORD@stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com:5432/quant_investment_db

# Redis도 ElastiCache 엔드포인트로 직접 접근
REDIS_URL=redis://stock-lab-redis.xxxxx.cache.amazonaws.com:6379/0
REDIS_HOST=stock-lab-redis.xxxxx.cache.amazonaws.com
REDIS_PORT=6379
```

**배포 시 사용:**
- GitHub Actions가 EC2에 SSH로 접속
- `.env` 파일 업데이트 (또는 Secrets Manager 사용)
- `docker-compose -f docker-compose.prod.yml up -d`

---

## 핵심 차이점

### 로컬 환경 (맥북)

```
문제: 맥북은 VPC 밖에 있음 ❌
해결: SSH 터널링으로 EC2를 통해 우회 ✅

[맥북] ❌→ [RDS (VPC 내부)]
[맥북] --SSH--> [EC2] ✅→ [RDS]
```

### 배포 환경 (EC2 Docker)

```
문제 없음: EC2가 이미 VPC 내부에 있음 ✅
방법: RDS 엔드포인트로 직접 연결

[EC2 Docker Container] ✅→ [RDS (VPC 내부)]
```

---

## 배포 시나리오

### 시나리오 1: GitHub Actions 자동 배포

```yaml
# .github/workflows/deploy.yml

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ec2-user/Stock-Lab-Demo

            # .env 업데이트 (Secrets에서 가져오기)
            echo "DATABASE_URL=${{ secrets.DATABASE_URL }}" > SL-Back-end/.env
            echo "REDIS_URL=${{ secrets.REDIS_URL }}" >> SL-Back-end/.env

            # Docker Compose로 배포
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
```

**EC2 내부에서 실행되므로 RDS 직접 접근 가능!**

---

### 시나리오 2: 수동 배포

```bash
# 1. EC2에 SSH 접속
ssh -i ~/.ssh/Stock-Lab-Dev.pem ec2-user@your-ec2-host

# 2. 프로젝트 디렉토리로 이동
cd /home/ec2-user/Stock-Lab-Demo

# 3. .env 확인/수정
vim SL-Back-end/.env

# 확인할 내용:
# DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@RDS-ENDPOINT:5432/quant_investment_db
# REDIS_URL=redis://REDIS-ENDPOINT:6379/0

# 4. 배포
docker-compose -f docker-compose.prod.yml up -d

# 5. 로그 확인
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## 네트워크 구성도

### 로컬 개발 환경

```
┌─────────────────────────────────────────┐
│ 당신의 맥북 (VPC 외부)                    │
│                                         │
│  [터미널]                                │
│     ↓ SSH 터널 (start-tunnel.sh)        │
│  localhost:5433                         │
│     ↓                                   │
└─────┼───────────────────────────────────┘
      │
      │ SSH Tunnel
      ↓
┌─────────────────────────────────────────┐
│ EC2 (VPC 내부)                          │
│     ↓                                   │
│  [점프 서버 역할]                        │
│     ↓                                   │
└─────┼───────────────────────────────────┘
      │
      │ VPC 내부 통신
      ↓
┌─────────────────────────────────────────┐
│ RDS (VPC 내부)                          │
│  stock-lab-rds.xxxxx.rds.amazonaws.com  │
└─────────────────────────────────────────┘
```

### 배포 환경

```
┌─────────────────────────────────────────┐
│ EC2 (VPC 내부)                          │
│                                         │
│  [Docker Container - Backend]           │
│     ↓ 직접 연결                         │
│  RDS_ENDPOINT:5432                      │
│     ↓                                   │
└─────┼───────────────────────────────────┘
      │
      │ VPC 내부 통신 (직접)
      ↓
┌─────────────────────────────────────────┐
│ RDS (VPC 내부)                          │
│  stock-lab-rds.xxxxx.rds.amazonaws.com  │
└─────────────────────────────────────────┘
```

**핵심: EC2 Docker는 VPC 내부에 있으므로 터널링 불필요!**

---

## Security Group 설정

### RDS Security Group

**Inbound Rules:**

```
Type        Protocol  Port  Source                Description
──────────────────────────────────────────────────────────────
PostgreSQL  TCP       5432  sg-xxxxx (EC2 SG)     EC2에서 RDS 접근 허용
PostgreSQL  TCP       5432  10.0.0.0/16           VPC 내부 통신 허용
```

**주의:**
- **외부 IP 차단**: 0.0.0.0/0 허용하지 말 것! ❌
- **EC2 Security Group만 허용**: VPC 내부 통신만 허용 ✅

### EC2 Security Group

**Inbound Rules:**

```
Type  Protocol  Port  Source          Description
────────────────────────────────────────────────────
SSH   TCP       22    Your-IP/32      SSH 터널용 (당신의 IP만)
HTTP  TCP       80    0.0.0.0/0       웹 접근
HTTPS TCP       443   0.0.0.0/0       웹 접근 (SSL)
```

---

## 환경별 체크리스트

### ✅ 로컬 개발 (SSH 터널)

- [ ] EC2 SSH 키가 있음 (`Stock-Lab-Dev.pem`)
- [ ] `start-tunnel.sh`에 EC2 정보 설정됨
- [ ] `.env.tunnel`에 RDS 비밀번호 설정됨
- [ ] EC2 Security Group에서 SSH(22) 허용됨
- [ ] RDS Security Group에서 EC2 허용됨
- [ ] 터널 시작: `./scripts/start-tunnel.sh`
- [ ] 환경 전환: `./scripts/switch-env.sh tunnel`

### ✅ 배포 환경 (EC2 Docker)

- [ ] EC2가 VPC 내부에 있음
- [ ] RDS Security Group에서 EC2 Security Group 허용됨
- [ ] `.env` 파일에 RDS 엔드포인트 직접 설정됨
- [ ] Docker Compose로 배포됨
- [ ] 컨테이너 로그에서 DB 연결 확인됨

---

## 실제 배포 시나리오

### 개발자 워크플로우

```bash
# 1. 로컬에서 SSH 터널로 개발
./scripts/start-tunnel.sh
./scripts/switch-env.sh tunnel
uvicorn app.main:app --reload

# 2. 기능 개발 & 테스트 (프로덕션 DB로 테스트)
# ... 코딩 ...

# 3. 테스트 완료 후 커밋
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin feature-branch

# 4. PR 생성 및 병합

# 5. GitHub Actions 자동 배포
# - EC2에 SSH 접속
# - git pull
# - docker-compose 재시작
# - EC2 Docker는 VPC 내부에서 RDS 직접 접근!
```

---

## FAQ

### Q1: 로컬에서 SSH 터널을 사용하는데, 배포 환경도 터널을 사용해야 하나요?

**A:** ❌ 아니요! 배포 환경(EC2 Docker)은 이미 VPC 내부에 있으므로 RDS 엔드포인트로 직접 연결합니다.

---

### Q2: EC2 Docker 컨테이너가 어떻게 RDS에 접근하나요?

**A:** EC2가 VPC 내부에 있고, Docker 컨테이너도 EC2 네트워크를 사용하므로 VPC 내부 통신으로 RDS에 직접 접근합니다.

```
Docker Container → EC2 Network → VPC Network → RDS
```

---

### Q3: 배포 환경 .env에도 localhost:5433을 써야 하나요?

**A:** ❌ 절대 안 됩니다! 배포 환경에는 RDS 엔드포인트를 직접 씁니다:

```bash
# ❌ 잘못된 예시 (배포 환경)
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5433/db

# ✅ 올바른 예시 (배포 환경)
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@stock-lab-rds.xxxxx.rds.amazonaws.com:5432/db
```

---

### Q4: Docker Compose 파일 수정이 필요한가요?

**A:** ❌ `docker-compose.prod.yml`은 수정할 필요 없습니다. `.env` 파일만 올바르게 설정하면 됩니다.

---

### Q5: GitHub Actions에서 배포 시 터널이 필요한가요?

**A:** ❌ GitHub Actions는 EC2에 SSH로 접속해서 명령을 실행합니다. 배포된 Docker 컨테이너가 VPC 내부에서 RDS에 직접 접근하므로 터널 불필요합니다.

---

## 요약

| 환경 | 위치 | RDS 접근 방법 | 설정 파일 |
|------|------|--------------|----------|
| **로컬 개발 (Docker)** | VPC 외부 | localhost:5432 (로컬 DB) | `.env.local` |
| **로컬 개발 (터널)** | VPC 외부 | localhost:5433 (SSH 터널) | `.env.tunnel` |
| **EC2 배포** | VPC 내부 | RDS 엔드포인트 직접 | `.env` (프로덕션) |

**핵심:**
- 🏠 **로컬**: SSH 터널 사용
- 🚀 **배포**: RDS 직접 연결

SSH 터널링은 **로컬 개발을 편하게 하기 위한 도구**이며, 배포 환경에는 영향을 주지 않습니다! ✅