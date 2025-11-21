import asyncio
from app.core.database import AsyncSessionLocal
from app.models.auto_trading import AutoTradingStrategy
from app.services.auto_trading_service import AutoTradingService
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

        print("=== 활성화된 전략 정보 ===")
        print(f"Strategy ID: {strategy.strategy_id}")
        print(f"Session ID: {strategy.simulation_session_id}")
        print(f"Allocated Capital: {strategy.allocated_capital:,.0f}원")
        print(f"Per Stock Ratio: {strategy.per_stock_ratio}%")
        print(f"Max Positions: {strategy.max_positions}")
        print()

        print("🔍 종목 선정 및 매매 실행 시작...")
        print()

        # execute_trading 메서드 호출
        trade_result = await AutoTradingService.execute_trading(
            db=db,
            strategy_id=strategy.strategy_id
        )

        print("✅ 실행 완료!")
        selected_cnt = trade_result.get("selected_count", 0)
        bought_cnt = trade_result.get("bought_count", 0)
        print(f"선정 종목 수: {selected_cnt}")
        print(f"매수 성공: {bought_cnt}")
        print()

        stocks = trade_result.get("stocks", [])
        if stocks:
            print("📊 매수된 종목:")
            for i, stock in enumerate(stocks[:20], 1):
                name = stock.get("company_name", "N/A")
                code = stock.get("stock_code", "N/A")
                price = stock.get("current_price", 0)
                per = stock.get("per", "N/A")
                pbr = stock.get("pbr", "N/A")
                print(f"  {i}. {name} ({code})")
                print(f"     현재가: {price:,.0f}원, PER: {per}, PBR: {pbr}")

asyncio.run(execute_manual_trading())
