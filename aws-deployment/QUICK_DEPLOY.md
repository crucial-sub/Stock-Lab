# 🚀 AWS 빠른 배포 가이드

이 가이드는 Stack Lab Demo를 AWS에 빠르게 배포하기 위한 단계별 체크리스트입니다.

## ⏱️ 예상 소요 시간: 60-90분

---

## 📋 사전 준비

- [ ] AWS 계정 생성
- [ ] AWS CLI 설치 및 구성 (`aws configure`)
- [ ] SSH 키 페어 생성 (.pem 파일)
- [ ] 본인 IP 주소 확인 (https://whatismyipaddress.com/)

---

## 🔐 1단계: Security Groups 생성 (10분)

### 방법 1: AWS CLI 사용 (빠름)

```bash
cd aws-deployment

# 스크립트 편집
nano security-groups-setup.sh
# VPC_ID와 YOUR_IP를 실제 값으로 변경

# 실행
./security-groups-setup.sh

# 생성된 Security Group IDs 저장
cat security-groups-ids.json
```

### 방법 2: AWS Console 사용

[AWS_DEPLOYMENT_GUIDE.md](../AWS_DEPLOYMENT_GUIDE.md#security-groups-설정) 참조

---

## 🗄️ 2단계: RDS PostgreSQL 생성 (15분)

**AWS Console → RDS → Create database**

### 핵심 설정

```
Engine: PostgreSQL 15.x
Template: Dev/Test (개발용) 또는 Production (프로덕션)

DB instance identifier: sl-postgres-db
Master username: postgres
Master password: <강력한 비밀번호>

DB instance class: db.t3.micro (개발) / db.t3.medium (프로덕션)
Storage: 20 GiB gp3, Enable auto-scaling to 100 GiB

Multi-AZ: No (개발) / Yes (프로덕션)
VPC security group: sl-rds-sg
Public access: No

Initial database name: quant_investment_db
Backup retention: 7 days
```

### 생성 후

```bash
# RDS 엔드포인트 저장
RDS_ENDPOINT="sl-postgres-db.xxxxx.ap-northeast-2.rds.amazonaws.com"
```

---

## 🔴 3단계: ElastiCache Redis 생성 (10분)

**AWS Console → ElastiCache → Redis → Create**

### 핵심 설정

```
Cluster mode: Disabled
Name: sl-redis-cluster
Engine version: 7.x
Port: 6379
Node type: cache.t3.micro (개발) / cache.t3.medium (프로덕션)
Number of replicas: 0 (개발) / 1 (프로덕션)

Subnet group: Create new
  Name: sl-redis-subnet-group
  Subnets: 2개 이상 선택

Security groups: sl-redis-sg
Encryption at rest: Yes
Encryption in transit: No (개발) / Yes (프로덕션)
```

### 생성 후

```bash
# Redis 엔드포인트 저장
REDIS_ENDPOINT="sl-redis-cluster.xxxxx.cache.amazonaws.com"
```

---

## 💻 4단계: EC2 인스턴스 설정 및 AMI 생성 (20분)

### 4-1. 첫 번째 EC2 인스턴스 시작

```
AMI: Ubuntu Server 22.04 LTS
Instance type: t3.medium (프로덕션) / t3.small (개발)
Key pair: 선택 또는 새로 생성
VPC: 기본 VPC
Subnet: Public subnet 선택
Security group: sl-ec2-sg
Storage: 30 GiB gp3
```

### 4-2. SSH 접속 및 환경 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 재로그인 (docker 그룹 적용)
exit
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# 프로젝트 클론
cd ~
git clone https://github.com/Krafton-Jungle-10-Final-Project/Stock-Lab-Demo.git
cd Stock-Lab-Demo
```

### 4-3. 환경 변수 설정

```bash
# Backend .env 파일 생성
cat > SL-Back-end/.env <<EOF
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_RDS_PASSWORD@${RDS_ENDPOINT}:5432/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:YOUR_RDS_PASSWORD@${RDS_ENDPOINT}:5432/quant_investment_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
REDIS_HOST=${REDIS_ENDPOINT}
REDIS_PORT=6379

API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

BACKEND_CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
LOG_FILE=logs/quant_api.log
EOF

# Frontend .env.local 생성 (ALB 생성 후 업데이트)
cat > SL-Front-End/.env.local <<EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
EOF

# 루트 .env 생성
cat > .env <<EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
EOF
```

### 4-4. 테스트 실행

```bash
# 로그 디렉토리 생성
mkdir -p SL-Back-end/logs

# Docker Compose 실행
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 헬스 체크
curl http://localhost:8000/health
curl http://localhost:3000

# 컨테이너 중지
docker-compose -f docker-compose.prod.yml down
```

### 4-5. AMI 생성

```
EC2 Console → Instances → 인스턴스 선택 → Actions → Image and templates → Create image

Image name: stacklab-app-ami-v1
Image description: Stack Lab App with Docker and project
Reboot instance: Yes
```

AMI 생성 완료까지 약 5-10분 소요

---

## 🚀 5단계: Launch Template 생성 (5분)

**EC2 Console → Launch Templates → Create launch template**

```
Launch template name: stacklab-launch-template
AMI: stacklab-app-ami-v1
Instance type: t3.medium
Key pair: 선택
Security groups: sl-ec2-sg
Storage: 30 GiB gp3

IAM instance profile: Create new with CloudWatch permissions

User data: (ec2-user-data.sh 내용 복사)
  - RDS_ENDPOINT, REDIS_ENDPOINT, RDS_PASSWORD, ALB_DNS_NAME 수정
```

---

## ⚖️ 6단계: Application Load Balancer 생성 (15분)

### 6-1. Target Groups 생성

#### Backend Target Group

```
Target group name: sl-backend-tg
Target type: Instances
Protocol: HTTP, Port: 8000

Health check path: /health
Healthy threshold: 2
Unhealthy threshold: 3
Timeout: 5 seconds
Interval: 30 seconds
```

#### Frontend Target Group

```
Target group name: sl-frontend-tg
Target type: Instances
Protocol: HTTP, Port: 3000

Health check path: /
Healthy threshold: 2
Unhealthy threshold: 3
Timeout: 5 seconds
Interval: 30 seconds
```

### 6-2. ALB 생성

```
Load balancer name: sl-application-lb
Scheme: Internet-facing
IP address type: IPv4

VPC: 선택한 VPC
Availability Zones: 2개 이상 선택 (Public subnets)

Security groups: sl-alb-sg

Listeners:
  - HTTP:80 → Forward to sl-frontend-tg
```

### 6-3. Listener Rules 추가

```
HTTP:80 Listener → View/edit rules → Add rule

Rule 1:
  IF Path is /api/*
  THEN Forward to sl-backend-tg
  Priority: 1

Default: Forward to sl-frontend-tg
```

### 6-4. ALB DNS 이름 저장

```bash
ALB_DNS_NAME="sl-application-lb-xxxxxxxxxx.ap-northeast-2.elb.amazonaws.com"
```

---

## 📈 7단계: Auto Scaling Group 생성 (10분)

**EC2 Console → Auto Scaling Groups → Create Auto Scaling group**

```
Auto Scaling group name: sl-auto-scaling-group
Launch template: stacklab-launch-template (Latest)

VPC: 선택한 VPC
Availability Zones: 2개 이상 (Private subnets 권장)

Load balancing:
  - Attach to existing load balancer
  - Choose target groups: sl-backend-tg, sl-frontend-tg

Health checks:
  - ELB health check
  - Grace period: 300 seconds

Group size:
  - Desired: 2
  - Minimum: 2
  - Maximum: 4

Scaling policies:
  - Target tracking scaling policy
  - Metric: Average CPU utilization
  - Target value: 70%
  - Instance warmup: 300 seconds
```

### 인스턴스 시작 확인

```
EC2 Console → Instances → 2개의 인스턴스가 "running" 상태
Target Groups → Targets → 2개의 인스턴스가 "healthy" 상태
```

---

## 8단계: 환경 변수 업데이트 (5분)

Auto Scaling Group이 시작되면 ALB DNS로 환경 변수를 업데이트해야 합니다.

### 방법 1: Launch Template User Data 수정

```bash
# Launch Template 수정
# User Data에서 ALB_DNS_NAME을 실제 값으로 변경

export ALB_DNS_NAME="sl-application-lb-xxxxx.ap-northeast-2.elb.amazonaws.com"
```

### 방법 2: Systems Manager Parameter Store 사용 (권장)

```bash
# Parameter Store에 저장
aws ssm put-parameter \
  --name "/stacklab/alb/dns" \
  --value "$ALB_DNS_NAME" \
  --type String \
  --region ap-northeast-2

# User Data에서 가져오기
export ALB_DNS_NAME=$(aws ssm get-parameter --name "/stacklab/alb/dns" --query 'Parameter.Value' --output text)
```

### Auto Scaling Group 인스턴스 재시작

```
Auto Scaling Group → Instance refresh
  - Minimum healthy percentage: 50%
  - Instance warmup: 300 seconds
```

---

## ✅ 9단계: 테스트 및 확인 (10분)

### 접속 테스트

```bash
# Frontend 접속
curl http://$ALB_DNS_NAME

# Backend API 접속
curl http://$ALB_DNS_NAME/api/v1

# Health check
curl http://$ALB_DNS_NAME/api/v1/health
```

### 브라우저 테스트

```
Frontend: http://<ALB-DNS-NAME>
Backend Docs: http://<ALB-DNS-NAME>/api/v1/docs
```

### Target Groups Health Check

```
EC2 Console → Target Groups → sl-backend-tg → Targets
모든 인스턴스가 "healthy" 상태인지 확인

EC2 Console → Target Groups → sl-frontend-tg → Targets
모든 인스턴스가 "healthy" 상태인지 확인
```

---

## 🔧 10단계: CloudWatch 모니터링 설정 (선택, 10분)

### Log Groups 생성

```bash
aws logs create-log-group --log-group-name /aws/stacklab/backend --region ap-northeast-2
aws logs create-log-group --log-group-name /aws/stacklab/frontend --region ap-northeast-2
aws logs create-log-group --log-group-name /aws/stacklab/system --region ap-northeast-2
```

### Alarms 생성

```
CloudWatch → Alarms → Create alarm

1. High CPU Alarm
   - Metric: EC2 CPUUtilization
   - Threshold: > 80% for 2 periods of 5 minutes

2. Unhealthy Targets
   - Metric: ALB UnHealthyHostCount
   - Threshold: >= 1

3. RDS High Connections
   - Metric: RDS DatabaseConnections
   - Threshold: > 80
```

---

## 🎉 완료!

배포가 완료되었습니다. 이제 팀원들이 ALB DNS 주소로 접속할 수 있습니다.

### 접속 정보

```
Frontend: http://<ALB-DNS-NAME>
Backend API: http://<ALB-DNS-NAME>/api/v1
API Docs: http://<ALB-DNS-NAME>/api/v1/docs
```

---

## 📊 비용 모니터링

**AWS Console → Cost Explorer**

예상 월별 비용 (개발 환경):
- EC2 (t3.medium × 2): ~$60
- RDS (db.t3.micro): ~$25
- ElastiCache (cache.t3.micro): ~$15
- ALB: ~$20
- **Total: ~$120/month**

---

## 🔄 다음 단계

- [ ] HTTPS 설정 (ACM + Route 53)
- [ ] 도메인 연결
- [ ] CI/CD 파이프라인 구축
- [ ] WAF 설정
- [ ] S3 백업 설정
- [ ] CloudFront CDN 설정

---

## 🆘 문제 해결

### Target이 Unhealthy 상태

```bash
# EC2 인스턴스에 SSH 접속
ssh -i your-key.pem ubuntu@<EC2-IP>

# Docker 컨테이너 확인
docker ps

# 로그 확인
cd ~/Stock-Lab-Demo
docker-compose -f docker-compose.prod.yml logs

# Security Group 확인
# sl-ec2-sg에 sl-alb-sg로부터 8000, 3000 포트 허용 확인
```

### ALB에서 502 Bad Gateway

```bash
# Backend health check 실패
curl http://localhost:8000/health

# 환경 변수 확인
cat ~/Stock-Lab-Demo/SL-Back-end/.env

# RDS 연결 테스트
telnet <RDS-ENDPOINT> 5432
```

### 인스턴스가 시작되지 않음

```bash
# User Data 로그 확인
ssh -i your-key.pem ubuntu@<EC2-IP>
sudo cat /var/log/user-data.log
```

---

**배포에 성공하셨다면 축하합니다! 🎊**
