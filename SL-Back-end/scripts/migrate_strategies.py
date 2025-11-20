"""
투자 전략 데이터 마이그레이션 스크립트
investmentStrategies.json → investment_strategies 테이블

실행 방법:
    cd SL-Back-end
    python -m scripts.migrate_strategies
"""
import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.investment_strategy import InvestmentStrategy


# 전략별 기본 백테스트 설정 생성
def create_backtest_config(strategy_id: str, conditions: list) -> dict:
    """
    각 전략에 대한 기본 백테스트 설정 생성

    Args:
        strategy_id: 전략 ID
        conditions: UI 표시용 조건 배열

    Returns:
        BacktestRunRequest 형식의 설정 딕셔너리
    """
    # 공통 기본 설정
    # ✅ 성능 최적화: 시총 상위 300종목으로 제한 (전체 2645 → 300)
    base_config = {
        "strategy_name": strategy_id,
        "is_day_or_month": "D",  # 일봉 기준
        "commission_rate": 0.1,  # 0.1% 수수료
        "slippage": 0,  # 0% 슬리피지
        "buy_logic": "and",  # 매수 조건 AND 결합
        "priority_factor": "market_cap",  # 시가총액 우선순위
        "priority_order": "desc",
        "per_stock_ratio": 10,  # 종목당 10% 투자
        "max_holdings": 10,  # 최대 10개 종목 보유
        "max_buy_value": None,
        "max_daily_stock": None,
        "buy_price_basis": "close",  # 종가 기준
        "buy_price_offset": 0,
        "trade_targets": {
            "use_all_stocks": False,  # 전체 종목 사용 안 함
            "selected_universes": ["KOSPI", "KOSDAQ"],
            "selected_themes": [
                "전기 / 전자",
                "화학",
                "은행",
                "증권",
                "통신",
                "IT서비스",
                "음식료 / 담배",
                "제약",
                "건설",
                "유통"
            ],  # 주요 테마 10개 선택 (약 300-400 종목)
            "selected_stocks": []
        },
        "buy_conditions": [],
        "target_and_loss": None,
        "hold_days": None,
        "condition_sell": None,
    }

    # 전략별 특화 설정
    strategy_specific_configs = {
        "surge_stocks": {
            "buy_conditions": [
                {"name": "시가총액", "exp_left_side": "market_cap", "inequality": ">", "exp_right_side": 10000000000}
            ],
            "priority_factor": "change_rate",
            "priority_order": "desc",
            "per_stock_ratio": 20,
            "max_holdings": 5,
            # 급등주 전략: 거래량 많은 주요 테마 (변동성 높은 업종)
            "trade_targets": {
                "use_all_stocks": False,
                "selected_universes": ["KOSPI", "KOSDAQ"],
                "selected_themes": ["전기 / 전자", "제약", "IT서비스", "기계 / 장비", "화학"],
                "selected_stocks": []
            },
        },
        "steady_growth": {
            "buy_conditions": [
                {"name": "매출 CAGR", "exp_left_side": "revenue_cagr_3y", "inequality": ">", "exp_right_side": 0},
                {"name": "영업이익 CAGR", "exp_left_side": "operating_profit_cagr_3y", "inequality": ">", "exp_right_side": 0},
                {"name": "부채비율", "exp_left_side": "debt_ratio", "inequality": "<", "exp_right_side": 100},
                {"name": "ROE", "exp_left_side": "roe", "inequality": ">", "exp_right_side": 10}
            ],
            "priority_factor": "roe",
        },
        "benjamin_graham": {
            "buy_conditions": [
                {"name": "유동비율", "exp_left_side": "current_ratio", "inequality": ">", "exp_right_side": 200},
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 15}
            ],
            "priority_factor": "pbr",
            "priority_order": "asc",
        },
        "peter_lynch": {
            "buy_conditions": [
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 30},
                {"name": "PEG", "exp_left_side": "peg", "inequality": "<", "exp_right_side": 1.8},
                {"name": "PEG", "exp_left_side": "peg", "inequality": ">", "exp_right_side": 0},
                {"name": "부채비율", "exp_left_side": "debt_ratio", "inequality": "<", "exp_right_side": 150},
                {"name": "ROE", "exp_left_side": "roe", "inequality": ">", "exp_right_side": 5}
            ],
            "priority_factor": "peg",
            "priority_order": "asc",
        },
        "warren_buffett": {
            "buy_conditions": [
                {"name": "ROE", "exp_left_side": "roe", "inequality": ">", "exp_right_side": 15},
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 17},
                {"name": "PBR", "exp_left_side": "pbr", "inequality": "<", "exp_right_side": 1.5},
                {"name": "부채비율", "exp_left_side": "debt_ratio", "inequality": "<", "exp_right_side": 150}
            ],
            "priority_factor": "pbr",
            "priority_order": "asc",
        },
        "william_oneil": {
            "buy_conditions": [
                {"name": "EPS 성장률", "exp_left_side": "eps_growth", "inequality": ">", "exp_right_side": 18},
                {"name": "ROE", "exp_left_side": "roe", "inequality": ">", "exp_right_side": 17}
            ],
            "priority_factor": "eps_growth",
            "priority_order": "desc",
            "per_stock_ratio": 15,
            "max_holdings": 6,
        },
        "bill_ackman": {
            "buy_conditions": [
                {"name": "ROIC", "exp_left_side": "roic", "inequality": ">", "exp_right_side": 13},
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 20},
                {"name": "PBR", "exp_left_side": "pbr", "inequality": "<", "exp_right_side": 2}
            ],
            "priority_factor": "roic",
            "priority_order": "desc",
        },
        "charlie_munger": {
            "buy_conditions": [
                {"name": "ROIC", "exp_left_side": "roic", "inequality": ">", "exp_right_side": 15},
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 10},
                {"name": "PBR", "exp_left_side": "pbr", "inequality": "<", "exp_right_side": 1.5},
                {"name": "ROE", "exp_left_side": "roe", "inequality": ">", "exp_right_side": 15}
            ],
            "priority_factor": "roic",
            "priority_order": "desc",
        },
        "glenn_welling": {
            "buy_conditions": [
                {"name": "PBR", "exp_left_side": "pbr", "inequality": "<", "exp_right_side": 1.5},
                {"name": "PSR", "exp_left_side": "psr", "inequality": "<", "exp_right_side": 1.5}
            ],
            "priority_factor": "pbr",
            "priority_order": "asc",
        },
        "cathie_wood": {
            "buy_conditions": [
                {"name": "PEG", "exp_left_side": "peg", "inequality": "<", "exp_right_side": 2},
                {"name": "PEG", "exp_left_side": "peg", "inequality": ">", "exp_right_side": 0}
            ],
            "priority_factor": "revenue_growth",
            "priority_order": "desc",
        },
        "glenn_greenberg": {
            "buy_conditions": [
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 15},
                {"name": "ROIC", "exp_left_side": "roic", "inequality": ">", "exp_right_side": 15},
                {"name": "부채비율", "exp_left_side": "debt_ratio", "inequality": "<", "exp_right_side": 50}
            ],
            "priority_factor": "roic",
            "priority_order": "desc",
        },
        "undervalued_dividend": {
            "buy_conditions": [
                {"name": "PBR", "exp_left_side": "pbr", "inequality": "<", "exp_right_side": 1},
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 20}
            ],
            "priority_factor": "dividend_yield",
            "priority_order": "desc",
        },
        "long_term_dividend": {
            "buy_conditions": [
                {"name": "PER", "exp_left_side": "per", "inequality": "<", "exp_right_side": 20},
                {"name": "PBR", "exp_left_side": "pbr", "inequality": "<", "exp_right_side": 1.5},
                {"name": "부채비율", "exp_left_side": "debt_ratio", "inequality": "<", "exp_right_side": 66}
            ],
            "priority_factor": "dividend_yield",
            "priority_order": "desc",
        },
    }

    # 전략별 설정 병합
    config = base_config.copy()
    if strategy_id in strategy_specific_configs:
        config.update(strategy_specific_configs[strategy_id])

    return config


async def migrate_strategies():
    """JSON 파일에서 전략 데이터를 읽어 데이터베이스에 삽입"""

    # JSON 파일 경로 (Docker 환경 고려)
    import os
    if os.path.exists("/tmp/investmentStrategies.json"):
        json_path = Path("/tmp/investmentStrategies.json")
    else:
        json_path = project_root.parent / "SL-Front-End" / "src" / "data" / "investmentStrategies.json"

    if not json_path.exists():
        print(f"❌ JSON 파일을 찾을 수 없습니다: {json_path}")
        return

    # JSON 파일 읽기
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    strategies_data = data.get("strategies", [])
    print(f"📄 {len(strategies_data)}개 전략 로드 완료")

    # 데이터베이스 세션
    async with AsyncSessionLocal() as db:
        inserted_count = 0
        updated_count = 0

        for strategy_data in strategies_data:
            strategy_id = strategy_data["id"]

            # 백테스트 설정 생성
            backtest_config = create_backtest_config(
                strategy_id,
                strategy_data.get("conditions", [])
            )

            # 기존 전략 확인
            result = await db.execute(
                text("SELECT id FROM investment_strategies WHERE id = :id"),
                {"id": strategy_id}
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 업데이트
                strategy = InvestmentStrategy(
                    id=strategy_id,
                    name=strategy_data["name"],
                    summary=strategy_data["summary"],
                    description=strategy_data.get("description", ""),
                    tags=strategy_data["tags"],
                    backtest_config=backtest_config,
                    display_conditions=strategy_data.get("conditions", []),
                    is_active=True,
                    popularity_score=0,
                )
                db.merge(strategy)
                updated_count += 1
                print(f"🔄 업데이트: {strategy_id} - {strategy_data['name']}")
            else:
                # 삽입
                strategy = InvestmentStrategy(
                    id=strategy_id,
                    name=strategy_data["name"],
                    summary=strategy_data["summary"],
                    description=strategy_data.get("description", ""),
                    tags=strategy_data["tags"],
                    backtest_config=backtest_config,
                    display_conditions=strategy_data.get("conditions", []),
                    is_active=True,
                    popularity_score=0,
                )
                db.add(strategy)
                inserted_count += 1
                print(f"✅ 삽입: {strategy_id} - {strategy_data['name']}")

        # 커밋
        await db.commit()

        print(f"\n{'='*60}")
        print(f"✅ 마이그레이션 완료")
        print(f"   - 새로 삽입: {inserted_count}개")
        print(f"   - 업데이트: {updated_count}개")
        print(f"   - 전체: {inserted_count + updated_count}개")
        print(f"{'='*60}")


if __name__ == "__main__":
    print("🚀 투자 전략 데이터 마이그레이션 시작...\n")
    asyncio.run(migrate_strategies())
