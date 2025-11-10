#!/bin/bash

# SSH Tunnel 상태 확인 스크립트
# Usage: ./scripts/check-tunnel.sh

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOCAL_RDS_PORT=5433

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  SSH Tunnel Status${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# 터널 상태 확인
PID=$(lsof -ti:$LOCAL_RDS_PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo -e "${RED}❌ SSH tunnel is NOT running${NC}"
    echo ""
    echo -e "${YELLOW}Start tunnel:${NC}"
    echo -e "  ${BLUE}./scripts/start-tunnel.sh${NC}"
    exit 1
else
    echo -e "${GREEN}✅ SSH tunnel is running${NC}"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Tunnel Information                    ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC} PID: ${YELLOW}$PID${NC}"
    echo -e "${GREEN}║${NC} Local Port: ${YELLOW}$LOCAL_RDS_PORT${NC}"
    echo -e "${GREEN}║${NC} Status: ${GREEN}ACTIVE${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""

    # 프로세스 정보
    echo -e "${BLUE}Process details:${NC}"
    ps -p $PID -o pid,ppid,user,etime,command
    echo ""

    # 포트 상태
    echo -e "${BLUE}Port status:${NC}"
    lsof -i:$LOCAL_RDS_PORT
    echo ""

    # 연결 테스트 옵션
    if command -v pg_isready &> /dev/null; then
        echo -e "${BLUE}Testing database connection...${NC}"
        if pg_isready -h localhost -p $LOCAL_RDS_PORT -q; then
            echo -e "${GREEN}✅ Database is ready to accept connections${NC}"
        else
            echo -e "${YELLOW}⚠️  Database is not responding${NC}"
            echo -e "${YELLOW}Tunnel is active but RDS might not be accessible${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ️  Install postgresql-client to test database connection:${NC}"
        echo -e "  ${BLUE}brew install postgresql${NC}"
    fi

    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo -e "  Stop tunnel: ${YELLOW}./scripts/stop-tunnel.sh${NC}"
    echo -e "  Test connection: ${YELLOW}psql -h localhost -p $LOCAL_RDS_PORT -U postgres -d quant_investment_db${NC}"
fi
