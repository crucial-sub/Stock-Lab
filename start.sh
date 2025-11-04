#!/bin/bash

# SL Quant Investment Platform 시작 스크립트

echo "🚀 SL Quant Investment Platform 시작 중..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python 버전 확인
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "Python 버전: $python_version"

# Backend 시작
echo -e "\n${YELLOW}1. Backend 서버 시작${NC}"
cd SL-Back-Test

# Python 3.13 경고
if [[ "$python_version" == "3.13" ]]; then
    echo -e "${RED}⚠️  경고: Python 3.13이 감지되었습니다.${NC}"
    echo "일부 패키지가 호환되지 않을 수 있습니다."
    echo "Python 3.11 사용을 권장합니다."
    echo ""
    echo "최소 패키지로 실행하시겠습니까? (y/n)"
    read -r answer
    if [[ "$answer" == "y" ]]; then
        echo "최소 패키지로 설치 진행..."
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install -q -r requirements_minimal.txt
    else
        echo "Docker를 사용하여 실행합니다..."
        docker-compose up -d postgres redis
        sleep 5
        docker-compose up -d api
        echo -e "${GREEN}✅ Backend가 Docker에서 실행 중 (http://localhost:8000)${NC}"
        cd ..
    fi
else
    # Python 3.11 이하
    if [ ! -d "venv" ]; then
        echo "가상환경 생성 중..."
        python3 -m venv venv
    fi
    source venv/bin/activate

    echo "패키지 설치 중..."
    pip install -q -r requirements_stable.txt 2>/dev/null || pip install -q -r requirements_minimal.txt
fi

# 로그 디렉토리 생성
mkdir -p logs

# Backend 서버 실행 (백그라운드)
if [[ "$answer" != "n" ]]; then
    echo "Backend 서버 시작 중..."
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend 서버 시작됨 (PID: $BACKEND_PID)${NC}"
fi

cd ..

# Frontend 시작
echo -e "\n${YELLOW}2. Frontend 서버 시작${NC}"
cd SL-Front-End

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo "패키지 설치 중..."
    npm install
fi

# Frontend 서버 실행 (백그라운드)
echo "Frontend 서버 시작 중..."
nohup npm run dev > ../SL-Back-Test/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend 서버 시작됨 (PID: $FRONTEND_PID)${NC}"

cd ..

# 서버 상태 확인
echo -e "\n${YELLOW}3. 서버 상태 확인${NC}"
sleep 3

# Backend 헬스체크
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend 서버 정상 작동 중${NC}"
else
    echo -e "${RED}❌ Backend 서버 응답 없음${NC}"
fi

# Frontend 확인
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend 서버 정상 작동 중${NC}"
else
    echo -e "${RED}❌ Frontend 서버 응답 없음${NC}"
fi

echo -e "\n${GREEN}🎉 서비스가 시작되었습니다!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "종료하려면: ./stop.sh"
echo "로그 확인: tail -f SL-Back-Test/logs/*.log"

# PID 파일 저장
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid