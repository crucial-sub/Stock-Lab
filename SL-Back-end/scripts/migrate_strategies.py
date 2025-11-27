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
        "is_day_or_month": "daily",  # "daily"
        "commission_rate": 0.1,  # 0.1% 수수료
        "slippage": 0,  # 0% 슬리피지
        "buy_logic": "and",  # 매수 조건 AND 결합
        "priority_factor": "기본값({MARKET_CAP})",  # 서브팩터 포함 양식
        "priority_order": "desc",
        "per_stock_ratio": 10,  # 종목당 10% 투자
        "max_holdings": 10,  # 최대 10개 종목 보유
        "max_buy_value": None,
        "max_daily_stock": None,
        "buy_price_basis": "전일 종가",  # "전일 종가"
        "buy_price_offset": 0,
        "trade_targets": {
            "use_all_stocks": False,  # 전체 종목 사용 안 함
            "selected_universes": [], # 현재 안쓰는 속성이므로 절대 건들지 말것.
            "selected_themes": [],
            "selected_stocks": [],
            "selected_stock_count": None,  # 런타임에 계산됨
            "total_stock_count": 2645,      # 전체 종목 수
            "total_theme_count": 29         # 전체 테마 수
        },
        "buy_conditions": [],
        "target_and_loss": {
            "target_gain": None,
            "stop_loss": None
        },
        "hold_days": None,
        "condition_sell": None,
    }

    # 전략별 특화 설정
    strategy_specific_configs = {
        #! 기존 유명 전략 목록
        "surge_stocks": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨
            "expression": "A",
            "conditions": [
                {"id": "A", "factor": "MARKET_CAP", "operator": ">", "value": 7000000000},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({MARKET_CAP})", "inequality": ">", "exp_right_side": 7000000000}
            ],
            "priority_factor": "기본값({CHANGE_RATE})",
            "priority_order": "desc",
            "per_stock_ratio": 8,
            "max_holdings": 12,
            "max_buy_value": 20000000,
            "max_daily_stock": 5,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["전기 / 전자", "IT서비스", "의료 / 정밀기기", "오락 / 문화", "증권", "통신"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 8,
                "stop_loss": 5
            },
            "hold_days": {
                "min_hold_days": 3,
                "max_hold_days": 10,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "DISTANCE_FROM_52W_HIGH", "operator": "<", "value": -35},
                    {"id": "B", "factor": "CHANGE_RATE", "operator": "<", "value": -7},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({DISTANCE_FROM_52W_HIGH})", "inequality": "<", "exp_right_side": -35},
                    {"name": "B", "exp_left_side": "기본값({CHANGE_RATE})", "inequality": "<", "exp_right_side": -7}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            }
        },
        "steady_growth": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D)
            "expression": "A and B and C and D",
            "conditions": [
                {"id": "A", "factor": "REVENUE_GROWTH_1Y", "operator": ">", "value": -5},
                {"id": "B", "factor": "OPERATING_INCOME_GROWTH_YOY", "operator": ">", "value": -5},
                {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 120},
                {"id": "D", "factor": "ROE", "operator": ">", "value": 8},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": ">", "exp_right_side": -5},
                {"name": "B", "exp_left_side": "기본값({OPERATING_INCOME_GROWTH_YOY})", "inequality": ">", "exp_right_side": -5},
                {"name": "C", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 120},
                {"name": "D", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 8}
            ],
            "priority_factor": "기본값({ROE})",
            "per_stock_ratio": 4,
            "max_holdings": 15,
            "max_buy_value": 20000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["화학", "기계 / 장비", "유통", "음식료 / 담배", "건설", "섬유 / 의류", "운송장비 / 부품"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 12,
                "stop_loss": 8
            },
            "hold_days": {
                "min_hold_days": 60,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "ROE", "operator": "<", "value": 5},
                    {"id": "B", "factor": "REVENUE_GROWTH_1Y", "operator": "<", "value": -10},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({ROE})", "inequality": "<", "exp_right_side": 5},
                    {"name": "B", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": "<", "exp_right_side": -10}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "peter_lynch": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D and E and F)
            "expression": "A and B and C and D and E and F",
            "conditions": [
                {"id": "A", "factor": "PER", "operator": "<", "value": 40},
                {"id": "B", "factor": "PEG", "operator": ">", "value": 0},
                {"id": "C", "factor": "PEG", "operator": "<", "value": 2.0},
                {"id": "D", "factor": "DEBT_RATIO", "operator": "<", "value": 180},
                {"id": "E", "factor": "ROE", "operator": ">", "value": 3},
                {"id": "F", "factor": "ROA", "operator": ">", "value": 0.5},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 40},
                {"name": "B", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0},
                {"name": "C", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 2.0},
                {"name": "D", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 180},
                {"name": "E", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 3},
                {"name": "F", "exp_left_side": "기본값({ROA})", "inequality": ">", "exp_right_side": 0.5},
            ],
            "priority_factor": "기본값({PEG})",
            "priority_order": "desc",
            "per_stock_ratio": 4,
            "max_holdings": 15,
            "max_buy_value": 20000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["IT서비스", "일반 서비스", "유통", "금속", "의료 / 정밀기기", "음식료 / 담배"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 15,
                "stop_loss": 8
            },
            "hold_days": {
                "min_hold_days": 90,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "PEG", "operator": ">", "value": 2.5},
                    {"id": "B", "factor": "DEBT_RATIO", "operator": ">", "value": 200},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 2.5},
                    {"name": "B", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 200}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "warren_buffett": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D and E and F)
            "expression": "A and B and C and D and E and F",
            "conditions": [
                {"id": "A", "factor": "ROE", "operator": ">", "value": 12},
                {"id": "B", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.2},
                {"id": "C", "factor": "PER", "operator": "<", "value": 20},
                {"id": "D", "factor": "PBR", "operator": "<", "value": 2.0},
                {"id": "E", "factor": "DEBT_RATIO", "operator": "<", "value": 170},
                {"id": "F", "factor": "EARNINGS_GROWTH_1Y", "operator": ">", "value": 5},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 12},
                {"name": "B", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.2},
                {"name": "C", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20},
                {"name": "D", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.0},
                {"name": "E", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 170},
                {"name": "F", "exp_left_side": "기본값({EARNINGS_GROWTH_1Y})", "inequality": ">", "exp_right_side": 5}
            ],
            "priority_factor": "기본값({PBR})",
            "priority_order": "asc",
            "per_stock_ratio": 4,
            "max_holdings": 15,
            "max_buy_value": 20000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["전기 / 전자", "화학", "제약", "금융", "음식료 / 담배"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 20,
                "stop_loss": 10
            },
            "hold_days": {
                "min_hold_days": 180,
                "max_hold_days": 360,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "PBR", "operator": ">", "value": 2.5},
                    {"id": "B", "factor": "ROE", "operator": "<", "value": 8},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({PBR})", "inequality": ">", "exp_right_side": 2.5},
                    {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": "<", "exp_right_side": 8}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "william_oneil": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C)
            "expression": "A and B and C",
            "conditions": [
                {"id": "A", "factor": "EARNINGS_GROWTH_1Y", "operator": ">", "value": 12},
                {"id": "B", "factor": "ROE", "operator": ">", "value": 12},
                {"id": "C", "factor": "DISTANCE_FROM_52W_HIGH", "operator": ">", "value": -25},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({EARNINGS_GROWTH_1Y})", "inequality": ">", "exp_right_side": 12},
                {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 12},
                {"name": "C", "exp_left_side": "기본값({DISTANCE_FROM_52W_HIGH})", "inequality": ">", "exp_right_side": -25}
            ],
            "priority_factor": "기본값({EARNINGS_GROWTH_1Y})",
            "priority_order": "desc",
            "per_stock_ratio": 8,
            "max_holdings": 12,
            "max_buy_value": 20000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["전기 / 전자", "IT서비스", "의료 / 정밀기기", "일반 서비스", "오락 / 문화"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 18,
                "stop_loss": 7
            },
            "hold_days": {
                "min_hold_days": 20,
                "max_hold_days": 120,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A",
                "conditions": [
                    {"id": "A", "factor": "DISTANCE_FROM_52W_HIGH", "operator": "<", "value": -35},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({DISTANCE_FROM_52W_HIGH})", "inequality": "<", "exp_right_side": -35}
                ],
                "sell_logic": "A",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "bill_ackman": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D)
            "expression": "A and B and C and D",
            "conditions": [
                {"id": "A", "factor": "ROIC", "operator": ">", "value": 10},
                {"id": "B", "factor": "PER", "operator": "<", "value": 22},
                {"id": "C", "factor": "PBR", "operator": "<", "value": 2.5},
                {"id": "D", "factor": "DEBT_RATIO", "operator": ">", "value": 100},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": ">", "exp_right_side": 10},
                {"name": "B", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 22},
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.5},
                {"name": "D", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 100},
            ],
            "priority_factor": "기본값({ROIC})",
            "priority_order": "asc",
            "per_stock_ratio": 4,
            "max_holdings": 15,
            "max_buy_value": 20000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["화학", "기계 / 장비", "유통", "건설", "운송장비 / 부품", "기타 금융"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 18,
                "stop_loss": 10
            },
            "hold_days": {
                "min_hold_days": 90,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "PER", "operator": ">", "value": 25},
                    {"id": "B", "factor": "ROIC", "operator": "<", "value": 5},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({PER})", "inequality": ">", "exp_right_side": 25},
                    {"name": "B", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 5}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "charlie_munger": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D and E and F and G)
            "expression": "A and B and C and D and E and F and G",
            "conditions": [
                {"id": "A", "factor": "ROIC", "operator": ">", "value": 12},
                {"id": "B", "factor": "PER", "operator": "<", "value": 14},
                {"id": "C", "factor": "PBR", "operator": "<", "value": 2.0},
                {"id": "D", "factor": "ROE", "operator": ">", "value": 12},
                {"id": "E", "factor": "REVENUE_GROWTH_1Y", "operator": ">", "value": 10},
                {"id": "F", "factor": "DEBT_RATIO", "operator": "<", "value": 70},
                {"id": "G", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.5},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": ">", "exp_right_side": 12},
                {"name": "B", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 14},
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.0},
                {"name": "D", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 12},
                {"name": "E", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": ">", "exp_right_side": 10},
                {"name": "F", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 70},
                {"name": "G", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.5}
            ],
            "priority_factor": "기본값({ROIC})",
            "priority_order": "desc",
            "per_stock_ratio": 4,
            "max_holdings": 15,
            "max_buy_value": 20000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["화학", "제약", "음식료 / 담배", "유통", "금속", "일반 서비스"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 18,
                "stop_loss": 10
            },
            "hold_days": {
                "min_hold_days": 180,
                "max_hold_days": 360,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "ROIC", "operator": "<", "value": 8},
                    {"id": "B", "factor": "PBR", "operator": ">", "value": 2.3},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 8},
                    {"name": "B", "exp_left_side": "기본값({PBR})", "inequality": ">", "exp_right_side": 2.3}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "glenn_welling": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D and E and F)
            "expression": "A and B and C and D and E and F",
            "conditions": [
                {"id": "A", "factor": "EV_EBITDA", "operator": "<", "value": 10},
                {"id": "B", "factor": "ROIC", "operator": "<", "value": 12},
                {"id": "C", "factor": "PBR", "operator": "<", "value": 2.0},
                {"id": "D", "factor": "PSR", "operator": "<", "value": 2.0},
                {"id": "E", "factor": "PEG", "operator": ">", "value": 0},
                {"id": "F", "factor": "PEG", "operator": "<", "value": 1.2},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({EV_EBITDA})", "inequality": "<", "exp_right_side": 10},
                {"name": "B", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 12},
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.0},
                {"name": "D", "exp_left_side": "기본값({PSR})", "inequality": "<", "exp_right_side": 2.0},
                {"name": "E", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0},
                {"name": "F", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 1.2},
            ],
            "priority_factor": "기본값({EV_EBITDA})",
            "priority_order": "asc",
            "per_stock_ratio": 6,
            "max_holdings": 12,
            "max_buy_value": 20000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["IT서비스", "일반 서비스", "금융", "기타 금융", "유통", "금속", "건설"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 15,
                "stop_loss": 10
            },
            "hold_days": {
                "min_hold_days": 120,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "EV_EBITDA", "operator": ">", "value": 12},
                    {"id": "B", "factor": "PBR", "operator": ">", "value": 2.2},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({EV_EBITDA})", "inequality": ">", "exp_right_side": 12},
                    {"name": "B", "exp_left_side": "기본값({PBR})", "inequality": ">", "exp_right_side": 2.2}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "cathie_wood": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C and D and E)
            "expression": "A and B and C and D and E",
            "conditions": [
                {"id": "A", "factor": "PEG", "operator": ">", "value": 0},
                {"id": "B", "factor": "PEG", "operator": "<", "value": 3},
                {"id": "C", "factor": "PSR", "operator": "<", "value": 30},
                {"id": "D", "factor": "REVENUE_GROWTH_1Y", "operator": ">", "value": 10},
                {"id": "E", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.2},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0},
                {"name": "B", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 3},
                {"name": "C", "exp_left_side": "기본값({PSR})", "inequality": "<", "exp_right_side": 30},
                {"name": "D", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": ">", "exp_right_side": 10},
                {"name": "E", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.2}
            ],
            "priority_factor": "기본값({REVENUE_GROWTH_1Y})",
            "priority_order": "desc",
            "per_stock_ratio": 6,
            "max_holdings": 14,
            "max_buy_value": 20000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["전기 / 전자", "IT서비스", "의료 / 정밀기기", "제약", "오락 / 문화", "통신"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 20,
                "stop_loss": 12
            },
            "hold_days": {
                "min_hold_days": 90,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "PSR", "operator": ">", "value": 30},
                    {"id": "B", "factor": "REVENUE_GROWTH_1Y", "operator": "<", "value": 5},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({PSR})", "inequality": ">", "exp_right_side": 30},
                    {"name": "B", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": "<", "exp_right_side": 5}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        "glenn_greenberg": {
            # 🚀 벡터화 평가: buy_conditions와 동기화됨 (A and B and C)
            "expression": "A and B and C",
            "conditions": [
                {"id": "A", "factor": "PER", "operator": "<", "value": 20},
                {"id": "B", "factor": "ROIC", "operator": ">", "value": 12},
                {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 70},
            ],
            # UI 표시용
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20},
                {"name": "B", "exp_left_side": "기본값({ROIC})", "inequality": ">", "exp_right_side": 12},
                {"name": "C", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 70},
            ],
            "priority_factor": "기본값({ROIC})",
            "priority_order": "desc",
            "per_stock_ratio": 4,
            "max_holdings": 15,
            "max_buy_value": 20000000,
            "max_daily_stock": 2,
            "trade_targets": {
                "use_all_stocks": False,
                "selected_themes": ["화학", "금융", "유통", "일반 서비스", "음식료 / 담배", "제약"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 18,
                "stop_loss": 10
            },
            "hold_days": {
                "min_hold_days": 120,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가: sell_conditions와 동기화됨
                "expression": "A or B",
                "conditions": [
                    {"id": "A", "factor": "ROIC", "operator": "<", "value": 8},
                    {"id": "B", "factor": "DEBT_RATIO", "operator": ">", "value": 90},
                ],
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 8},
                    {"name": "B", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 90}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
        },
        #! 여기서부터는 추가 전략
        
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

            # 🔍 디버그: 피터린치 설정 확인
            if strategy_id == "peter_lynch":
                print("\n" + "=" * 80)
                print("🔍 디버그: 피터린치 backtest_config")
                print("=" * 80)
                print(f"expression: {backtest_config.get('expression')}")
                print(f"conditions: {backtest_config.get('conditions')}")
                print(f"buy_conditions (first 2): {backtest_config.get('buy_conditions', [])[:2]}")
                print("=" * 80 + "\n")

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
