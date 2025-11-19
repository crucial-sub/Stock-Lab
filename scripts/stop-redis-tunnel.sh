#!/bin/bash

# Redis SSH 터널 종료 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOCAL_PORT="6379"

echo -e "${GREEN}=== Redis SSH 터널 종료 ===${NC}"

# 포트를 사용 중인 프로세스 찾기
PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null || true)

if [ -z "$PID" ]; then
    echo -e "${YELLOW}[INFO] 실행 중인 Redis 터널이 없습니다${NC}"
    exit 0
fi

echo -e "${YELLOW}[INFO] Redis 터널 프로세스 종료 중... (PID: $PID)${NC}"
kill -9 $PID 2>/dev/null || true
sleep 1

# 종료 확인
if [ -z "$(lsof -ti:$LOCAL_PORT 2>/dev/null || true)" ]; then
    echo -e "${GREEN}[SUCCESS] Redis SSH 터널이 종료되었습니다${NC}"
else
    echo -e "${RED}[ERROR] 터널 종료에 실패했습니다${NC}"
    exit 1
fi
