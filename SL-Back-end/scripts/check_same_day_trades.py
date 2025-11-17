#!/usr/bin/env python3
"""
백테스트에서 같은 날 매수/매도된 종목을 분석하는 스크립트
- 같은 종목이 같은 날 매수/매도되었는지 확인
- 서로 다른 종목인지 확인
"""

import asyncio
import asyncpg
from datetime import datetime
import sys

# SSH 터널을 통한 데이터베이스 연결
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,  # SSH 터널 포트
    "database": "stocklabDB",
    "user": "nmmteam05",
    "password": "nmmteam05"
}

async def analyze_same_day_trades(backtest_id: str):
    """같은 날 매수/매도가 발생한 종목들을 분석"""

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print(f"\n{'='*80}")
        print(f"백테스트 ID: {backtest_id}")
        print(f"{'='*80}\n")

        # 1. 같은 날 매수/매도 횟수가 같은 날짜 찾기
        query = """
        WITH daily_counts AS (
            SELECT
                trade_date,
                SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) as buy_count,
                SUM(CASE WHEN trade_type = 'SELL' THEN 1 ELSE 0 END) as sell_count
            FROM simulation_trades
            WHERE session_id = $1
            GROUP BY trade_date
        )
        SELECT trade_date, buy_count, sell_count
        FROM daily_counts
        WHERE buy_count = sell_count AND buy_count > 0
        ORDER BY trade_date
        """

        same_count_days = await conn.fetch(query, backtest_id)

        if not same_count_days:
            print("✅ 같은 날 매수/매도 횟수가 같은 날이 없습니다!")
            return

        print(f"⚠️  같은 날 매수/매도 횟수가 같은 날: {len(same_count_days)}일\n")

        # 2. 각 날짜별로 상세 분석
        overlap_count = 0
        total_days = len(same_count_days)

        for row in same_count_days[:10]:  # 처음 10일만 상세 분석
            trade_date = row['trade_date']
            buy_count = row['buy_count']
            sell_count = row['sell_count']

            # 해당 날짜의 매수/매도 종목 조회
            detail_query = """
            SELECT
                stock_code,
                stock_name,
                trade_type,
                quantity,
                price,
                reason
            FROM simulation_trades
            WHERE session_id = $1 AND trade_date = $2
            ORDER BY trade_type DESC, stock_code
            """

            trades = await conn.fetch(detail_query, backtest_id, trade_date)

            # 매수/매도 종목 분리
            buy_stocks = {t['stock_code'] for t in trades if t['trade_type'] == 'BUY'}
            sell_stocks = {t['stock_code'] for t in trades if t['trade_type'] == 'SELL'}

            # 겹치는 종목 확인
            overlap_stocks = buy_stocks & sell_stocks

            if overlap_stocks:
                overlap_count += 1
                print(f"❌ {trade_date} - 같은 종목 매수/매도 발생!")
                print(f"   매수: {buy_count}개, 매도: {sell_count}개")
                print(f"   🚨 겹치는 종목: {overlap_stocks}")
            else:
                print(f"✅ {trade_date} - 서로 다른 종목")
                print(f"   매수: {buy_count}개 종목 {list(buy_stocks)[:3]}...")
                print(f"   매도: {sell_count}개 종목 {list(sell_stocks)[:3]}...")

            # 매도 사유 확인
            sell_reasons = {}
            for t in trades:
                if t['trade_type'] == 'SELL':
                    reason = t['reason'] or 'UNKNOWN'
                    sell_reasons[reason] = sell_reasons.get(reason, 0) + 1

            print(f"   매도 사유: {sell_reasons}")
            print()

        # 3. 요약 통계
        print(f"\n{'='*80}")
        print(f"📊 분석 요약")
        print(f"{'='*80}")
        print(f"같은 날 매수/매도 횟수가 같은 날: {total_days}일")
        print(f"그 중 같은 종목을 매수/매도한 날: {overlap_count}일")

        if overlap_count > 0:
            print(f"\n⚠️  {overlap_count}일에 같은 종목이 같은 날 매수/매도되었습니다!")
            print(f"   이는 최소 보유기간 정책을 위반한 것입니다.")
        else:
            print(f"\n✅ 모든 날짜에서 매수/매도는 서로 다른 종목입니다.")
            print(f"   이는 리밸런싱 로직이 정상 작동하는 것입니다:")
            print(f"   - 조건 불만족 종목 매도")
            print(f"   - 조건 만족 신규 종목 매수")

    finally:
        await conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_same_day_trades.py <backtest_id>")
        sys.exit(1)

    backtest_id = sys.argv[1]
    asyncio.run(analyze_same_day_trades(backtest_id))
