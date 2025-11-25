#!/usr/bin/env python3
"""
유명 전략 백테스트 실행 스크립트 (짧은 기간)
- 2개 유명 전략 6개월 기간 백테스트
- 기업행동 감지 및 강제 청산 로직 검증
"""

import asyncio
import json
import time
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal
from uuid import uuid4

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 경로 설정
import sys
sys.path.insert(0, '/Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end')

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine

# 유명 전략 정의 (2개만)
FAMOUS_STRATEGIES = [
    {
        "name": "저PER_고ROE",
        "description": "PER 낮고 ROE 높은 가치주",
        "buy_conditions": [
            {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 10},
            {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 10}
        ],
        "buy_logic": "A AND B",
        "priority_factor": "PER",
        "priority_order": "asc"
    },
    {
        "name": "고배당_저PBR",
        "description": "배당 높고 PBR 낮은 안정주",
        "buy_conditions": [
            {"name": "A", "exp_left_side": "기본값({배당수익률})", "inequality": ">", "exp_right_side": 3},
            {"name": "B", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 1}
        ],
        "buy_logic": "A AND B",
        "priority_factor": "배당수익률",
        "priority_order": "desc"
    }
]


async def run_backtest(strategy: Dict, start_date_str: str, end_date_str: str) -> Dict[str, Any]:
    """
    단일 전략 백테스트 실행
    """
    strategy_name = strategy["name"]
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 전략 실행: {strategy_name}")
    logger.info(f"   설명: {strategy['description']}")
    logger.info(f"   기간: {start_date_str} ~ {end_date_str}")
    logger.info(f"{'='*60}")

    start_date = datetime.strptime(start_date_str, "%Y%m%d").date()
    end_date = datetime.strptime(end_date_str, "%Y%m%d").date()

    result = {
        "strategy_name": strategy_name,
        "description": strategy["description"],
        "period": f"{start_date_str} ~ {end_date_str}",
        "cache_timing": {},
        "corporate_actions": [],
        "forced_liquidations": [],
        "performance": {},
        "error": None
    }

    try:
        async with AsyncSessionLocal() as db:
            # 백테스트 엔진 초기화
            engine = BacktestEngine(db=db)

            # 캐시 시간 측정 시작
            cache_start = time.time()

            # 백테스트 실행
            backtest_result = await engine.run_backtest(
                backtest_id=uuid4(),
                buy_conditions=strategy["buy_conditions"],
                sell_conditions=[],  # 빈 매도 조건
                start_date=start_date,
                end_date=end_date,
                condition_sell=None,
                target_and_loss={
                    "target_gain": 20,       # 20% 목표가
                    "stop_loss": 10          # 10% 손절
                },
                hold_days={
                    "min_hold_days": 5,
                    "max_hold_days": 60,
                    "sell_price_basis": "시가",
                    "sell_price_offset": 0
                },
                initial_capital=Decimal("10000000"),  # 1000만원
                rebalance_frequency="DAILY",
                max_positions=10,
                position_sizing="EQUAL_WEIGHT",
                benchmark="KOSPI",
                commission_rate=0.00015,   # 0.015%
                slippage=0.001,            # 0.1%
                target_themes=None,
                target_stocks=None,
                target_universes=None,
                per_stock_ratio=0.1,       # 종목당 10%
                max_buy_value=None,
                max_daily_stock=3          # 일일 최대 3종목
            )

            cache_end = time.time()
            cache_elapsed = cache_end - cache_start

            # 캐시 타이밍 기록
            result["cache_timing"] = {
                "total_elapsed_sec": round(cache_elapsed, 2),
                "cache_hit": getattr(engine, '_cache_hit', False),
                "cache_key": getattr(engine, '_cache_key', None)
            }

            # 기업행동 감지 정보
            if hasattr(engine, 'corporate_actions') and engine.corporate_actions:
                result["corporate_actions"] = [
                    {
                        "stock_code": code,
                        "stock_name": info.get("stock_name", ""),
                        "event_date": str(info.get("event_date", "")),
                        "change_rate": round(info.get("change_rate", 0), 2),
                        "prev_price": float(info.get("prev_price", 0)),
                        "current_price": float(info.get("current_price", 0)),
                        "action_type": info.get("action_type", "")
                    }
                    for code, info in engine.corporate_actions.items()
                ]
                logger.warning(f"🚨 기업행동 감지: {len(result['corporate_actions'])}개 종목")

            # 강제 청산 정보
            if hasattr(engine, 'blocked_stocks') and engine.blocked_stocks:
                result["forced_liquidations"] = list(engine.blocked_stocks)
                logger.warning(f"🔒 강제 청산된 종목: {len(result['forced_liquidations'])}개")

            # 성과 지표
            if backtest_result:
                result["performance"] = {
                    "total_return": round(float(backtest_result.total_return), 2),
                    "annual_return": round(float(backtest_result.annual_return), 2),
                    "max_drawdown": round(float(backtest_result.max_drawdown), 2),
                    "sharpe_ratio": round(float(backtest_result.sharpe_ratio), 3),
                    "win_rate": round(float(backtest_result.win_rate), 2),
                    "total_trades": backtest_result.total_trades,
                    "final_value": round(float(backtest_result.final_value), 0)
                }

                logger.info(f"\n📊 성과 요약:")
                logger.info(f"   총 수익률: {result['performance']['total_return']}%")
                logger.info(f"   연환산 수익률: {result['performance']['annual_return']}%")
                logger.info(f"   최대 낙폭: {result['performance']['max_drawdown']}%")
                logger.info(f"   샤프 비율: {result['performance']['sharpe_ratio']}")
                logger.info(f"   승률: {result['performance']['win_rate']}%")
                logger.info(f"   총 거래 수: {result['performance']['total_trades']}")
                logger.info(f"   최종 자산: {result['performance']['final_value']:,.0f}원")

    except Exception as e:
        logger.error(f"❌ 백테스트 실행 오류: {e}")
        result["error"] = str(e)
        import traceback
        traceback.print_exc()

    return result


async def run_all_strategies():
    """
    모든 유명 전략 백테스트 실행
    """
    # 6개월 기간 설정 (2024-05-01 ~ 2024-10-31)
    end_date = "20241031"
    start_date = "20240501"

    logger.info("\n" + "="*80)
    logger.info("🎯 유명 전략 백테스트 시작")
    logger.info(f"   기간: {start_date} ~ {end_date} (6개월)")
    logger.info(f"   전략 수: {len(FAMOUS_STRATEGIES)}개")
    logger.info("="*80 + "\n")

    results = []
    total_start = time.time()

    for i, strategy in enumerate(FAMOUS_STRATEGIES, 1):
        logger.info(f"\n[{i}/{len(FAMOUS_STRATEGIES)}] {strategy['name']} 실행 중...")

        strategy_start = time.time()
        result = await run_backtest(strategy, start_date, end_date)
        strategy_elapsed = time.time() - strategy_start

        result["execution_time_sec"] = round(strategy_elapsed, 2)
        results.append(result)

        logger.info(f"✅ {strategy['name']} 완료 ({strategy_elapsed:.2f}초)")

    total_elapsed = time.time() - total_start

    # 결과 요약
    logger.info("\n" + "="*80)
    logger.info("📊 백테스트 결과 요약")
    logger.info("="*80)

    # 전략별 수익률 비교
    logger.info("\n📈 전략별 수익률:")
    logger.info("-"*70)
    logger.info(f"{'전략명':<25} {'총수익률':>12} {'연수익률':>12} {'MDD':>12} {'거래수':>8}")
    logger.info("-"*70)

    for r in results:
        if r["error"]:
            logger.info(f"{r['strategy_name']:<25} {'오류':>12}: {r['error'][:30]}")
        else:
            perf = r["performance"]
            if perf:
                logger.info(
                    f"{r['strategy_name']:<25} "
                    f"{perf.get('total_return', 0):>11.2f}% "
                    f"{perf.get('annual_return', 0):>11.2f}% "
                    f"{perf.get('max_drawdown', 0):>11.2f}% "
                    f"{perf.get('total_trades', 0):>8}"
                )
            else:
                logger.info(f"{r['strategy_name']:<25} {'데이터 없음':>12}")

    # 기업행동 감지 요약
    total_corporate_actions = sum(len(r["corporate_actions"]) for r in results)
    total_forced_liquidations = sum(len(r["forced_liquidations"]) for r in results)

    logger.info(f"\n🚨 기업행동 감지 요약:")
    logger.info(f"   감지된 기업행동: {total_corporate_actions}건")
    logger.info(f"   강제 청산된 종목: {total_forced_liquidations}개")

    # 상세 기업행동 목록
    if total_corporate_actions > 0:
        logger.info(f"\n📋 감지된 기업행동 상세:")
        for r in results:
            for ca in r["corporate_actions"][:10]:  # 최대 10개만 표시
                logger.info(
                    f"   - {ca['stock_name']}({ca['stock_code']}) {ca['event_date']}: "
                    f"{ca['prev_price']:,.0f}원 → {ca['current_price']:,.0f}원 ({ca['change_rate']:+.1f}%)"
                )

    # 캐시 성능 분석
    logger.info(f"\n⚡ 캐시 성능 분석:")
    for r in results:
        ct = r.get("cache_timing", {})
        cache_status = "캐시 히트" if ct.get("cache_hit") else "캐시 미스"
        elapsed = ct.get("total_elapsed_sec", "N/A")
        logger.info(f"   {r['strategy_name']}: {elapsed}초 ({cache_status})")

    logger.info(f"\n⏱️ 총 실행 시간: {total_elapsed:.2f}초")
    logger.info("="*80)

    # JSON 결과 저장
    output = {
        "execution_summary": {
            "period": f"{start_date} ~ {end_date}",
            "total_strategies": len(FAMOUS_STRATEGIES),
            "total_execution_time_sec": round(total_elapsed, 2),
            "total_corporate_actions": total_corporate_actions,
            "total_forced_liquidations": total_forced_liquidations
        },
        "strategy_results": results
    }

    with open("/app/backtest_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"\n📁 결과 파일 저장: backtest_results.json")

    return output


if __name__ == "__main__":
    asyncio.run(run_all_strategies())
