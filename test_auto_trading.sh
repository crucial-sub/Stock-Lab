#!/bin/bash

echo "======================================="
echo "자동매매 테스트 스크립트"
echo "======================================="
echo ""

# 1. 백엔드가 정상 작동하는지 확인
echo "1. 백엔드 상태 확인..."
BACKEND_STATUS=$(curl -s http://localhost:8000/health | grep -o "healthy" || echo "error")
if [ "$BACKEND_STATUS" = "healthy" ]; then
    echo "✅ 백엔드 정상 작동 중"
else
    echo "❌ 백엔드 연결 실패"
    exit 1
fi
echo ""

# 2. 로그인 필요 (실제 토큰 필요)
echo "2. 자동매매 테스트를 하려면 먼저 다음을 확인하세요:"
echo ""
echo "   ① 프론트엔드에서 로그인이 되어 있어야 합니다"
echo "   ② 완료된 백테스트가 있어야 합니다"
echo "   ③ 키움증권 API가 연동되어 있어야 합니다"
echo ""

# 3. 테스트 방법 안내
echo "======================================="
echo "📋 자동매매 테스트 절차"
echo "======================================="
echo ""
echo "Step 1: 백테스트 결과 페이지 접속"
echo "  → http://localhost:3000/quant/list"
echo "  → 완료된 백테스트 클릭"
echo ""
echo "Step 2: 자동매매 활성화"
echo "  → 결과 페이지에서 '자동매매 활성화' 버튼 클릭"
echo "  → 초기 자본금: 5천만원"
echo ""
echo "Step 3: 수동 실행 (테스트)"
echo "  → '수동 실행 (테스트)' 버튼 클릭"
echo "  → 조건에 맞는 종목 자동 선정 및 매수"
echo ""
echo "Step 4: 결과 확인"
echo "  → http://localhost:3000/mypage"
echo "  → 보유 종목 및 잔고 확인"
echo ""
echo "======================================="
echo "🔍 유용한 명령어"
echo "======================================="
echo ""
echo "# 백엔드 로그 실시간 확인 (자동매매 실행 로그 보기)"
echo "docker logs -f sl_backend_dev | grep -E 'auto.*trading|종목.*선정|매수'"
echo ""
echo "# 자동매매 관련 에러 확인"
echo "docker logs sl_backend_dev --tail 100 | grep -i error"
echo ""
echo "# 데이터베이스에서 자동매매 전략 확인"
echo "docker exec sl_postgres_dev psql -U [사용자명] -d stock_lab_investment_db -c \"SELECT * FROM auto_trading_strategies;\""
echo ""
