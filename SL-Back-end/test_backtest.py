#!/usr/bin/env python3
"""
백테스트 테스트 스크립트
간단한 백테스트를 실행하여 문제점을 파악합니다.
"""

import asyncio
import sys
import logging
from datetime import date, timedelta
from pathlib import Path
import uuid

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.api.routes.backtest import execute_backtest_wrapper

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_minimal_backtest():
    """최소 설정으로 백테스트 테스트"""

    # 간단한 요청 데이터
    request_data = {
        "user_id": "test_user",
        "strategy_name": "테스트 전략",
        "start_date": "20241201",  # 1개월만
        "end_date": "20241231",
        "initial_investment": 10000000,
        "is_day_or_month": "daily",
        "commission_rate": 0.15,
        "slippage": 0.1,
        "rebalance_frequency": "WEEKLY",
        "max_holdings": 5,

        # 매수 조건 (단순)
        "buy_conditions": [
            {
                "name": "A",
                "exp_left_side": "기본값({PBR})",
                "inequality": "<",
                "exp_right_side": 5.0
            }
        ],
        "buy_logic": "A",
        "priority_factor": "PER",
        "priority_order": "asc",
        "per_stock_ratio": 20,
        "buy_price_basis": "시가",
        "buy_price_offset": 0,

        # 매도 조건 (익절/손절)
        "target_and_loss": {
            "profit_target": 10,
            "stop_loss": -5
        },

        # 매매 대상 (1개 종목)
        "trade_targets": {
            "use_all_stocks": False,
            "selected_themes": [],
            "selected_stocks": ["005930"],  # 삼성전자만
            "selected_stock_count": 1
        }
    }

    # 백테스트 실행
    logger.info("=" * 80)
    logger.info("백테스트 테스트 시작")
    logger.info("=" * 80)

    try:
        async with AsyncSessionLocal() as db:
            # mock request 객체 생성
            class MockRequest:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            request = MockRequest(request_data)

            # 백테스트 실행
            import uuid
            session_id = str(uuid.uuid4())
            strategy_id = str(uuid.uuid4())

            result = await execute_backtest_wrapper(
                session_id=session_id,
                strategy_id=strategy_id,
                start_date=date(2024, 12, 1),
                end_date=date(2024, 12, 31),
                initial_capital=10000000,
                benchmark="KOSPI",
                target_themes=[],
                target_stocks=["005930"],  # 삼성전자
                use_all_stocks=False,
                buy_conditions=[{
                    "exp_left_side": "기본값({PBR})",
                    "inequality": "<",
                    "exp_right_side": 5.0
                }],
                buy_logic="A",
                priority_factor="PER",
                priority_order="asc",
                max_holdings=5,
                per_stock_ratio=20.0,
                rebalance_frequency="WEEKLY",
                commission_rate=0.15,
                slippage=0.1,
                target_and_loss={"profit_target": 10, "stop_loss": -5},
                hold_days=None,
                condition_sell=None
            )

            logger.info("=" * 80)
            logger.info("✅ 백테스트 완료!")
            logger.info(f"Session ID: {result.get('backtestId', 'Unknown')}")
            logger.info(f"Status: {result.get('status', 'Unknown')}")
            logger.info("=" * 80)

            return result

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ 백테스트 실패: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return None

async def test_factor_calculation_speed():
    """팩터 계산 속도 테스트"""
    from app.services.backtest import BacktestEngine
    import time

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)

        # 1주일 데이터로 테스트
        start = date(2024, 12, 23)
        end = date(2024, 12, 30)

        logger.info("=" * 80)
        logger.info("팩터 계산 속도 테스트")
        logger.info(f"기간: {start} ~ {end}")
        logger.info("=" * 80)

        start_time = time.time()

        # 가격 데이터 로드
        price_data = await engine._load_price_data(
            start_date=start,
            end_date=end,
            target_themes=["증권"],
            target_stocks=["005930"]
        )

        load_time = time.time() - start_time
        logger.info(f"가격 데이터 로드: {load_time:.2f}초 ({len(price_data)}개 레코드)")

        # 재무 데이터 로드
        start_time = time.time()
        financial_data = await engine._load_financial_data(start, end)

        fin_time = time.time() - start_time
        logger.info(f"재무 데이터 로드: {fin_time:.2f}초")

        # 팩터 계산
        start_time = time.time()
        factor_data = await engine._calculate_all_factors(
            price_data, financial_data, start, end
        )

        calc_time = time.time() - start_time
        logger.info(f"팩터 계산: {calc_time:.2f}초 ({len(factor_data)}개 팩터)")

        logger.info("=" * 80)
        logger.info(f"전체 시간: {load_time + fin_time + calc_time:.2f}초")
        logger.info("=" * 80)

if __name__ == "__main__":
    # 테스트 선택
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "speed":
        asyncio.run(test_factor_calculation_speed())
    else:
        asyncio.run(test_minimal_backtest())