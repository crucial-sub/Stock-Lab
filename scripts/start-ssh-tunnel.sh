#!/bin/bash

# SSH 터널 자동 시작 스크립트
# AWS RDS에 SSH 터널을 통해 로컬 5433 포트로 연결

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정
SSH_KEY="/Users/a2/Desktop/Keys/Stock-Lab-Dev.pem"
BASTION_HOST="52.79.38.80"
BASTION_USER="ubuntu"
RDS_ENDPOINT="sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com"
RDS_PORT="5432"
LOCAL_PORT="5433"

echo -e "${GREEN}=== SSH 터널 시작 ===${NC}"

# 1. SSH 키 파일 존재 확인
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}[ERROR] SSH 키 파일을 찾을 수 없습니다: $SSH_KEY${NC}"
    exit 1
fi

# 2. SSH 키 파일 권한 확인 및 수정
KEY_PERMISSIONS=$(stat -f "%OLp" "$SSH_KEY")
if [ "$KEY_PERMISSIONS" != "400" ] && [ "$KEY_PERMISSIONS" != "600" ]; then
    echo -e "${YELLOW}[INFO] SSH 키 파일 권한 수정 중...${NC}"
    chmod 400 "$SSH_KEY"
fi

# 3. 기존 터널 프로세스 확인
EXISTING_PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null || true)
if [ ! -z "$EXISTING_PID" ]; then
    echo -e "${YELLOW}[INFO] 기존 SSH 터널이 실행 중입니다 (PID: $EXISTING_PID)${NC}"
    echo -e "${YELLOW}[INFO] 기존 터널을 종료합니다...${NC}"
    kill -9 $EXISTING_PID 2>/dev/null || true
    sleep 2
fi

# 4. SSH 터널 시작
echo -e "${GREEN}[INFO] SSH 터널 연결 중...${NC}"
echo -e "  Bastion: ${BASTION_USER}@${BASTION_HOST}"
echo -e "  RDS: ${RDS_ENDPOINT}:${RDS_PORT}"
echo -e "  Local: localhost:${LOCAL_PORT}"

ssh -i "$SSH_KEY" \
    -L ${LOCAL_PORT}:${RDS_ENDPOINT}:${RDS_PORT} \
    -N -f \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    ${BASTION_USER}@${BASTION_HOST}

# 5. 연결 확인
sleep 2
NEW_PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null || true)
if [ ! -z "$NEW_PID" ]; then
    echo -e "${GREEN}[SUCCESS] SSH 터널이 성공적으로 시작되었습니다! (PID: $NEW_PID)${NC}"
    echo -e "${GREEN}[INFO] localhost:${LOCAL_PORT} → ${RDS_ENDPOINT}:${RDS_PORT}${NC}"
    echo ""
    echo -e "${YELLOW}[TIP] 터널 종료: kill -9 $NEW_PID${NC}"
    echo -e "${YELLOW}[TIP] 또는: ./scripts/stop-ssh-tunnel.sh${NC}"
else
    echo -e "${RED}[ERROR] SSH 터널 시작에 실패했습니다${NC}"
    exit 1
fi
