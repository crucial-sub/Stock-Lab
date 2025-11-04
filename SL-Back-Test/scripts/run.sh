#!/bin/bash

echo "🚀 SL-Back-Test 백엔드 시작 스크립트"
echo "===================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Docker 컨테이너 정리
echo -e "\n${YELLOW}1. 기존 Docker 컨테이너 정리 중...${NC}"
docker-compose down 2>/dev/null || true
docker rm -f sl_postgres sl_redis sl_api sl_redis_commander 2>/dev/null || true
echo -e "${GREEN}✓ 정리 완료${NC}"

# 2. PostgreSQL과 Redis만 실행
echo -e "\n${YELLOW}2. PostgreSQL과 Redis 시작...${NC}"
docker-compose -f docker-compose-simple.yml up -d
sleep 5

# 3. 컨테이너 상태 확인
echo -e "\n${YELLOW}3. 서비스 상태 확인...${NC}"
if docker ps | grep -q postgres; then
    echo -e "${GREEN}✓ PostgreSQL 실행 중${NC}"
else
    echo -e "${RED}✗ PostgreSQL 실행 실패${NC}"
fi

if docker ps | grep -q redis; then
    echo -e "${GREEN}✓ Redis 실행 중${NC}"
else
    echo -e "${RED}✗ Redis 실행 실패${NC}"
fi

# 4. Python 환경 설정
echo -e "\n${YELLOW}4. Python 환경 확인...${NC}"
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "Python 버전: $python_version"

# 5. 가상환경 생성/활성화
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi

echo -e "\n${BLUE}가상환경 활성화:${NC}"
echo "source venv/bin/activate"

# 6. 패키지 설치 가이드
echo -e "\n${YELLOW}5. 패키지 설치:${NC}"
if [[ "$python_version" == "3.13" ]]; then
    echo -e "${RED}Python 3.13 감지!${NC}"
    echo "다음 명령어를 실행하세요:"
    echo -e "${BLUE}pip install -r requirements_minimal.txt${NC}"
else
    echo "다음 명령어를 실행하세요:"
    echo -e "${BLUE}pip install -r requirements_stable.txt${NC}"
fi

# 7. 백엔드 서버 실행 가이드
echo -e "\n${YELLOW}6. 백엔드 서버 실행:${NC}"
echo -e "${BLUE}uvicorn app.main:app --reload --host 0.0.0.0 --port 8000${NC}"

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}준비 완료! 위의 명령어들을 순서대로 실행하세요.${NC}"
echo -e "${GREEN}============================================${NC}"

echo -e "\n${YELLOW}빠른 실행 (복사해서 사용):${NC}"
echo "------------------------"
echo "source venv/bin/activate"
if [[ "$python_version" == "3.13" ]]; then
    echo "pip install -r requirements_minimal.txt"
else
    echo "pip install -r requirements_stable.txt"
fi
echo "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "------------------------"

echo -e "\n${YELLOW}접속 URL:${NC}"
echo "- API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Health Check: http://localhost:8000/health"