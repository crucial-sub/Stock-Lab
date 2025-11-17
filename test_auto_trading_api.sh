#!/bin/bash

# 자동매매 API 직접 테스트 스크립트
# 사용법: ./test_auto_trading_api.sh <session_id> <access_token>

echo "======================================="
echo "자동매매 API 직접 테스트"
echo "======================================="
echo ""

# 파라미터 확인
if [ -z "$1" ]; then
    echo "❌ 사용법: $0 <session_id> [access_token]"
    echo ""
    echo "예시:"
    echo "  $0 0912c796-7514-45f5-8e87-d8b2dce22b16"
    echo ""
    echo "💡 Tip: session_id는 프론트엔드 URL에서 확인할 수 있습니다"
    echo "   http://localhost:3000/quant/result/<session_id>"
    exit 1
fi

SESSION_ID=$1
ACCESS_TOKEN=${2:-""}  # 실제 토큰이 필요합니다

echo "📝 Session ID: $SESSION_ID"
echo ""

# 1. 자동매매 활성화
echo "1️⃣  자동매매 활성화 시도..."
echo ""

ACTIVATE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auto-trading/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"initial_capital\": 50000000
  }")

echo "응답:"
echo "$ACTIVATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ACTIVATE_RESPONSE"
echo ""

# strategy_id 추출
STRATEGY_ID=$(echo "$ACTIVATE_RESPONSE" | grep -o '"strategy_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$STRATEGY_ID" ]; then
    echo "❌ 활성화 실패. 에러 확인:"
    echo "$ACTIVATE_RESPONSE"
    exit 1
fi

echo "✅ Strategy ID: $STRATEGY_ID"
echo ""
echo "======================================="
echo ""

# 2. 자동매매 수동 실행 (테스트)
echo "2️⃣  자동매매 수동 실행 (종목 선정 + 매수)..."
echo ""

EXECUTE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auto-trading/strategies/$STRATEGY_ID/execute" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "응답:"
echo "$EXECUTE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$EXECUTE_RESPONSE"
echo ""
echo "======================================="
echo ""

# 3. 자동매매 상태 조회
echo "3️⃣  자동매매 상태 조회..."
echo ""

STATUS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auto-trading/strategies/$STRATEGY_ID/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "응답:"
echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
echo ""
echo "======================================="
echo ""

# 4. 비활성화 (옵션)
read -p "자동매매를 비활성화하시겠습니까? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "4️⃣  자동매매 비활성화..."
    echo ""

    DEACTIVATE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auto-trading/strategies/$STRATEGY_ID/deactivate" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d "{
        \"sell_all_positions\": true
      }")

    echo "응답:"
    echo "$DEACTIVATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DEACTIVATE_RESPONSE"
    echo ""
fi

echo "======================================="
echo "✅ 테스트 완료"
echo "======================================="
