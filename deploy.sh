#!/bin/bash

# EC2 배포 자동화 스크립트
echo "🚀 Stock-Lab 배포 시작..."

# 1. Git Pull
echo "📦 최신 코드 받아오기..."
git pull origin main

# 2. .env 파일 복사 (처음 1회만)
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성..."
    cp .env.ec2 .env
    echo "⚠️  .env 파일을 수정해주세요 (EC2 IP 설정)"
    echo "    nano .env"
    echo "    NEXT_PUBLIC_API_BASE_URL을 EC2 퍼블릭 IP로 변경"
    exit 1
fi

if [ ! -f SL-Back-end/.env ]; then
    echo "📝 백엔드 .env 파일 생성..."
    cp SL-Back-end/.env.ec2 SL-Back-end/.env
    echo "⚠️  SL-Back-end/.env 파일을 수정해주세요 (CORS 설정)"
    echo "    nano SL-Back-end/.env"
    echo "    BACKEND_CORS_ORIGINS에 EC2 IP 추가"
    exit 1
fi

# 3. Docker Compose 실행
echo "🐳 Docker 컨테이너 시작..."
docker-compose down
docker-compose up -d --build

# 4. 로그 확인
echo "📋 서비스 시작 대기 중..."
sleep 10
docker-compose ps

echo ""
echo "✅ 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 프론트엔드: http://$(curl -s http://checkip.amazonaws.com):3000"
echo "🔧 백엔드 API: http://$(curl -s http://checkip.amazonaws.com):8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 로그 확인: docker-compose logs -f"
echo "🔄 재시작: docker-compose restart"
echo "⛔ 중지: docker-compose down"
