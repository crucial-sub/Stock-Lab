#!/bin/bash

echo "=================================="
echo "🔥 피터린치 전략 캐시 워밍 시작"
echo "=================================="
echo ""
echo "⏰ 예상 소요 시간: 2~5분"
echo "📍 시연 30분 전에 실행하세요"
echo ""

# 백엔드 컨테이너에서 스크립트 실행
docker exec sl_backend_dev python scripts/warm_peter_lynch_demo.py

echo ""
echo "=================================="
echo "✅ 캐시 워밍 완료!"
echo "=================================="
echo ""
echo "🎯 이제 시연 준비가 완료되었습니다:"
echo "   1. 첫 번째 백테스트 (기본 팩터): 1~2초"
echo "   2. 팩터 추가 후 재테스트: 3~5초"
echo ""
echo "💡 Tip: 캐시는 영구적이므로 재시작해도 유지됩니다"
echo ""
