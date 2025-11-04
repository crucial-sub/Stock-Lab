#!/bin/bash

# SL Quant Investment Platform 종료 스크립트

echo "🛑 SL Quant Investment Platform 종료 중..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend 종료
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo -e "${GREEN}✅ Backend 서버 종료됨 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend 서버가 이미 종료됨${NC}"
    fi
    rm .backend.pid
else
    # PID 파일이 없으면 포트로 찾기
    BACKEND_PID=$(lsof -ti:8000)
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID
        echo -e "${GREEN}✅ Backend 서버 종료됨 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend 서버를 찾을 수 없음${NC}"
    fi
fi

# Frontend 종료
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ Frontend 서버 종료됨 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend 서버가 이미 종료됨${NC}"
    fi
    rm .frontend.pid
else
    # PID 파일이 없으면 포트로 찾기
    FRONTEND_PID=$(lsof -ti:3000)
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ Frontend 서버 종료됨 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend 서버를 찾을 수 없음${NC}"
    fi
fi

# Docker 컨테이너 확인 및 종료
if docker ps | grep -q quant_; then
    echo -e "\n${YELLOW}Docker 컨테이너 종료 중...${NC}"
    cd SL-Back-Test
    docker-compose down
    cd ..
    echo -e "${GREEN}✅ Docker 컨테이너 종료됨${NC}"
fi

echo -e "\n${GREEN}🛑 모든 서비스가 종료되었습니다.${NC}"