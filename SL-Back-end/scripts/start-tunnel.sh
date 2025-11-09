#!/bin/bash

# SSH Tunnel 시작 스크립트
# Usage: ./scripts/start-tunnel.sh

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정 (실제 값으로 변경 필요)
SSH_KEY="/Users/a2/Desktop/Keys/Stock-Lab-Dev.pem"
EC2_HOST="ec2-13-209-198-242.ap-northeast-2.compute.amazonaws.com"
EC2_USER="luca"
RDS_ENDPOINT="sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com"
LOCAL_RDS_PORT=5433
REMOTE_RDS_PORT=5432

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  SSH Tunnel Setup for Stock Lab RDS${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# SSH 키 파일 확인
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ SSH key not found: $SSH_KEY${NC}"
    echo -e "${YELLOW}Please update SSH_KEY path in this script${NC}"
    exit 1
fi

# SSH 키 권한 확인
KEY_PERMS=$(stat -f "%OLp" "$SSH_KEY" 2>/dev/null || stat -c "%a" "$SSH_KEY" 2>/dev/null)
if [ "$KEY_PERMS" != "400" ] && [ "$KEY_PERMS" != "600" ]; then
    echo -e "${YELLOW}⚠️  Fixing SSH key permissions...${NC}"
    chmod 400 "$SSH_KEY"
    echo -e "${GREEN}✅ SSH key permissions set to 400${NC}"
fi

# 기존 터널 확인
if lsof -ti:$LOCAL_RDS_PORT > /dev/null 2>&1; then
    PID=$(lsof -ti:$LOCAL_RDS_PORT)
    echo -e "${RED}❌ Port $LOCAL_RDS_PORT is already in use (PID: $PID)${NC}"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  1. Stop existing tunnel: ./scripts/stop-tunnel.sh"
    echo "  2. Check tunnel status: ./scripts/check-tunnel.sh"
    exit 1
fi

# EC2 연결 테스트
echo -e "${BLUE}🔍 Testing EC2 connection...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" exit 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to EC2 instance${NC}"
    echo -e "${YELLOW}Please check:${NC}"
    echo "  - EC2 instance is running"
    echo "  - Security group allows SSH (port 22)"
    echo "  - EC2_HOST is correct: $EC2_HOST"
    exit 1
fi
echo -e "${GREEN}✅ EC2 connection successful${NC}"
echo ""

# SSH 터널 시작
echo -e "${BLUE}🚀 Starting SSH tunnel to RDS...${NC}"
ssh -f -N -i "$SSH_KEY" \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -L $LOCAL_RDS_PORT:$RDS_ENDPOINT:$REMOTE_RDS_PORT \
    "$EC2_USER@$EC2_HOST"

# 터널 확인
sleep 2
if lsof -ti:$LOCAL_RDS_PORT > /dev/null 2>&1; then
    PID=$(lsof -ti:$LOCAL_RDS_PORT)
    echo -e "${GREEN}✅ SSH tunnel established successfully!${NC}"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Tunnel Information                    ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC} PID: ${YELLOW}$PID${NC}"
    echo -e "${GREEN}║${NC} Local Port: ${YELLOW}$LOCAL_RDS_PORT${NC}"
    echo -e "${GREEN}║${NC} RDS Endpoint: ${YELLOW}$RDS_ENDPOINT${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 RDS accessible at: ${YELLOW}localhost:$LOCAL_RDS_PORT${NC}"
    echo ""
    echo -e "${BLUE}Test connection:${NC}"
    echo -e "  ${YELLOW}psql -h localhost -p $LOCAL_RDS_PORT -U postgres -d quant_investment_db${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Switch environment: ${YELLOW}./scripts/switch-env.sh tunnel${NC}"
    echo "  2. Start backend: ${YELLOW}uvicorn app.main:app --reload${NC}"
    echo "  3. Stop tunnel when done: ${YELLOW}./scripts/stop-tunnel.sh${NC}"
else
    echo -e "${RED}❌ Failed to establish SSH tunnel${NC}"
    echo -e "${YELLOW}Check the error messages above${NC}"
    exit 1
fi
