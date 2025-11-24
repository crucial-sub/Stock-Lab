#!/bin/bash

# ============================================
# Stock Lab EC2 Environment Setup Script
# ============================================
# This script helps you set up environment variables
# for EC2 deployment with AWS RDS and ElastiCache
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "============================================"
echo "  Stock Lab EC2 Environment Setup"
echo "============================================"
echo -e "${NC}"

# Function to prompt for input
prompt_input() {
    local prompt_message=$1
    local default_value=$2
    local result

    if [ -n "$default_value" ]; then
        read -p "$prompt_message [$default_value]: " result
        result=${result:-$default_value}
    else
        read -p "$prompt_message: " result
    fi

    echo "$result"
}

# Function to prompt for secret input
prompt_secret() {
    local prompt_message=$1
    local result

    read -s -p "$prompt_message: " result
    echo
    echo "$result"
}

# Function to validate required input
validate_required() {
    local value=$1
    local field_name=$2

    if [ -z "$value" ]; then
        echo -e "${RED}Error: $field_name is required${NC}"
        exit 1
    fi
}

# Check if we're in the project root
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}This script will guide you through setting up environment variables for EC2 deployment.${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to cancel.${NC}\n"

# ============================================
# Gather AWS Resource Information
# ============================================

echo -e "${GREEN}Step 1: AWS RDS Configuration${NC}"
echo "----------------------------------------"

RDS_ENDPOINT=$(prompt_input "Enter RDS endpoint (e.g., xxx.rds.amazonaws.com)")
validate_required "$RDS_ENDPOINT" "RDS endpoint"

RDS_PORT=$(prompt_input "Enter RDS port" "5432")
RDS_USERNAME=$(prompt_input "Enter RDS username" "stocklabadmin")
RDS_PASSWORD=$(prompt_secret "Enter RDS password")
validate_required "$RDS_PASSWORD" "RDS password"

RDS_DATABASE=$(prompt_input "Enter database name" "stock_lab_investment_db")

echo -e "\n${GREEN}Step 2: AWS ElastiCache Configuration${NC}"
echo "----------------------------------------"

REDIS_ENDPOINT=$(prompt_input "Enter ElastiCache Redis endpoint (e.g., xxx.cache.amazonaws.com)")
validate_required "$REDIS_ENDPOINT" "Redis endpoint"

REDIS_PORT=$(prompt_input "Enter Redis port" "6379")
REDIS_PASSWORD=$(prompt_input "Enter Redis password (leave empty if not set)" "")

echo -e "\n${GREEN}Step 3: EC2 Instance Configuration${NC}"
echo "----------------------------------------"

EC2_IP=$(prompt_input "Enter EC2 public IP or domain")
validate_required "$EC2_IP" "EC2 IP/domain"

echo -e "\n${GREEN}Step 4: Security Configuration${NC}"
echo "----------------------------------------"

echo "Generating new SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)
echo -e "Generated: ${GREEN}${SECRET_KEY}${NC}"

echo -e "\n${GREEN}Step 5: External API Keys${NC}"
echo "----------------------------------------"

DART_API_KEY=$(prompt_input "Enter OpenDart API Key (optional)" "")

echo -e "\n${GREEN}Step 6: Application Settings${NC}"
echo "----------------------------------------"

DEBUG_MODE=$(prompt_input "Enable debug mode? (true/false)" "false")
LOG_LEVEL=$(prompt_input "Log level (DEBUG/INFO/WARNING/ERROR)" "INFO")

# ============================================
# Create Backend .env file
# ============================================

echo -e "\n${BLUE}Creating backend .env file...${NC}"

BACKEND_ENV_FILE="SL-Back-end/.env"

cat > "$BACKEND_ENV_FILE" << EOF
# ============================================
# Stock Lab Backend - EC2 Production Config
# ============================================
# Generated on: $(date)
# ============================================

# Deployment Environment
DEPLOYMENT_ENV=ec2

# Database Configuration (AWS RDS)
DATABASE_URL=postgresql+asyncpg://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:${RDS_PORT}/${RDS_DATABASE}
DATABASE_SYNC_URL=postgresql://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:${RDS_PORT}/${RDS_DATABASE}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=False

# Redis Configuration (AWS ElastiCache)
REDIS_URL=redis://${REDIS_ENDPOINT}:${REDIS_PORT}/0
REDIS_HOST=${REDIS_ENDPOINT}
REDIS_PORT=${REDIS_PORT}
REDIS_DB=0
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_CACHE_TTL=3600
CACHE_TTL_SECONDS=3600
CACHE_PREFIX=quant
ENABLE_CACHE=True

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Quant Investment API
VERSION=1.0.0
DEBUG=${DEBUG_MODE}

# Security Configuration
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

# CORS Settings
BACKEND_CORS_ORIGINS=["http://${EC2_IP}:3000","https://${EC2_IP}"]

# External APIs
DART_API_KEY=${DART_API_KEY}

# Logging
LOG_LEVEL=${LOG_LEVEL}
LOG_FILE=logs/quant_api.log
EOF

echo -e "${GREEN}✓ Backend .env file created: ${BACKEND_ENV_FILE}${NC}"

# ============================================
# Create Root .env.production file
# ============================================

echo -e "\n${BLUE}Creating root .env.production file...${NC}"

ROOT_ENV_FILE=".env.production"

cat > "$ROOT_ENV_FILE" << EOF
# ============================================
# Stock Lab - EC2 Production Environment
# ============================================
# Generated on: $(date)
# ============================================

# Database (AWS RDS)
DATABASE_URL=postgresql+asyncpg://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:${RDS_PORT}/${RDS_DATABASE}
DATABASE_SYNC_URL=postgresql://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:${RDS_PORT}/${RDS_DATABASE}

# PostgreSQL credentials
POSTGRES_USER=${RDS_USERNAME}
POSTGRES_PASSWORD=${RDS_PASSWORD}
POSTGRES_DB=${RDS_DATABASE}

# Backend
BACKEND_PORT=8000

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_BASE_URL=http://${EC2_IP}:8000/api/v1
API_BASE_URL=http://backend:8000/api/v1

# Redis
REDIS_PORT=${REDIS_PORT}
EOF

echo -e "${GREEN}✓ Root .env.production file created: ${ROOT_ENV_FILE}${NC}"

# ============================================
# Create summary file
# ============================================

SUMMARY_FILE="deployment-summary.txt"

cat > "$SUMMARY_FILE" << EOF
============================================
Stock Lab EC2 Deployment Configuration
============================================
Generated on: $(date)

AWS Resources:
--------------
RDS Endpoint:     ${RDS_ENDPOINT}:${RDS_PORT}
Database Name:    ${RDS_DATABASE}
Redis Endpoint:   ${REDIS_ENDPOINT}:${REDIS_PORT}
EC2 IP/Domain:    ${EC2_IP}

Application URLs:
-----------------
Frontend:         http://${EC2_IP}:3000
Backend API:      http://${EC2_IP}:8000
API Docs:         http://${EC2_IP}:8000/docs

Configuration:
--------------
Debug Mode:       ${DEBUG_MODE}
Log Level:        ${LOG_LEVEL}
SECRET_KEY:       ${SECRET_KEY}

Next Steps:
-----------
1. Review the generated .env files
2. Deploy to EC2 using: docker-compose -f docker-compose.prod.yml up -d --build
3. Check logs: docker-compose -f docker-compose.prod.yml logs -f
4. Verify health: curl http://localhost:8000/health

Security Notes:
---------------
- Keep .env files secure and never commit to Git
- Ensure EC2 security groups allow access to RDS and ElastiCache
- Update SECRET_KEY periodically
- Rotate RDS credentials regularly

============================================
EOF

echo -e "${GREEN}✓ Deployment summary saved: ${SUMMARY_FILE}${NC}"

# ============================================
# Final Summary
# ============================================

echo -e "\n${BLUE}============================================${NC}"
echo -e "${GREEN}Environment Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}\n"

echo -e "Configuration files created:"
echo -e "  ${GREEN}✓${NC} $BACKEND_ENV_FILE"
echo -e "  ${GREEN}✓${NC} $ROOT_ENV_FILE"
echo -e "  ${GREEN}✓${NC} $SUMMARY_FILE"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "  1. Review the configuration files"
echo "  2. Deploy to EC2:"
echo -e "     ${BLUE}docker-compose -f docker-compose.prod.yml up -d --build${NC}"
echo "  3. Check the logs:"
echo -e "     ${BLUE}docker-compose -f docker-compose.prod.yml logs -f${NC}"
echo "  4. Verify deployment:"
echo -e "     ${BLUE}curl http://localhost:8000/health${NC}"

echo -e "\n${YELLOW}Security Reminders:${NC}"
echo "  - Never commit .env files to Git (already in .gitignore)"
echo "  - Secure your EC2 instance and keep it updated"
echo "  - Review AWS security group settings"
echo "  - Enable CloudWatch monitoring"

echo -e "\n${GREEN}For detailed deployment instructions, see: DEPLOYMENT_GUIDE.md${NC}\n"
