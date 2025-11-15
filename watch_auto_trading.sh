#!/bin/bash
echo "======================================="
echo "자동매매 실시간 로그 모니터링"
echo "======================================="
echo ""
echo "백테스트 결과 페이지에서 자동매매를 활성화/실행하면"
echo "여기서 실시간으로 로그를 확인할 수 있습니다."
echo ""
echo "로그 모니터링 시작..."
echo "======================================="
echo ""

docker logs -f sl_backend_dev 2>&1 | grep -E "auto.*trading|자동매매|종목.*선정|매수|LiveTrade|LivePosition|AutoTrading" --line-buffered --color=always
