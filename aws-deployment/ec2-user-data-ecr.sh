#!/bin/bash
#==============================================================================
# EC2 User Data Script for Stock Lab Demo (ECR Version)
# Ubuntu 22.04 LTS
# Uses Docker images from Amazon ECR
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

# AWS 설정
export AWS_REGION="ap-northeast-2"
export AWS_ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID"  # TODO: 실제 계정 ID로 변경
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# 데이터베이스 설정
export RDS_ENDPOINT="sl-postgres-db.c96kksa2ypfb.ap-southeast-2.rds.amazonaws.com"
export RDS_USERNAME="stocklabadmin"
export RDS_PASSWORD="nmmteam05"
export RDS_DATABASE="stock_lab_investment_db"

# Redis 설정
export REDIS_ENDPOINT="master.sl-redis-cluster.rpfsit.apse2.cache.amazonaws.com"
export REDIS_PORT="6379"

# 애플리케이션 설정
export SECRET_KEY="b030a2fbd70ad5a6e27f0b39bec76e4483ac1d6c829aa206ad5f9cbb9a454444"
export ALB_DNS_NAME="SL-APPLICAITION-ALB-2039380111.ap-northeast-2.elb.amazonaws.com"

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
# 5. Docker Compose 설치
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
# 6. ECR 로그인
#==============================================================================

echo "Logging into Amazon ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REGISTRY}

#==============================================================================
# 7. Docker Compose 파일 생성 (ECR 이미지 사용)
#==============================================================================

echo "Creating Docker Compose configuration..."

mkdir -p /home/ubuntu/app
cd /home/ubuntu/app

cat > docker-compose.prod.yml <<'COMPOSE_EOF'
services:
  backend:
    image: ${ECR_REGISTRY}/stocklab-backend:latest
    container_name: sl_backend_prod
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:5432/${RDS_DATABASE}
      - DATABASE_SYNC_URL=postgresql://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:5432/${RDS_DATABASE}
      - DATABASE_POOL_SIZE=20
      - DATABASE_MAX_OVERFLOW=40
      - DATABASE_POOL_TIMEOUT=30
      - DATABASE_POOL_RECYCLE=3600
      - DATABASE_ECHO=False
      - REDIS_URL=redis://${REDIS_ENDPOINT}:${REDIS_PORT}/0
      - REDIS_HOST=${REDIS_ENDPOINT}
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_DB=0
      - REDIS_PASSWORD=
      - REDIS_CACHE_TTL=3600
      - CACHE_TTL_SECONDS=3600
      - CACHE_PREFIX=quant
      - ENABLE_CACHE=False
      - API_V1_PREFIX=/api/v1
      - PROJECT_NAME=Quant Investment API
      - VERSION=1.0.0
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - CHUNK_SIZE=10000
      - MAX_WORKERS=4
      - ENABLE_QUERY_CACHE=True
      - BACKTEST_MAX_CONCURRENT_JOBS=2
      - BACKTEST_MEMORY_LIMIT_GB=8
      - BACKEND_CORS_ORIGINS=["http://${ALB_DNS_NAME}","https://${ALB_DNS_NAME}","http://localhost:3000"]
      - LOG_LEVEL=INFO
      - LOG_FILE=logs/quant_api.log
    ports:
      - "8000:8000"
    volumes:
      - /home/ubuntu/app/logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - app_network

  frontend:
    image: ${ECR_REGISTRY}/stocklab-frontend:latest
    container_name: sl_frontend_prod
    restart: always
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://${ALB_DNS_NAME}/api/v1
      - NODE_ENV=production
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
COMPOSE_EOF

# 환경 변수 치환
envsubst < docker-compose.prod.yml > docker-compose.prod.yml.tmp
mv docker-compose.prod.yml.tmp docker-compose.prod.yml

#==============================================================================
# 8. 로그 디렉토리 생성
#==============================================================================

echo "Creating log directories..."
mkdir -p /home/ubuntu/app/logs
chown -R ubuntu:ubuntu /home/ubuntu/app
chmod -R 755 /home/ubuntu/app/logs

#==============================================================================
# 9. Docker 이미지 Pull 및 실행
#==============================================================================

echo "Pulling latest Docker images from ECR..."
sudo -u ubuntu docker pull ${ECR_REGISTRY}/stocklab-backend:latest
sudo -u ubuntu docker pull ${ECR_REGISTRY}/stocklab-frontend:latest

echo "Starting Docker containers..."
cd /home/ubuntu/app

# 기존 컨테이너 정리
sudo -u ubuntu docker-compose -f docker-compose.prod.yml down || true

# 새 컨테이너 시작
sudo -u ubuntu docker-compose -f docker-compose.prod.yml up -d

# 컨테이너 상태 확인
sleep 10
sudo -u ubuntu docker-compose -f docker-compose.prod.yml ps

#==============================================================================
# 10. Health Check
#==============================================================================

echo "Performing health checks..."

# Backend health check
for i in {1..30}; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo "✓ Backend is healthy!"
        break
    fi
    echo "Waiting for backend... ($i/30)"
    sleep 5
done

# Frontend health check
for i in {1..30}; do
    if curl -f http://localhost:3000 &>/dev/null; then
        echo "✓ Frontend is healthy!"
        break
    fi
    echo "Waiting for frontend... ($i/30)"
    sleep 5
done

#==============================================================================
# 11. Systemd Service 설정 (자동 시작)
#==============================================================================

echo "Setting up systemd service..."

cat > /etc/systemd/system/stocklab.service <<'SYSTEMD_SERVICE'
[Unit]
Description=Stack Lab Demo Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/app
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
systemctl enable stocklab.service

#==============================================================================
# 12. 정리 및 완료
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
cd /home/ubuntu/app
sudo -u ubuntu docker-compose -f docker-compose.prod.yml ps

echo "Disk usage:"
df -h | head -5

echo "Memory usage:"
free -h

exit 0
