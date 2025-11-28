#!/bin/bash
# EC2 환경변수 파일 자동 생성 스크립트

set -e

echo "=========================================="
echo "EC2 Production Environment Setup"
echo "=========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 루트 .env.production 파일 생성
echo -e "${GREEN}Creating .env.production...${NC}"
cat > .env.production << 'EOF'
# EC2 Production Environment Variables

# Database (AWS RDS)
DATABASE_URL=postgresql+asyncpg://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db
DATABASE_SYNC_URL=postgresql://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db

# PostgreSQL 컨테이너는 EC2에서 사용하지 않음 (RDS 사용)
POSTGRES_USER=stocklabadmin
POSTGRES_PASSWORD=nmmteam05
POSTGRES_DB=stock_lab_investment_db

# Backend
BACKEND_PORT=8000

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_BASE_URL=http://43.203.206.70:8000/api/v1
API_BASE_URL=http://backend:8000/api/v1

# Redis (AWS ElastiCache)
REDIS_URL=redis://clustercfg.sl-redis-cl.lvbc9o.apn2.cache.amazonaws.com:6379/0
REDIS_HOST=clustercfg.sl-redis-cl.lvbc9o.apn2.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SSL=False

# Chatbot
CHATBOT_PORT=8003
NEXT_PUBLIC_CHATBOT_API_URL=http://43.203.206.70:8003

# AWS Credentials (for Chatbot) - FILL THESE IN!
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY_HERE
AWS_REGION=ap-northeast-2
AWS_KB_ID=YOUR_KB_ID_HERE
RETRIEVER_TYPE=aws_kb
EOF

echo -e "${GREEN}✓ .env.production created${NC}"
echo ""

# Backend .env.production 파일 생성
echo -e "${GREEN}Creating SL-Back-end/.env.production...${NC}"

# SECRET_KEY 생성
SECRET_KEY=$(openssl rand -hex 32)
echo -e "${YELLOW}Generated SECRET_KEY: ${SECRET_KEY}${NC}"

cat > SL-Back-end/.env.production << EOF
# EC2 Production Environment - Backend Configuration
# ==============================================

# Database Configuration (AWS RDS - Direct Connection)
DATABASE_URL=postgresql+asyncpg://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db
DATABASE_SYNC_URL=postgresql://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db
DATABASE_POOL_SIZE=40
DATABASE_MAX_OVERFLOW=50
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

# Redis Configuration (AWS ElastiCache - Direct Connection)
REDIS_URL=redis://clustercfg.sl-redis-cl.lvbc9o.apn2.cache.amazonaws.com:6379/0
REDIS_HOST=clustercfg.sl-redis-cl.lvbc9o.apn2.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_TTL=3600
CACHE_TTL_SECONDS=3600
CACHE_PREFIX=quant
ENABLE_CACHE=True
ENABLE_CACHE_WARMING=True
REDIS_SSL=False

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API
VERSION=1.0.0
DEBUG=False

# Security (AUTO-GENERATED)
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Performance Settings
CHUNK_SIZE=10000
MAX_WORKERS=4
ENABLE_QUERY_CACHE=True

# Backtesting Configuration
BACKTEST_MAX_CONCURRENT_JOBS=2
BACKTEST_MEMORY_LIMIT_GB=8
USE_MULTIPROCESSING=true

# CORS Settings
BACKEND_CORS_ORIGINS=["http://43.203.206.70:3000", "http://43.203.206.70:8000"]

# Deployment Environment
DEPLOYMENT_ENV=ec2

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quant_api.log

# External APIs
DART_API_KEY=
EOF

echo -e "${GREEN}✓ SL-Back-end/.env.production created${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}Environment files created successfully!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Please edit .env.production and fill in:${NC}"
echo "  - AWS_ACCESS_KEY_ID"
echo "  - AWS_SECRET_ACCESS_KEY"
echo "  - AWS_KB_ID"
echo ""
echo "Then run: make ec2-build"
echo ""
