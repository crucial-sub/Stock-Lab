"""
모든 유명 전략들을 100종목만 사용하도록 업데이트하는 스크립트
AI 어시스턴트 데모용으로 빠른 백테스트를 위해 종목 수 제한
"""

import asyncio
import json
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import AsyncSessionLocal
from app.models.investment_strategy import InvestmentStrategy
from app.models.stock_price import StockPrice
from app.models.company import Company


async def get_top_100_stocks_by_volume(db: AsyncSession) -> list[str]:
    """
    최근 거래량 기준 상위 100개 종목 코드 조회
    """
    # Company 테이블과 조인하여 stock_code 가져오기
    # 평균 거래량이 높은 종목 100개 선택
    query = (
        select(
            Company.stock_code,
            func.avg(StockPrice.volume).label('avg_volume')
        )
        .join(Company, StockPrice.company_id == Company.company_id)
        .where(StockPrice.volume.isnot(None))
        .where(Company.stock_code.isnot(None))
        .group_by(Company.stock_code)
        .order_by(desc('avg_volume'))
        .limit(100)
    )

    result = await db.execute(query)
    stock_codes = [row.stock_code for row in result.all()]

    return stock_codes


async def update_all_strategies():
    """
    모든 유명 전략들의 backtest_config를 업데이트하여
    use_all_stocks: false로 설정하고 상위 100개 종목만 사용하도록 변경
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. 상위 100개 종목 코드 조회
            print("📊 상위 100개 종목 조회 중...")
            stock_codes = await get_top_100_stocks_by_volume(db)

            if not stock_codes:
                print("❌ 종목 데이터를 찾을 수 없습니다.")
                return

            print(f"✅ {len(stock_codes)}개 종목 조회 완료")
            print(f"샘플: {stock_codes[:10]}")

            # 2. 모든 투자 전략 조회
            query = select(InvestmentStrategy)
            result = await db.execute(query)
            all_strategies = result.scalars().all()

            if not all_strategies:
                print("❌ 투자 전략을 찾을 수 없습니다.")
                return

            print(f"\n📋 총 {len(all_strategies)}개 전략 발견")

            # 3. 각 전략의 backtest_config 업데이트
            updated_count = 0
            for strategy in all_strategies:
                print(f"\n🔄 [{strategy.id}] {strategy.name} 전략 업데이트 중...")

                # 기존 설정 출력
                old_use_all = strategy.backtest_config.get('trade_targets', {}).get('use_all_stocks')
                old_stocks_count = len(strategy.backtest_config.get('trade_targets', {}).get('selected_stocks', []))
                print(f"   기존: use_all_stocks={old_use_all}, selected_stocks={old_stocks_count}개")

                # backtest_config 업데이트
                backtest_config = strategy.backtest_config.copy()

                if 'trade_targets' not in backtest_config:
                    backtest_config['trade_targets'] = {}

                backtest_config['trade_targets']['use_all_stocks'] = False
                backtest_config['trade_targets']['selected_stocks'] = stock_codes

                # 데이터베이스 업데이트
                strategy.backtest_config = backtest_config
                # JSONB 필드 변경사항을 SQLAlchemy가 추적하도록 플래그 설정
                flag_modified(strategy, 'backtest_config')
                updated_count += 1

                print(f"   ✅ 업데이트 완료: use_all_stocks=False, selected_stocks={len(stock_codes)}개")

            # 4. 변경사항 커밋
            await db.commit()

            print(f"\n🎉 총 {updated_count}개 전략 업데이트 완료!")
            print(f"모든 전략이 상위 {len(stock_codes)}개 종목으로 백테스트를 수행합니다.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(update_all_strategies())
