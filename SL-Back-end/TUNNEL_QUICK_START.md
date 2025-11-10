# SSH 터널링 빠른 시작 가이드 🚀

## 1분 안에 SSH 터널링 설정하기

### Step 1: SSH 키와 EC2 정보 설정

`scripts/start-tunnel.sh` 파일을 열고 아래 부분을 실제 값으로 수정:

```bash
# 이 부분을 수정하세요
SSH_KEY="$HOME/.ssh/stock-lab-ec2.pem"  # EC2 SSH 키 경로
EC2_HOST="ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com"  # EC2 Public DNS
RDS_ENDPOINT="stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com"  # RDS 엔드포인트
```

### Step 2: RDS 비밀번호 설정

```bash
# .env.tunnel 파일 생성
cp .env.tunnel.template .env.tunnel

# 비밀번호 변경
vim .env.tunnel
# YOUR_RDS_PASSWORD를 실제 RDS 비밀번호로 변경
```

### Step 3: 터널 시작

```bash
# 터널 시작
./scripts/start-tunnel.sh

# 터널 상태 확인
./scripts/check-tunnel.sh
```

### Step 4: 환경 전환 및 개발

```bash
# 터널 환경으로 전환
./scripts/switch-env.sh tunnel

# 백엔드 서버 실행
uvicorn app.main:app --reload
```

---

## 일일 개발 워크플로우

### 아침에 시작할 때

```bash
cd /Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end

# 1. 터널 시작
./scripts/start-tunnel.sh

# 2. 환경 전환
./scripts/switch-env.sh tunnel

# 3. 서버 실행
uvicorn app.main:app --reload
```

### 저녁에 종료할 때

```bash
# 1. 서버 중지 (Ctrl+C)

# 2. 터널 중지
./scripts/stop-tunnel.sh

# 3. (선택) 로컬 환경으로 복귀
./scripts/switch-env.sh local
```

---

## 자주 사용하는 명령어

```bash
# 터널 시작
./scripts/start-tunnel.sh

# 터널 상태 확인
./scripts/check-tunnel.sh

# 터널 중지
./scripts/stop-tunnel.sh

# 환경 전환
./scripts/switch-env.sh tunnel    # 터널 모드
./scripts/switch-env.sh local     # 로컬 모드

# DB 연결 테스트
psql -h localhost -p 5433 -U postgres -d quant_investment_db
```

---

## 필요한 정보 찾기

### EC2 Public DNS 찾기

```bash
# AWS CLI로 찾기
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=stock-lab-*" \
    --query 'Reservations[0].Instances[0].PublicDnsName' \
    --output text

# 또는 AWS 콘솔에서:
# EC2 → Instances → 인스턴스 선택 → Public IPv4 DNS
```

### RDS 엔드포인트 찾기

```bash
# AWS CLI로 찾기
aws rds describe-db-instances \
    --db-instance-identifier stock-lab-rds \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text

# 또는 AWS 콘솔에서:
# RDS → Databases → DB 선택 → Connectivity & security → Endpoint
```

### RDS 비밀번호 확인

```bash
# Secrets Manager에서 확인 (비밀번호가 거기 저장되어 있다면)
aws secretsmanager get-secret-value \
    --secret-id stock-lab-rds-password \
    --query 'SecretString' \
    --output text

# 또는 배포 환경의 .env 파일 확인
```

---

## 트러블슈팅

### "Permission denied (publickey)"

```bash
# SSH 키 권한 수정
chmod 400 ~/.ssh/stock-lab-ec2.pem
```

### "Port 5433 already in use"

```bash
# 기존 터널 중지
./scripts/stop-tunnel.sh

# 또는 직접 종료
lsof -ti:5433 | xargs kill
```

### "Could not connect to server"

```bash
# EC2가 실행 중인지 확인
aws ec2 describe-instances \
    --instance-ids i-xxxxx \
    --query 'Reservations[0].Instances[0].State.Name'

# Security Group에서 SSH(22) 포트 열려있는지 확인
```

### 터널은 열렸는데 DB 연결 안됨

```bash
# RDS Security Group에서 EC2 Security Group 허용되어 있는지 확인
# RDS가 실행 중인지 확인
aws rds describe-db-instances \
    --db-instance-identifier stock-lab-rds \
    --query 'DBInstances[0].DBInstanceStatus'
```

---

## 보안 체크리스트

- [ ] SSH 키 파일 권한이 400인지 확인
- [ ] SSH 키가 git에 커밋되지 않도록 .gitignore에 추가
- [ ] .env.tunnel 파일이 git에 커밋되지 않도록 .gitignore에 추가
- [ ] 작업 완료 후 터널 종료
- [ ] 프로덕션 데이터 수정 시 백업 먼저 확인

---

## .gitignore 업데이트

`.gitignore`에 아래 내용 추가:

```gitignore
# SSH Keys
*.pem
*.key

# Environment files with credentials
.env.tunnel
.env.production
.env.backup

# SSH config
.ssh/
```

---

## 도움말

더 자세한 내용은 다음 파일들을 참고하세요:

- [상세 SSH 터널링 가이드](../aws-deployment/SSH_TUNNEL_SETUP.md)
- [AWS 배포 가이드](../aws-deployment/CICD_SETUP_GUIDE.md)
- [백테스트 API 명세서](docs/API_SPECIFICATION_GENPORT.md)

문제가 발생하면 Slack #dev-backend 채널에 문의하세요.
