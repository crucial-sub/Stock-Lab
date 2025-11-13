#!/bin/bash

# SSH Tunnel 중지 스크립트
# Usage: ./scripts/stop-tunnel.sh

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOCAL_RDS_PORT=5433

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Stop SSH Tunnel${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# 터널 프로세스 찾기
PID=$(lsof -ti:$LOCAL_RDS_PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo -e "${YELLOW}ℹ️  No tunnel found on port $LOCAL_RDS_PORT${NC}"
    echo ""
    echo -e "${GREEN}✅ Already stopped${NC}"
    exit 0
fi

# 프로세스 정보 출력
echo -e "${BLUE}Found tunnel process:${NC}"
ps -p $PID -o pid,ppid,user,command | head -2
echo ""

# 프로세스 종료
echo -e "${BLUE}🛑 Stopping SSH tunnel (PID: ${YELLOW}$PID${NC}${BLUE})...${NC}"
kill $PID

# 종료 확인
sleep 1
if lsof -ti:$LOCAL_RDS_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Failed to stop tunnel gracefully, force killing...${NC}"
    kill -9 $PID
    sleep 1
fi

# 최종 확인
if lsof -ti:$LOCAL_RDS_PORT > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to stop tunnel${NC}"
    echo -e "${YELLOW}Try manually: kill -9 $PID${NC}"
    exit 1
else
    echo -e "${GREEN}✅ SSH tunnel stopped successfully${NC}"
    echo ""
    echo -e "${BLUE}Port ${YELLOW}$LOCAL_RDS_PORT${NC}${BLUE} is now free${NC}"
fi
