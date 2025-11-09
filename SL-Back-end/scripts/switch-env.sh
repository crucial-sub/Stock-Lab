#!/bin/bash

# 환경 변수 전환 스크립트
# Usage: ./scripts/switch-env.sh [local|tunnel|production]

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ENV_MODE=$1

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Environment Switcher${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

if [ -z "$ENV_MODE" ]; then
    echo -e "${RED}❌ Error: Environment mode not specified${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  ${BLUE}./scripts/switch-env.sh [local|tunnel|production]${NC}"
    echo ""
    echo -e "${YELLOW}Available modes:${NC}"
    echo -e "  ${GREEN}local${NC}      - Use local Docker PostgreSQL (localhost:5432)"
    echo -e "  ${GREEN}tunnel${NC}     - Use RDS via SSH tunnel (localhost:5433)"
    echo -e "  ${GREEN}production${NC} - Use production RDS directly"
    exit 1
fi

# 현재 디렉토리 확인
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found in current directory${NC}"
    echo -e "${YELLOW}Make sure you're in SL-Back-end directory${NC}"
    exit 1
fi

# 백업 생성
if [ -f ".env" ]; then
    cp .env .env.backup
    echo -e "${BLUE}📦 Current .env backed up to .env.backup${NC}"
fi

case $ENV_MODE in
    local)
        echo -e "${BLUE}Switching to ${GREEN}LOCAL${NC}${BLUE} environment...${NC}"

        if [ ! -f ".env.local" ]; then
            echo -e "${YELLOW}⚠️  .env.local not found, creating from current .env${NC}"
            cp .env .env.local
        fi

        cp .env.local .env
        echo ""
        echo -e "${GREEN}✅ Switched to LOCAL environment${NC}"
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  Local Environment Active              ║${NC}"
        echo -e "${GREEN}╠════════════════════════════════════════╣${NC}"
        echo -e "${GREEN}║${NC} Database: ${YELLOW}localhost:5432${NC}"
        echo -e "${GREEN}║${NC} Type: ${YELLOW}Docker PostgreSQL${NC}"
        echo -e "${GREEN}║${NC} Redis: ${YELLOW}localhost:6379${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}Make sure Docker containers are running:${NC}"
        echo -e "  ${YELLOW}docker-compose up -d${NC}"
        ;;

    tunnel)
        echo -e "${BLUE}Switching to ${GREEN}TUNNEL${NC}${BLUE} environment...${NC}"

        if [ ! -f ".env.tunnel" ]; then
            echo -e "${YELLOW}⚠️  .env.tunnel not found, creating template...${NC}"
            cat > .env.tunnel << 'EOF'
# Database Configuration (SSH Tunnel through EC2 to RDS)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_RDS_PASSWORD@localhost:5433/quant_investment_db
DATABASE_SYNC_URL=postgresql://postgres:YOUR_RDS_PASSWORD@localhost:5433/quant_investment_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
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
EOF
            echo -e "${GREEN}✅ Created .env.tunnel template${NC}"
            echo -e "${YELLOW}⚠️  Please update YOUR_RDS_PASSWORD in .env.tunnel${NC}"
        fi

        cp .env.tunnel .env
        echo ""
        echo -e "${GREEN}✅ Switched to TUNNEL environment${NC}"
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  Tunnel Environment Active             ║${NC}"
        echo -e "${GREEN}╠════════════════════════════════════════╣${NC}"
        echo -e "${GREEN}║${NC} Database: ${YELLOW}localhost:5433${NC}"
        echo -e "${GREEN}║${NC} Type: ${YELLOW}RDS via SSH Tunnel${NC}"
        echo -e "${GREEN}║${NC} Redis: ${YELLOW}localhost:6379${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}Make sure SSH tunnel is running:${NC}"
        echo -e "  ${YELLOW}./scripts/check-tunnel.sh${NC}"
        echo -e "  ${YELLOW}./scripts/start-tunnel.sh${NC} (if not running)"
        ;;

    production)
        echo -e "${BLUE}Switching to ${GREEN}PRODUCTION${NC}${BLUE} environment...${NC}"

        if [ ! -f ".env.production" ]; then
            echo -e "${RED}❌ .env.production not found${NC}"
            echo -e "${YELLOW}This file should contain production RDS credentials${NC}"
            exit 1
        fi

        cp .env.production .env
        echo ""
        echo -e "${GREEN}✅ Switched to PRODUCTION environment${NC}"
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  Production Environment Active         ║${NC}"
        echo -e "${GREEN}╠════════════════════════════════════════╣${NC}"
        echo -e "${GREEN}║${NC} Database: ${YELLOW}Direct RDS Connection${NC}"
        echo -e "${GREEN}║${NC} Type: ${YELLOW}Production RDS${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${RED}⚠️  WARNING: You are now connected to PRODUCTION database${NC}"
        echo -e "${YELLOW}Be careful with data modifications!${NC}"
        ;;

    *)
        echo -e "${RED}❌ Invalid mode: $ENV_MODE${NC}"
        echo ""
        echo -e "${YELLOW}Available modes:${NC}"
        echo -e "  ${GREEN}local${NC}      - Local Docker PostgreSQL"
        echo -e "  ${GREEN}tunnel${NC}     - RDS via SSH tunnel"
        echo -e "  ${GREEN}production${NC} - Production RDS"
        exit 1
        ;;
esac

# 현재 설정 확인
echo ""
echo -e "${BLUE}Current database configuration:${NC}"
grep "^DATABASE_URL=" .env | sed 's/DATABASE_URL=/  /'
echo ""
