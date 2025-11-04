#!/bin/bash

echo "🚀 SL-Back-Test 의존성 설치 스크립트"
echo "===================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PostgreSQL 설치 확인 (psycopg2-binary 빌드에 필요)
echo -e "\n${YELLOW}1. PostgreSQL 설치 확인...${NC}"
if brew list postgresql@15 &>/dev/null || brew list postgresql &>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL이 이미 설치되어 있습니다.${NC}"
else
    echo -e "${YELLOW}PostgreSQL 설치 중...${NC}"
    brew install postgresql@15
    echo -e "${GREEN}✓ PostgreSQL 설치 완료${NC}"
fi

# pg_config PATH 추가
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Python 버전 확인
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo -e "\n${YELLOW}2. Python 버전: $python_version${NC}"

# 가상환경 생성/활성화
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}3. 가상환경 생성 중...${NC}"
    python3 -m venv venv
else
    echo -e "\n${YELLOW}3. 기존 가상환경 사용${NC}"
fi

source venv/bin/activate

# pip 업그레이드
echo -e "\n${YELLOW}4. pip 업그레이드...${NC}"
pip install --upgrade pip setuptools wheel

# 패키지 설치
echo -e "\n${YELLOW}5. 패키지 설치 중...${NC}"

# Python 3.13용 최적화된 requirements 사용
pip install -r requirements_working.txt

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ 모든 패키지 설치 완료!${NC}"

    echo -e "\n${YELLOW}다음 단계:${NC}"
    echo "1. Docker 서비스 시작:"
    echo -e "${BLUE}   docker-compose -f docker-compose-simple.yml up -d${NC}"
    echo ""
    echo "2. 백엔드 서버 실행:"
    echo -e "${BLUE}   source venv/bin/activate${NC}"
    echo -e "${BLUE}   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000${NC}"
else
    echo -e "\n${RED}❌ 패키지 설치 실패${NC}"
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "1. PostgreSQL 설치 확인:"
    echo "   brew install postgresql@15"
    echo "2. 개별 패키지 설치 시도:"
    echo "   pip install fastapi uvicorn"
fi