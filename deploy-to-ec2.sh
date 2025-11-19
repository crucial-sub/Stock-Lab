#!/bin/bash

# ==============================================
# EC2 배포 스크립트
# ==============================================

echo "📦 EC2 배포를 시작합니다..."

# 1. Git에서 최신 코드 가져오기
echo "1️⃣ Git에서 최신 코드를 가져옵니다..."
git pull origin main

# 2. .env.ec2를 .env로 복사
echo "2️⃣ EC2용 환경 변수를 설정합니다..."
cp .env.ec2 .env

# 3. 기존 컨테이너 중지 및 제거
echo "3️⃣ 기존 컨테이너를 중지합니다..."
docker compose down

# 4. 도커 이미지 다시 빌드 (no-cache로 강제 재빌드)
echo "4️⃣ 도커 이미지를 다시 빌드합니다..."
docker compose build --no-cache

# 5. 컨테이너 시작
echo "5️⃣ 컨테이너를 시작합니다..."
docker compose up -d

# 6. 백엔드 로그 확인 (DATABASE_URL 확인)
echo "6️⃣ 백엔드 환경 변수를 확인합니다..."
sleep 5
docker exec sl_backend printenv | grep DATABASE_URL

# 7. 컨테이너 상태 확인
echo "7️⃣ 컨테이너 상태를 확인합니다..."
docker compose ps

echo "✅ 배포가 완료되었습니다!"
echo ""
echo "다음 URL에서 확인하세요:"
echo "  - Frontend: http://54.180.34.167:3000"
echo "  - Backend: http://54.180.34.167:8000/docs"
echo ""
echo "로그 확인:"
echo "  docker logs -f sl_backend"
echo "  docker logs -f sl_frontend"
