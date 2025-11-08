#!/bin/bash
#==============================================================================
# EC2 User Data Script for Stack Lab Demo
# Ubuntu 22.04 LTS
#==============================================================================

set -e

# 로그 파일 설정
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "========================================"
echo "Stack Lab Application Deployment Start"
echo "Time: $(date)"
echo "========================================"

#==============================================================================
# 1. 환경 변수 설정
#==============================================================================

# TODO: Launch Template 생성 시 아래 값들을 실제 값으로 변경하세요
export RDS_ENDPOINT="YOUR_RDS_ENDPOINT.rds.amazonaws.com"
export RDS_PASSWORD="YOUR_RDS_PASSWORD"
export REDIS_ENDPOINT="YOUR_REDIS_PRIMARY_ENDPOINT.cache.amazonaws.com"  # 기본(Primary) 엔드포인트 사용

# SECRET_KEY: 모든 인스턴스에서 동일한 값을 사용해야 합니다
# 로컬에서 'openssl rand -hex 32' 명령어로 생성한 후 아래에 붙여넣으세요
export SECRET_KEY="GENERATE_WITH_openssl_rand_hex_32_AND_PASTE_HERE"

# ALB DNS는 ALB 생성 후 업데이트하거나 Parameter Store 사용
export ALB_DNS_NAME="PLACEHOLDER_UPDATE_AFTER_ALB_CREATION"

# AWS 리전
export AWS_REGION="ap-northeast-2"

#==============================================================================
# 2. 시스템 업데이트
#==============================================================================

echo "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

#==============================================================================
# 3. 필수 패키지 설치
#==============================================================================

echo "Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    jq \
    awscli

#==============================================================================
# 4. Docker 설치 (이미 AMI에 포함되어 있다면 스킵)
#==============================================================================

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker ubuntu
    rm get-docker.sh
else
    echo "Docker already installed"
fi

#==============================================================================
# 5. Docker Compose 설치 (이미 AMI에 포함되어 있다면 스킵)
#==============================================================================

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

#==============================================================================
# 6. CloudWatch Logs Agent 설치 및 설정
#==============================================================================

echo "Installing CloudWatch Agent..."
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb

# CloudWatch Agent 설정
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<'CWCONFIG'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ubuntu/Stock-Lab-Demo/SL-Back-end/logs/*.log",
            "log_group_name": "/aws/stacklab/backend",
            "log_stream_name": "{instance_id}/backend.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/stacklab/system",
            "log_stream_name": "{instance_id}/user-data.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "/aws/stacklab/system",
            "log_stream_name": "{instance_id}/syslog",
            "timezone": "UTC"
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
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          },
          {
            "name": "cpu_usage_iowait",
            "rename": "CPU_IOWAIT",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "netstat": {
        "measurement": [
          {
            "name": "tcp_established",
            "rename": "TCP_ESTABLISHED",
            "unit": "Count"
          }
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
CWCONFIG

#==============================================================================
# 7. 프로젝트 클론 또는 업데이트
#==============================================================================

PROJECT_DIR="/home/ubuntu/Stock-Lab-Demo"

if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory exists, pulling latest changes..."
    cd "$PROJECT_DIR"
    sudo -u ubuntu git pull origin main || {
        echo "Git pull failed, trying to reset..."
        sudo -u ubuntu git fetch origin
        sudo -u ubuntu git reset --hard origin/main
    }
else
    echo "Cloning project repository..."
    sudo -u ubuntu git clone https://github.com/Krafton-Jungle-10-Final-Project/Stock-Lab-Demo.git "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

#==============================================================================
# 8. 환경 변수 파일 생성
#==============================================================================

echo "Creating environment files..."

# Backend .env
sudo -u ubuntu cat > "$PROJECT_DIR/SL-Back-end/.env" <<BACKEND_ENV
# Database Configuration (AWS RDS)
DATABASE_URL=postgresql+asyncpg://postgres:${RDS_PASSWORD}@${RDS_ENDPOINT}:5432/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:${RDS_PASSWORD}@${RDS_ENDPOINT}:5432/quant_investment_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

# Redis Configuration (AWS ElastiCache)
REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
REDIS_HOST=${REDIS_ENDPOINT}
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600
CACHE_TTL_SECONDS=3600
CACHE_PREFIX=quant
ENABLE_CACHE=True

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API
VERSION=1.0.0
DEBUG=False

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Performance
CHUNK_SIZE=10000
MAX_WORKERS=4
ENABLE_QUERY_CACHE=True

# Backtesting
BACKTEST_MAX_CONCURRENT_JOBS=2
BACKTEST_MEMORY_LIMIT_GB=8

# CORS Settings
BACKEND_CORS_ORIGINS=["http://${ALB_DNS_NAME}","https://${ALB_DNS_NAME}"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quant_api.log
BACKEND_ENV

# Frontend .env.local
sudo -u ubuntu cat > "$PROJECT_DIR/SL-Front-End/.env.local" <<FRONTEND_ENV
NEXT_PUBLIC_API_BASE_URL=http://${ALB_DNS_NAME}/api/v1
API_BASE_URL=http://backend:8000/api/v1
FRONTEND_ENV

# 루트 .env (docker-compose.prod.yml 용)
sudo -u ubuntu cat > "$PROJECT_DIR/.env" <<ROOT_ENV
NEXT_PUBLIC_API_BASE_URL=http://${ALB_DNS_NAME}/api/v1
ROOT_ENV

#==============================================================================
# 9. 로그 디렉토리 생성
#==============================================================================

echo "Creating log directories..."
mkdir -p "$PROJECT_DIR/SL-Back-end/logs"
chown -R ubuntu:ubuntu "$PROJECT_DIR/SL-Back-end/logs"
chmod -R 755 "$PROJECT_DIR/SL-Back-end/logs"

#==============================================================================
# 10. Docker 이미지 빌드 및 실행
#==============================================================================

echo "Starting Docker containers..."

cd "$PROJECT_DIR"

# 기존 컨테이너 정리
sudo -u ubuntu docker-compose -f docker-compose.prod.yml down || true

# 새 이미지 빌드 및 시작
sudo -u ubuntu docker-compose -f docker-compose.prod.yml build --no-cache
sudo -u ubuntu docker-compose -f docker-compose.prod.yml up -d

# 컨테이너 상태 확인
sleep 10
sudo -u ubuntu docker-compose -f docker-compose.prod.yml ps

#==============================================================================
# 11. CloudWatch Agent 시작
#==============================================================================

echo "Starting CloudWatch Agent..."
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

#==============================================================================
# 12. Health Check
#==============================================================================

echo "Performing health checks..."

# Backend health check
for i in {1..30}; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo "Backend is healthy!"
        break
    fi
    echo "Waiting for backend... ($i/30)"
    sleep 5
done

# Frontend health check
for i in {1..30}; do
    if curl -f http://localhost:3000 &>/dev/null; then
        echo "Frontend is healthy!"
        break
    fi
    echo "Waiting for frontend... ($i/30)"
    sleep 5
done

#==============================================================================
# 13. Systemd Service 설정 (자동 시작)
#==============================================================================

echo "Setting up systemd service..."

cat > /etc/systemd/system/stacklab.service <<'SYSTEMD_SERVICE'
[Unit]
Description=Stack Lab Demo Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/Stock-Lab-Demo
ExecStartPre=/usr/bin/docker-compose -f docker-compose.prod.yml pull
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu
Group=ubuntu
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
SYSTEMD_SERVICE

# Systemd 재로드 및 서비스 활성화
systemctl daemon-reload
systemctl enable stacklab.service

#==============================================================================
# 14. 정리 및 완료
#==============================================================================

echo "Cleaning up..."
apt-get autoremove -y
apt-get autoclean -y

echo "========================================"
echo "Stack Lab Application Deployment Complete!"
echo "Time: $(date)"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "========================================"

# 최종 상태 출력
echo "Docker containers status:"
cd "$PROJECT_DIR"
sudo -u ubuntu docker-compose -f docker-compose.prod.yml ps

echo "Disk usage:"
df -h

echo "Memory usage:"
free -h

exit 0
