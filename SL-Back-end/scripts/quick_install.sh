#!/bin/bash

echo "🚀 빠른 설치 스크립트 - Python 3.13 최적화"
echo "=========================================="

# PostgreSQL 설치 (필수)
if ! command -v pg_config &> /dev/null; then
    echo "📦 PostgreSQL 설치 중..."
    brew install postgresql@15
    export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
fi

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 핵심 패키지만 먼저 설치
echo "1️⃣ 핵심 패키지 설치..."
pip install fastapi uvicorn pydantic pydantic-settings

echo "2️⃣ 데이터베이스 패키지 설치..."
pip install asyncpg sqlalchemy psycopg[binary]

echo "3️⃣ 데이터 처리 패키지 설치..."
pip install polars  # pandas/numpy 대신 polars만 사용

echo "4️⃣ 기타 필수 패키지 설치..."
pip install redis python-dotenv orjson httpx

echo "✅ 설치 완료!"
echo ""
echo "서버 실행:"
echo "uvicorn app.main:app --reload --port 8000"