# AWS 배포 가이드

Stack Lab Demo 프로젝트를 AWS에 배포하기 위한 완전한 가이드입니다.

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [배포 순서](#배포-순서)
3. [Security Groups 설정](#security-groups-설정)
4. [RDS PostgreSQL 설정](#rds-postgresql-설정)
5. [ElastiCache Redis 설정](#elasticache-redis-설정)
6. [AMI 및 Launch Template 생성](#ami-및-launch-template-생성)
7. [Application Load Balancer 설정](#application-load-balancer-설정)
8. [Auto Scaling Group 설정](#auto-scaling-group-설정)
9. [Route 53 DNS 설정](#route-53-dns-설정)
10. [CloudWatch 모니터링](#cloudwatch-모니터링)
11. [추가 권장 AWS 서비스](#추가-권장-aws-서비스)
12. [비용 최적화](#비용-최적화)

---

## 🏗️ 아키텍처 개요

```
                                    [Route 53]
                                        ↓
                                  [CloudFront] (선택)
                                        ↓
┌────────────────────────────────────────────────────────────────┐
│                    Application Load Balancer                   │
│              (Port 80/443 → Backend:8000, Frontend:3000)       │
└────────────────────────────────────────────────────────────────┘
         ↓                                              ↓
┌──────────────────┐                          ┌──────────────────┐
│   Target Group   │                          │   Target Group   │
│    (Backend)     │                          │   (Frontend)     │
└──────────────────┘                          └──────────────────┘
         ↓                                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Auto Scaling Group                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ EC2 (1)  │  │ EC2 (2)  │  │ EC2 (3)  │  │ EC2 (4)  │       │
│  │ Backend  │  │ Backend  │  │ Backend  │  │ Backend  │       │
│  │ Frontend │  │ Frontend │  │ Frontend │  │ Frontend │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  Min: 2, Max: 4, Desired: 2                                    │
└──────────────────────────────────────────────────────────────────┘
         ↓                                              ↓
┌──────────────────┐                          ┌──────────────────┐
│   RDS PostgreSQL │                          │ ElastiCache Redis│
│   (Multi-AZ)     │                          │  (Cluster Mode)  │
└──────────────────┘                          └──────────────────┘
```

### 주요 구성 요소

- **ALB (Application Load Balancer)**: HTTP/HTTPS 트래픽 분산
- **EC2 Auto Scaling Group**: 최소 2개, 최대 4개 인스턴스
- **RDS PostgreSQL**: 관리형 데이터베이스 (Multi-AZ)
- **ElastiCache Redis**: 캐싱 및 세션 관리
- **CloudWatch**: 로그 및 모니터링
- **S3**: 정적 파일 및 백업 저장

---

## 🔄 배포 순서

### 1단계: VPC 및 네트워크 설정
### 2단계: Security Groups 생성
### 3단계: RDS PostgreSQL 생성
### 4단계: ElastiCache Redis 생성
### 5단계: EC2 인스턴스 설정 및 AMI 생성
### 6단계: Launch Template 생성
### 7단계: Target Groups 생성
### 8단계: Application Load Balancer 생성
### 9단계: Auto Scaling Group 생성
### 10단계: CloudWatch 설정

---

## 🔒 Security Groups 설정

### 1. ALB Security Group
**이름**: `sl-alb-sg`

**인바운드 규칙**:
```
Type            Protocol    Port Range    Source              Description
HTTP            TCP         80            0.0.0.0/0          Public HTTP
HTTPS           TCP         443           0.0.0.0/0          Public HTTPS
```

**아웃바운드 규칙**:
```
Type            Protocol    Port Range    Destination         Description
All traffic     All         All           0.0.0.0/0          Allow all outbound
```

### 2. EC2 Instance Security Group
**이름**: `sl-ec2-sg`

**인바운드 규칙**:
```
Type            Protocol    Port Range    Source              Description
Custom TCP      TCP         8000          sl-alb-sg          Backend API from ALB
Custom TCP      TCP         3000          sl-alb-sg          Frontend from ALB
SSH             TCP         22            Your-IP/32         SSH access (restrict to your IP)
```

**아웃바운드 규칙**:
```
Type            Protocol    Port Range    Destination         Description
All traffic     All         All           0.0.0.0/0          Allow all outbound
```

### 3. RDS Security Group
**이름**: `sl-rds-sg`

**인바운드 규칙**:
```
Type            Protocol    Port Range    Source              Description
PostgreSQL      TCP         5432          sl-ec2-sg          From EC2 instances
```

**아웃바운드 규칙**: 기본값 유지

### 4. ElastiCache Security Group
**이름**: `sl-redis-sg`

**인바운드 규칙**:
```
Type            Protocol    Port Range    Source              Description
Custom TCP      TCP         6379          sl-ec2-sg          From EC2 instances
```

**아웃바운드 규칙**: 기본값 유지

---

## 🗄️ RDS PostgreSQL 설정

### 1. RDS 인스턴스 생성

**AWS Console → RDS → Create database**

#### 기본 설정
```
Engine type: PostgreSQL
Version: PostgreSQL 15.x
Template: Production (또는 Dev/Test for lower cost)
```

#### DB 인스턴스 설정
```
DB instance identifier: sl-postgres-db
Master username: postgres
Master password: <강력한 비밀번호 설정>
```

#### 인스턴스 구성
```
DB instance class:
  - Production: db.t3.medium (2 vCPU, 4 GiB RAM)
  - Dev/Test: db.t3.micro (2 vCPU, 1 GiB RAM)

Storage:
  - Storage type: General Purpose SSD (gp3)
  - Allocated storage: 20 GiB
  - Enable storage autoscaling: Yes
  - Maximum storage threshold: 100 GiB
```

#### 가용성 및 내구성
```
Multi-AZ deployment: Yes (프로덕션 환경)
```

#### 연결
```
VPC: 기본 VPC 또는 사용자 정의 VPC
Public access: No
VPC security group: sl-rds-sg
Availability Zone: No preference
```

#### 데이터베이스 인증
```
Database authentication: Password authentication
```

#### 추가 구성
```
Initial database name: quant_investment_db
DB parameter group: default
Backup retention period: 7 days
Enable encryption: Yes
Performance Insights: Enable (선택)
Enable Enhanced monitoring: Yes
Monitoring role: Create new role
Deletion protection: Enable (프로덕션)
```

### 2. 엔드포인트 정보 저장

생성 후 RDS 엔드포인트를 확인하고 저장:
```
Endpoint: sl-postgres-db.xxxxxxxxxx.ap-northeast-2.rds.amazonaws.com
Port: 5432
```

이 정보를 EC2 인스턴스의 환경 변수에 사용합니다.

---

## 🔴 ElastiCache Redis 설정

### 1. ElastiCache 클러스터 생성

**AWS Console → ElastiCache → Redis → Create**

#### 클러스터 설정
```
Cluster mode: Disabled (개발) / Enabled (프로덕션)
Name: sl-redis-cluster
Engine version: 7.x
Port: 6379
Parameter group: default.redis7
Node type: cache.t3.micro (개발) / cache.t3.medium (프로덕션)
Number of replicas: 1 (High Availability)
```

#### 서브넷 그룹
```
Subnet group: Create new
Name: sl-redis-subnet-group
VPC: 선택한 VPC
Subnets: 2개 이상의 서브넷 선택 (다른 AZ)
```

#### 보안
```
Security groups: sl-redis-sg
Encryption at rest: Yes
Encryption in transit: Yes
```

### 2. 엔드포인트 정보 저장

```
Primary endpoint: sl-redis-cluster.xxxxxx.cache.amazonaws.com
Port: 6379
```

---

## 💻 AMI 및 Launch Template 생성

### 1. 기본 EC2 인스턴스 수동 설정

먼저 하나의 EC2 인스턴스를 수동으로 설정하고 AMI를 생성합니다.

#### EC2 인스턴스 시작
```
AMI: Ubuntu Server 22.04 LTS
Instance type: t3.medium (프로덕션) / t3.small (개발)
Key pair: 새로 생성 또는 기존 키 선택
Network: VPC 및 Public subnet 선택
Security group: sl-ec2-sg
Storage: 30 GiB gp3
```

#### SSH 접속 및 환경 설정

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
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo apt install -y git

# CloudWatch Agent 설치 (선택)
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# 프로젝트 클론
cd /home/ubuntu
git clone https://github.com/Krafton-Jungle-10-Final-Project/Stock-Lab-Demo.git
cd Stock-Lab-Demo

# 환경 변수 설정 스크립트 생성 (다음 섹션 참조)
```

#### 환경 변수 설정

`/home/ubuntu/Stock-Lab-Demo/setup-env.sh` 생성:

```bash
#!/bin/bash

# RDS PostgreSQL 엔드포인트
export RDS_ENDPOINT="sl-postgres-db.xxxxxxxxxx.ap-northeast-2.rds.amazonaws.com"
export REDIS_ENDPOINT="sl-redis-cluster.xxxxxx.cache.amazonaws.com"

# Backend .env 파일 생성
cat > /home/ubuntu/Stock-Lab-Demo/SL-Back-end/.env << EOF
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@${RDS_ENDPOINT}:5432/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:YOUR_PASSWORD@${RDS_ENDPOINT}:5432/quant_investment_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
REDIS_HOST=${REDIS_ENDPOINT}
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600
CACHE_TTL_SECONDS=3600
CACHE_PREFIX=quant
ENABLE_CACHE=True

API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API
VERSION=1.0.0
DEBUG=False

SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CHUNK_SIZE=10000
MAX_WORKERS=4
ENABLE_QUERY_CACHE=True

BACKTEST_MAX_CONCURRENT_JOBS=2
BACKTEST_MEMORY_LIMIT_GB=8

BACKEND_CORS_ORIGINS=["http://<ALB-DNS-NAME>", "https://<YOUR-DOMAIN>"]

LOG_LEVEL=INFO
LOG_FILE=logs/quant_api.log
EOF

# Frontend .env.local 파일 생성
cat > /home/ubuntu/Stock-Lab-Demo/SL-Front-End/.env.local << EOF
NEXT_PUBLIC_API_BASE_URL=http://<ALB-DNS-NAME>/api/v1
API_BASE_URL=http://backend:8000/api/v1
EOF

chmod +x /home/ubuntu/Stock-Lab-Demo/setup-env.sh
```

#### Docker Compose 프로덕션 파일 생성

`/home/ubuntu/Stock-Lab-Demo/docker-compose.prod.yml` (다음 섹션에서 생성)

#### 서비스 자동 시작 설정

```bash
# Systemd service 파일 생성
sudo nano /etc/systemd/system/stacklab.service
```

파일 내용:
```ini
[Unit]
Description=Stack Lab Demo Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/Stock-Lab-Demo
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable stacklab.service
sudo systemctl start stacklab.service
```

### 2. AMI 생성

설정이 완료된 EC2 인스턴스에서 AMI를 생성합니다.

```
EC2 Console → Instances → 인스턴스 선택 → Actions → Image and templates → Create image

Image name: stacklab-app-ami-v1
Image description: Stack Lab Application with Docker and project setup
Reboot instance: Yes (data consistency)
```

---

## 🚀 Launch Template 생성

AMI가 준비되면 Launch Template을 생성합니다.

**EC2 Console → Launch Templates → Create launch template**

### Launch Template 설정

```
Launch template name: stacklab-launch-template
Template version description: Initial version with app setup

AMI: stacklab-app-ami-v1 (방금 생성한 AMI)
Instance type: t3.medium
Key pair: 기존 키 선택
Network settings:
  - Security groups: sl-ec2-sg

Storage: 30 GiB gp3

Advanced details:
  - IAM instance profile: Create new role with CloudWatch permissions
  - User data: (아래 스크립트 참조)
```

### User Data 스크립트

```bash
#!/bin/bash
set -e

# 로그 파일 설정
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "Starting Stack Lab application deployment..."

# 환경 변수 설정 (필요한 경우 Parameter Store에서 가져오기)
export RDS_ENDPOINT="sl-postgres-db.xxxxxxxxxx.ap-northeast-2.rds.amazonaws.com"
export REDIS_ENDPOINT="sl-redis-cluster.xxxxxx.cache.amazonaws.com"
export ALB_DNS_NAME="<ALB-DNS-NAME>"

# 프로젝트 디렉토리로 이동
cd /home/ubuntu/Stock-Lab-Demo

# 최신 코드 가져오기
sudo -u ubuntu git pull origin main

# 환경 변수 파일 생성
sudo -u ubuntu bash <<'EOF'
cat > /home/ubuntu/Stock-Lab-Demo/SL-Back-end/.env << ENVEOF
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

BACKEND_CORS_ORIGINS=["http://${ALB_DNS_NAME}"]
LOG_LEVEL=INFO
ENVEOF

cat > /home/ubuntu/Stock-Lab-Demo/SL-Front-End/.env.local << ENVEOF
NEXT_PUBLIC_API_BASE_URL=http://${ALB_DNS_NAME}/api/v1
ENVEOF
EOF

# Docker Compose로 애플리케이션 시작
cd /home/ubuntu/Stock-Lab-Demo
sudo -u ubuntu docker-compose -f docker-compose.prod.yml pull
sudo -u ubuntu docker-compose -f docker-compose.prod.yml up -d

# CloudWatch Logs Agent 시작 (선택)
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

echo "Stack Lab application deployment completed!"
```

---

## ⚖️ Application Load Balancer 설정

### 1. Target Groups 생성

#### Backend Target Group

```
Target group name: sl-backend-tg
Target type: Instances
Protocol: HTTP
Port: 8000
VPC: 선택한 VPC

Health checks:
  - Health check protocol: HTTP
  - Health check path: /health
  - Healthy threshold: 2
  - Unhealthy threshold: 3
  - Timeout: 5 seconds
  - Interval: 30 seconds
  - Success codes: 200
```

#### Frontend Target Group

```
Target group name: sl-frontend-tg
Target type: Instances
Protocol: HTTP
Port: 3000
VPC: 선택한 VPC

Health checks:
  - Health check protocol: HTTP
  - Health check path: /
  - Healthy threshold: 2
  - Unhealthy threshold: 3
  - Timeout: 5 seconds
  - Interval: 30 seconds
  - Success codes: 200
```

### 2. Application Load Balancer 생성

**EC2 Console → Load Balancers → Create load balancer → Application Load Balancer**

```
Load balancer name: sl-application-lb
Scheme: Internet-facing
IP address type: IPv4

Network mapping:
  - VPC: 선택한 VPC
  - Availability Zones: 최소 2개 AZ 선택 (서로 다른 AZ의 public subnets)

Security groups: sl-alb-sg

Listeners:
  - Protocol: HTTP, Port: 80, Default action: Forward to sl-frontend-tg
```

### 3. Listener Rules 설정

**ALB → Listeners → HTTP:80 → View/edit rules → Add rules**

#### Rule 1: Backend API
```
IF Path is /api/*
THEN Forward to sl-backend-tg
Priority: 1
```

#### Rule 2: Frontend (Default)
```
Default action: Forward to sl-frontend-tg
```

### 4. HTTPS 설정 (프로덕션 필수)

AWS Certificate Manager에서 SSL 인증서 발급 후:

```
Add listener:
  - Protocol: HTTPS
  - Port: 443
  - Default SSL certificate: ACM 인증서 선택
  - Default action: Forward to sl-frontend-tg

Rules:
  - Path /api/* → Forward to sl-backend-tg
  - Default → Forward to sl-frontend-tg
```

HTTP → HTTPS 리다이렉트:
```
HTTP:80 Listener → Edit → Redirect to HTTPS
```

---

## 📈 Auto Scaling Group 설정

**EC2 Console → Auto Scaling Groups → Create Auto Scaling group**

### 1. 기본 설정

```
Auto Scaling group name: sl-auto-scaling-group
Launch template: stacklab-launch-template (latest version)
```

### 2. 네트워크

```
VPC: 선택한 VPC
Availability Zones and subnets: 최소 2개 AZ의 private subnets 선택
```

### 3. Load Balancing

```
Attach to an existing load balancer
Choose from Application Load Balancer target groups:
  - sl-backend-tg
  - sl-frontend-tg

Health checks:
  - Health check type: ELB
  - Health check grace period: 300 seconds
```

### 4. Group Size

```
Desired capacity: 2
Minimum capacity: 2
Maximum capacity: 4
```

### 5. Scaling Policies

#### Target Tracking Scaling Policy

```
Policy name: sl-cpu-scaling-policy
Metric type: Average CPU utilization
Target value: 70%
Instances need: 300 seconds warm up
```

#### Step Scaling Policy (추가 옵션)

```
Policy name: sl-request-count-scaling
CloudWatch alarm: Create new
  - Metric: ALB RequestCountPerTarget
  - Threshold: > 1000 requests per target

Scaling action:
  - Add 1 instance when threshold breached
  - Wait 60 seconds between scaling activities
```

### 6. Notifications (선택)

```
SNS Topic: Create new or select existing
Events:
  - Instance launch
  - Instance terminate
  - Instance launch error
  - Instance terminate error
```

---

## 🌐 Route 53 DNS 설정

도메인이 있는 경우 Route 53 설정:

```
Hosted zone: yourdomain.com

Record:
  - Record name: app.yourdomain.com (또는 원하는 서브도메인)
  - Record type: A (Alias)
  - Route traffic to: Alias to Application Load Balancer
  - Region: ap-northeast-2
  - Load balancer: sl-application-lb
```

---

## 📊 CloudWatch 모니터링

### 1. CloudWatch Logs

#### Log Groups 생성

```
- /aws/stacklab/backend
- /aws/stacklab/frontend
- /aws/stacklab/system
```

#### CloudWatch Agent 설정

EC2 인스턴스에 `/opt/aws/amazon-cloudwatch-agent/etc/config.json` 생성:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ubuntu/Stock-Lab-Demo/SL-Back-end/logs/*.log",
            "log_group_name": "/aws/stacklab/backend",
            "log_stream_name": "{instance_id}/backend.log"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/stacklab/system",
            "log_stream_name": "{instance_id}/user-data.log"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "StackLabApp",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {"name": "used_percent", "rename": "DISK_USED", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "rename": "MEM_USED", "unit": "Percent"}
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
```

### 2. CloudWatch Alarms

#### CPU 사용률 알람

```
Alarm name: sl-high-cpu-alarm
Metric: EC2 CPUUtilization
Threshold: > 80% for 2 consecutive periods of 5 minutes
Action: SNS notification + Auto Scaling policy
```

#### ALB Unhealthy Target 알람

```
Alarm name: sl-unhealthy-target-alarm
Metric: ALB UnHealthyHostCount
Threshold: >= 1
Action: SNS notification
```

#### RDS Connection 알람

```
Alarm name: sl-rds-connection-alarm
Metric: RDS DatabaseConnections
Threshold: > 80
Action: SNS notification
```

---

## 🎯 추가 권장 AWS 서비스

### 1. **AWS Systems Manager Parameter Store** ⭐⭐⭐

환경 변수를 안전하게 저장하고 관리:

```bash
# 환경 변수 저장
aws ssm put-parameter \
  --name "/stacklab/rds/password" \
  --value "your-secure-password" \
  --type SecureString

# User Data에서 사용
DB_PASSWORD=$(aws ssm get-parameter --name "/stacklab/rds/password" --with-decryption --query 'Parameter.Value' --output text)
```

### 2. **AWS Secrets Manager** ⭐⭐⭐

데이터베이스 자격 증명 및 API 키 관리:
- 자동 로테이션
- RDS와 직접 통합
- 세밀한 권한 제어

### 3. **CloudFront CDN** ⭐⭐

정적 파일 및 프론트엔드 성능 향상:
- 전 세계 엣지 로케이션
- DDoS 보호
- HTTPS 자동 설정

### 4. **S3 + CloudFront** ⭐⭐⭐

프론트엔드를 S3에 호스팅:
```
S3 Bucket: sl-frontend-static
CloudFront Distribution → S3 Origin
Cost: EC2보다 저렴
Performance: 더 빠름
```

### 5. **AWS Backup** ⭐⭐

RDS 및 EBS 자동 백업:
- 중앙화된 백업 관리
- 크로스 리전 백업
- 백업 정책 자동화

### 6. **AWS WAF (Web Application Firewall)** ⭐⭐

ALB 보안 강화:
- SQL Injection 차단
- XSS 공격 방어
- Rate limiting
- IP 화이트리스트/블랙리스트

### 7. **Amazon EventBridge** ⭐

이벤트 기반 아키텍처:
- 백테스팅 작업 스케줄링
- 서버리스 워크플로우

### 8. **AWS Lambda + API Gateway** ⭐

서버리스 마이크로서비스:
- 특정 API만 Lambda로 분리
- 비용 절감
- 무한 확장성

### 9. **Amazon SQS + SNS** ⭐⭐

비동기 작업 처리:
- 백테스팅 작업 큐
- 이메일 알림
- 이벤트 처리

### 10. **AWS CodePipeline + CodeDeploy** ⭐⭐⭐

CI/CD 자동화:
- GitHub 연동
- 자동 배포
- Blue/Green 배포
- 롤백 기능

---

## 💰 비용 최적화

### 예상 월별 비용 (개발 환경)

```
EC2 (t3.medium × 2):        $60
RDS (db.t3.micro):          $25
ElastiCache (cache.t3.micro): $15
ALB:                        $20
Data Transfer:              $10
CloudWatch:                 $5
-----------------------------------
Total:                      ~$135/month
```

### 예상 월별 비용 (프로덕션 환경)

```
EC2 (t3.medium × 2-4):      $60-120
RDS (db.t3.medium, Multi-AZ): $90
ElastiCache (cache.t3.medium): $50
ALB:                        $25
Data Transfer:              $30
CloudWatch + Logs:          $15
S3:                         $5
-----------------------------------
Total:                      ~$275-345/month
```

### 비용 절감 팁

1. **Reserved Instances**: 1년 약정 시 40% 할당
2. **Spot Instances**: 개발/테스트 환경에 활용
3. **Auto Scaling**: 사용량에 따라 자동 조절
4. **S3 Lifecycle Policies**: 오래된 로그 자동 삭제
5. **RDS Storage Autoscaling**: 필요한 만큼만 사용
6. **CloudWatch Logs Retention**: 30일로 제한

---

## 🚀 빠른 시작 체크리스트

- [ ] VPC 및 Subnets 확인
- [ ] Security Groups 생성 (ALB, EC2, RDS, Redis)
- [ ] RDS PostgreSQL 생성 및 엔드포인트 저장
- [ ] ElastiCache Redis 생성 및 엔드포인트 저장
- [ ] EC2 인스턴스 수동 설정 (Docker, 프로젝트 클론)
- [ ] 환경 변수 파일 생성
- [ ] docker-compose.prod.yml 생성
- [ ] 애플리케이션 테스트
- [ ] AMI 생성
- [ ] Launch Template 생성 (User Data 포함)
- [ ] Target Groups 생성 (Backend, Frontend)
- [ ] Application Load Balancer 생성
- [ ] Listener Rules 설정
- [ ] Auto Scaling Group 생성
- [ ] CloudWatch Alarms 설정
- [ ] 도메인 연결 (Route 53)
- [ ] HTTPS 인증서 설정 (ACM)
- [ ] 모니터링 대시보드 설정

---

## 📞 문제 해결

### ALB Health Check 실패

```bash
# EC2 인스턴스에서 직접 테스트
curl http://localhost:8000/health
curl http://localhost:3000

# Security Group 확인
# sl-ec2-sg에 sl-alb-sg로부터의 8000, 3000 포트 허용 확인
```

### RDS 연결 실패

```bash
# EC2에서 RDS 연결 테스트
telnet <RDS-ENDPOINT> 5432

# Security Group 확인
# sl-rds-sg에 sl-ec2-sg로부터의 5432 포트 허용 확인
```

### Auto Scaling이 작동하지 않음

```
- Launch Template이 최신 버전인지 확인
- Target Groups에 인스턴스가 등록되었는지 확인
- Health Check가 통과하는지 확인
- CloudWatch Alarms 상태 확인
```

---

**배포 성공을 기원합니다! 🎉**
