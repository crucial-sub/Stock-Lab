#!/bin/bash
# EC2 Launch Template User Data Script
# 이 스크립트는 EC2 인스턴스 시작 시 자동으로 실행됩니다.

set -e

# 로그 파일 설정
LOGFILE=/var/log/user-data.log
exec > >(tee -a $LOGFILE)
exec 2>&1

echo "=== EC2 User Data Script Started at $(date) ==="

# 환경 설정
export AWS_REGION=ap-northeast-2
export ENVIRONMENT=prod
export APP_DIR=/opt/stocklab
export ECR_REGISTRY="YOUR_ECR_REGISTRY_ID.dkr.ecr.ap-northeast-2.amazonaws.com"

# 필수 패키지 설치
echo "Installing required packages..."
yum update -y
yum install -y docker jq aws-cli

# Docker 서비스 시작
echo "Starting Docker service..."
service docker start
usermod -a -G docker ec2-user

# Docker Compose 설치
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 앱 디렉토리 생성
mkdir -p $APP_DIR
cd $APP_DIR

# ECR 로그인
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

# Parameter Store에서 환경 변수 가져오기
echo "Fetching environment variables from Parameter Store..."

# 환경 변수 파일 생성
cat > $APP_DIR/.env << EOF
# Database Configuration
DATABASE_URL=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/DATABASE_URL" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
DATABASE_SYNC_URL=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/DATABASE_SYNC_URL" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

# Redis Configuration
REDIS_URL=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/REDIS_URL" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
REDIS_HOST=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/REDIS_HOST" --query "Parameter.Value" --output text --region $AWS_REGION)
REDIS_PORT=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/REDIS_PORT" --query "Parameter.Value" --output text --region $AWS_REGION)
REDIS_DB=0
REDIS_CACHE_TTL=3600
CACHE_TTL_SECONDS=3600
CACHE_PREFIX=quant
ENABLE_CACHE=True

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API
VERSION=1.0.0
DEBUG=False

# Security Configuration
SECRET_KEY=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/SECRET_KEY" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
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
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://your-production-domain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quant_api.log

# Frontend Configuration
NEXT_PUBLIC_API_BASE_URL=$(aws ssm get-parameter --name "/stocklab/${ENVIRONMENT}/ALB_DNS_URL" --query "Parameter.Value" --output text --region $AWS_REGION)/api/v1
EOF

# docker-compose.yml 생성
cat > $APP_DIR/docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: ${ECR_REGISTRY}/stocklab-backend:latest
    container_name: stocklab-backend
    env_file:
      - .env
    ports:
      - "8000:8000"
    restart: unless-stopped
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

  frontend:
    image: ${ECR_REGISTRY}/stocklab-frontend:latest
    container_name: stocklab-frontend
    env_file:
      - .env
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# ECR_REGISTRY 환경 변수를 docker-compose.yml에서 사용하기 위해 export
export ECR_REGISTRY

# 최신 Docker 이미지 pull
echo "Pulling latest Docker images..."
docker pull $ECR_REGISTRY/stocklab-backend:latest
docker pull $ECR_REGISTRY/stocklab-frontend:latest

# 기존 컨테이너 정리
echo "Cleaning up old containers..."
docker-compose down || true

# 새 컨테이너 시작
echo "Starting Docker containers..."
docker-compose up -d

# 컨테이너 상태 확인
echo "Checking container status..."
sleep 10
docker-compose ps

# Health check
echo "Waiting for services to be healthy..."
for i in {1..30}; do
    BACKEND_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' stocklab-backend 2>/dev/null || echo "starting")
    FRONTEND_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' stocklab-frontend 2>/dev/null || echo "starting")

    echo "Backend: $BACKEND_HEALTH, Frontend: $FRONTEND_HEALTH"

    if [ "$BACKEND_HEALTH" = "healthy" ] && [ "$FRONTEND_HEALTH" = "healthy" ]; then
        echo "All services are healthy!"
        break
    fi

    sleep 10
done

# CloudWatch Logs Agent 설치 (선택사항)
# yum install -y amazon-cloudwatch-agent

echo "=== EC2 User Data Script Completed at $(date) ==="
echo "Application is running at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
