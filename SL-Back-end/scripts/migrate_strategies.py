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
    # ✅ 프론트엔드 양식과 일치하도록 수정 (2025-11-21)
    base_config = {
        "strategy_name": strategy_id,
        "is_day_or_month": "daily",  # "D" → "daily" (프론트엔드 양식)
        "commission_rate": 0.1,  # 0.1% 수수료
        "slippage": 0,  # 0% 슬리피지
        "buy_logic": "and",  # 매수 조건 AND 결합
        "priority_factor": "기본값({market_cap})",  # 서브팩터 포함 양식
        "priority_order": "desc",
        "per_stock_ratio": 10,  # 종목당 10% 투자
        "max_holdings": 10,  # 최대 10개 종목 보유
        "max_buy_value": None,
        "max_daily_stock": None,
        "buy_price_basis": "전일 종가",  # "close" → "전일 종가" (프론트엔드 양식)
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
            "selected_stocks": [],
            "selected_stock_count": None,  # 런타임에 계산됨
            "total_stock_count": 2645,      # 전체 종목 수
            "total_theme_count": 29         # 전체 테마 수
        },
        "buy_conditions": [],
        "target_and_loss": {               # 구조 추가
            "target_gain": None,
            "stop_loss": None
        },
        "hold_days": None,
        "condition_sell": None,
    }

    # 전략별 특화 설정
    strategy_specific_configs = {
        "surge_stocks": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({MARKET_CAP})", "inequality": ">", "exp_right_side": 10000000000}
            ],
            "priority_factor": "기본값({CHANGE_RATE})",
            "priority_order": "desc",
            "per_stock_ratio": 20,
            "max_holdings": 5,
            # 급등주 전략: 거래량 많은 주요 테마 (변동성 높은 업종)
            "trade_targets": {
                "use_all_stocks": False,
                "selected_universes": ["KOSPI", "KOSDAQ"],
                "selected_themes": ["전기 / 전자", "제약", "IT서비스", "기계 / 장비", "화학"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
        },
        "steady_growth": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({REVENUE_GROWTH_3Y})", "inequality": ">", "exp_right_side": 0},
                {"name": "B", "exp_left_side": "기본값({OPERATING_INCOME_GROWTH})", "inequality": ">", "exp_right_side": 0},  # 1Y로 대체
                {"name": "C", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 100},
                {"name": "D", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 10}
            ],
            "priority_factor": "기본값({ROE})",
            # TODO: 영업이익 CAGR 3Y 계산 함수 추가 필요
        },
        "benjamin_graham": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 2.0},  # 200% = 2.0
                {"name": "B", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 15}
            ],
            "priority_factor": "기본값({PBR})",
            "priority_order": "asc",
            # TODO: 순유동자산, 장기부채, EPS 5년 성장률, 연속 흑자 조건 추가 (향후 구현)
        },
        "peter_lynch": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 30},
                # PEG 조건 제외 (계산 불가)
                # 재고/매출 조건 제외 (계산 불가)
                {"name": "B", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 150},
                {"name": "C", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 5},
                {"name": "D", "exp_left_side": "기본값({ROA})", "inequality": ">", "exp_right_side": 1},
                {"name": "E", "exp_left_side": "기본값({DIVIDEND_YIELD})", "inequality": ">", "exp_right_side": 3}
            ],
            "priority_factor": "기본값({PER})",  # PEG 대신 PER 사용
            "priority_order": "asc",
            # TODO: PEG, 재고/매출 비율 추가 (향후 구현)
        },
        "warren_buffett": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 15},
                # 장기부채비율 제외 (계산 불가)
                {"name": "B", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.5},
                {"name": "C", "exp_left_side": "기본값({FCF_YIELD})", "inequality": ">", "exp_right_side": 0},  # FCF > 0 대체
                {"name": "D", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 17},
                {"name": "E", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 1.5},
                {"name": "F", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 150},
                {"name": "G", "exp_left_side": "기본값({EARNINGS_GROWTH})", "inequality": ">", "exp_right_side": 10}
            ],
            "priority_factor": "기본값({PBR})",
            "priority_order": "asc",
            # TODO: 장기부채비율 추가 (향후 구현)
        },
        "william_oneil": {
            "buy_conditions": [
                # QoQ 성장률 제외 (계산 불가)
                {"name": "A", "exp_left_side": "기본값({EARNINGS_GROWTH})", "inequality": ">", "exp_right_side": 18},
                {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 17}
                # 52주 신고가 조건 제외 (계산 불가)
            ],
            "priority_factor": "기본값({EARNINGS_GROWTH})",
            "priority_order": "desc",
            "per_stock_ratio": 15,
            "max_holdings": 6,
            # TODO: QoQ 성장률, 52주 신고가 비율 추가 (향후 구현)
        },
        "bill_ackman": {
            "buy_conditions": [
                # ROIC 제외 (계산 불가)
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20},
                {"name": "B", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2},
                {"name": "C", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 150},
                {"name": "D", "exp_left_side": "기본값({FCF_YIELD})", "inequality": ">", "exp_right_side": 0},
                {"name": "E", "exp_left_side": "기본값({DIVIDEND_YIELD})", "inequality": ">", "exp_right_side": 2}
            ],
            "priority_factor": "기본값({PER})",  # ROIC 대신 PER 사용
            "priority_order": "asc",
            # TODO: ROIC 추가 (향후 구현)
        },
        "charlie_munger": {
            "buy_conditions": [
                # ROIC 제외 (계산 불가)
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 10},
                {"name": "B", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 1.5},
                {"name": "C", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 15},
                {"name": "D", "exp_left_side": "기본값({REVENUE_GROWTH})", "inequality": ">", "exp_right_side": 15},
                {"name": "E", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 50},
                {"name": "F", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 2}
            ],
            "priority_factor": "기본값({ROE})",  # ROIC 대신 ROE 사용
            "priority_order": "desc",
            # TODO: ROIC 추가 (향후 구현)
        },
        "glenn_welling": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({EV_EBITDA})", "inequality": "<", "exp_right_side": 8},
                # ROIC 제외 (계산 불가)
                {"name": "B", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 1.5},
                {"name": "C", "exp_left_side": "기본값({PSR})", "inequality": "<", "exp_right_side": 1.5}
                # PEG 제외 (계산 불가)
            ],
            "priority_factor": "기본값({PBR})",
            "priority_order": "asc",
            # TODO: ROIC, PEG 추가 (향후 구현)
        },
        "cathie_wood": {
            "buy_conditions": [
                # PEG 제외 (계산 불가)
                {"name": "A", "exp_left_side": "기본값({PSR})", "inequality": "<", "exp_right_side": 20},
                {"name": "B", "exp_left_side": "기본값({REVENUE_GROWTH})", "inequality": ">", "exp_right_side": 20},
                {"name": "C", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 2}
            ],
            "priority_factor": "기본값({REVENUE_GROWTH})",
            "priority_order": "desc",
            # TODO: PEG 추가 (향후 구현)
        },
        "glenn_greenberg": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 15},
                # ROIC 제외 (계산 불가)
                {"name": "B", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 50},
                {"name": "C", "exp_left_side": "기본값({GROSS_PROFIT_GROWTH})", "inequality": ">", "exp_right_side": 3},
                {"name": "D", "exp_left_side": "기본값({FCF_YIELD})", "inequality": ">", "exp_right_side": 5}
            ],
            "priority_factor": "기본값({FCF_YIELD})",  # ROIC 대신 FCF_YIELD 사용
            "priority_order": "desc",
            # TODO: ROIC 추가 (향후 구현)
        },
        "undervalued_dividend": {
            "buy_conditions": [
                # 배당수익률 5년 평균 비교 제외 (계산 불가)
                {"name": "A", "exp_left_side": "기본값({FCF_YIELD})", "inequality": ">", "exp_right_side": 0},
                {"name": "B", "exp_left_side": "기본값({EARNINGS_GROWTH})", "inequality": ">", "exp_right_side": 5},
                # 배당금 성장 연수 제외 (계산 불가)
                # 배당성향 제외 (계산 불가)
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 1},
                {"name": "D", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20}
            ],
            "priority_factor": "기본값({DIVIDEND_YIELD})",
            "priority_order": "desc",
            # TODO: 배당 관련 팩터들 추가 (향후 구현)
        },
        "long_term_dividend": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({DIVIDEND_YIELD})", "inequality": ">=", "exp_right_side": 4},
                {"name": "B", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20},
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 1.5},
                {"name": "D", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 66},
                {"name": "E", "exp_left_side": "기본값({OPERATING_INCOME_GROWTH})", "inequality": ">=", "exp_right_side": 3}
            ],
            "priority_factor": "기본값({DIVIDEND_YIELD})",
            "priority_order": "desc",
            # TODO: 영업이익 CAGR 3Y 추가 (향후 구현)
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
                await db.merge(strategy)
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
