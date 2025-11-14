#!/bin/bash

# SSH 터널 상태 확인 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOCAL_PORT="5433"

echo -e "${GREEN}=== SSH 터널 상태 확인 ===${NC}"

# 포트 5433을 사용하는 프로세스 확인
PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null || true)

if [ -z "$PID" ]; then
    echo -e "${RED}[STATUS] SSH 터널이 실행되고 있지 않습니다${NC}"
    echo -e "${YELLOW}[TIP] 터널 시작: ./scripts/start-ssh-tunnel.sh${NC}"
    exit 1
else
    echo -e "${GREEN}[STATUS] SSH 터널이 실행 중입니다 (PID: $PID)${NC}"

    # 프로세스 상세 정보
    echo ""
    echo -e "${YELLOW}[INFO] 프로세스 정보:${NC}"
    ps -p $PID -o pid,etime,command | tail -1

    # 포트 정보
    echo ""
    echo -e "${YELLOW}[INFO] 포트 정보:${NC}"
    lsof -i:$LOCAL_PORT -P | grep LISTEN || true

    # 연결 테스트
    echo ""
    echo -e "${YELLOW}[INFO] 데이터베이스 연결 테스트:${NC}"
    if nc -z localhost $LOCAL_PORT 2>/dev/null; then
        echo -e "${GREEN}✓ localhost:$LOCAL_PORT 포트가 열려있습니다${NC}"
    else
        echo -e "${RED}✗ localhost:$LOCAL_PORT 포트 연결 실패${NC}"
    fi
fi
