import asyncio
from datetime import date
from app.core.database import AsyncSessionLocal
from app.models.auto_trading import AutoTradingStrategy
from app.services.auto_trading_executor import AutoTradingExecutor
from sqlalchemy import select

async def execute_manual_trading():
    async with AsyncSessionLocal() as db:
        # 활성화된 전략 조회
        result = await db.execute(
            select(AutoTradingStrategy).where(AutoTradingStrategy.is_active == True)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            print("활성화된 전략이 없습니다.")
            return

        print("=" * 80)
        print("🤖 자동매매 수동 실행")
        print("=" * 80)
        print()
        print("=== 전략 정보 ===")
        print(f"Strategy ID: {strategy.strategy_id}")
        print(f"할당 자본: {strategy.allocated_capital:,.0f}원")
        print(f"현금 잔고: {strategy.cash_balance:,.0f}원")
        print(f"종목당 비율: {strategy.per_stock_ratio}%")
        print(f"최대 보유 종목: {strategy.max_positions}개")
        print()

        # 1단계: 종목 선정
        print("🔍 1단계: 종목 선정 중...")
        selected_stocks = await AutoTradingExecutor.select_stocks_for_strategy(db, strategy)

        print(f"✅ {len(selected_stocks)}개 종목 선정 완료")
        if selected_stocks:
            print()
            print("📊 선정된 종목 (상위 20개):")
            for i, stock in enumerate(selected_stocks[:20], 1):
                name = stock.get("company_name", "N/A")
                code = stock.get("stock_code", "N/A")
                price = stock.get("current_price", 0)
                per = stock.get("per", "N/A")
                pbr = stock.get("pbr", "N/A")
                market_cap = stock.get("market_cap", 0)

                print(f"  {i}. {name} ({code})")
                print(f"     가격: {price:,.0f}원 | PER: {per} | PBR: {pbr} | 시가총액: {market_cap/100000000:,.0f}억원")

            if len(selected_stocks) > 20:
                print(f"  ... 외 {len(selected_stocks) - 20}개 종목")
        print()

        # 2단계: 매수 실행
        print("💰 2단계: 매수 주문 실행 중...")
        bought_count = await AutoTradingExecutor.execute_buy_orders(
            db, strategy, selected_stocks
        )

        print(f"✅ {bought_count}개 종목 매수 완료")
        print()

        if bought_count > 0:
            print("📈 매수 완료 종목:")
            for i, stock in enumerate(selected_stocks[:bought_count], 1):
                name = stock.get("company_name", "N/A")
                code = stock.get("stock_code", "N/A")
                price = stock.get("current_price", 0)

                print(f"  {i}. {name} ({code}) - {price:,.0f}원")

        print()
        print("=" * 80)
        print("✅ 자동매매 수동 실행 완료!")
        print("=" * 80)

asyncio.run(execute_manual_trading())
