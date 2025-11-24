#!/bin/bash

# EC2 + RDS + ElastiCache 배포 자동화 스크립트
echo "🚀 Stock-Lab 배포 시작 (AWS RDS + ElastiCache)..."

# 1. Git Pull
echo "📦 최신 코드 받아오기..."
git pull origin main

# 2. .env 파일 체크
if [ ! -f .env ]; then
    echo "📝 .env 파일 생성..."
    cp .env.ec2 .env
    echo ""
    echo "⚠️  .env 파일을 수정해주세요:"
    echo "    nano .env"
    echo "    → NEXT_PUBLIC_API_BASE_URL을 EC2 IP로 변경"
    echo ""
    exit 1
fi

if [ ! -f SL-Back-end/.env ]; then
    echo "📝 백엔드 .env 파일 생성..."
    cp SL-Back-end/.env.ec2 SL-Back-end/.env
    echo ""
    echo "⚠️  SL-Back-end/.env 파일을 수정해주세요:"
    echo "    nano SL-Back-end/.env"
    echo "    → DATABASE_URL: RDS 엔드포인트, 사용자명, 비밀번호"
    echo "    → REDIS_URL: ElastiCache 엔드포인트"
    echo "    → BACKEND_CORS_ORIGINS: EC2 IP"
    echo ""
    exit 1
fi

# 3. RDS/ElastiCache 설정 확인
echo "🔍 환경 변수 확인 중..."
if grep -q "YOUR_RDS_USERNAME" SL-Back-end/.env || grep -q "YOUR_RDS_PASSWORD" SL-Back-end/.env; then
    echo ""
    echo "❌ RDS 설정이 완료되지 않았습니다!"
    echo "   nano SL-Back-end/.env 에서 RDS 엔드포인트를 설정하세요."
    echo ""
    exit 1
fi

if grep -q "YOUR_ELASTICACHE_ENDPOINT" SL-Back-end/.env; then
    echo ""
    echo "❌ ElastiCache 설정이 완료되지 않았습니다!"
    echo "   nano SL-Back-end/.env 에서 ElastiCache 엔드포인트를 설정하세요."
    echo ""
    exit 1
fi

if grep -q "YOUR_EC2_IP" .env; then
    echo ""
    echo "❌ EC2 IP 설정이 완료되지 않았습니다!"
    echo "   nano .env 에서 NEXT_PUBLIC_API_BASE_URL을 설정하세요."
    echo ""
    exit 1
fi

echo "✅ 환경 변수 설정 완료"

# 4. Docker Compose 실행 (EC2용 - RDS/ElastiCache 사용)
echo "🐳 Docker 컨테이너 시작..."
docker-compose -f docker-compose.ec2.yml down
docker-compose -f docker-compose.ec2.yml up -d --build

# 5. 로그 확인
echo "📋 서비스 시작 대기 중..."
sleep 10
docker-compose -f docker-compose.ec2.yml ps

echo ""
echo "✅ 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 프론트엔드: http://$(curl -s http://checkip.amazonaws.com):3000"
echo "🔧 백엔드 API: http://$(curl -s http://checkip.amazonaws.com):8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 사용 중인 서비스:"
echo "   - AWS RDS PostgreSQL"
echo "   - AWS ElastiCache Redis"
echo "   - EC2 (Backend + Frontend)"
echo ""
echo "📋 로그 확인: docker-compose -f docker-compose.ec2.yml logs -f"
echo "🔄 재시작: docker-compose -f docker-compose.ec2.yml restart"
echo "⛔ 중지: docker-compose -f docker-compose.ec2.yml down"
