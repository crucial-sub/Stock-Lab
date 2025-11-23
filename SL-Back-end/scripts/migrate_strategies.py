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
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({MARKET_CAP})", "inequality": ">", "exp_right_side": 7000000000} # 시가총액 > 70억
            ],
            "priority_factor": "기본값({CHANGE_RATE})",
            "priority_order": "desc",
            "per_stock_ratio": 15,
            "max_holdings": 8,
            "max_buy_value": 50000000,
            "max_daily_stock": 5,
            # 급등주 전략: 거래량 많은 주요 테마 (변동성 높은 업종)
            "trade_targets": {
                "use_all_stocks": False,
                # 대형 변동성 테마 포함 (총 ~399종)
                "selected_themes": ["전기 / 전자", "증권"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 12,
                "stop_loss": 7
            },
            "hold_days": {
                "min_hold_days": 3,
                "max_hold_days": 15,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
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
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": ">", "exp_right_side": -5},  # 매출 성장률 완화
                {"name": "B", "exp_left_side": "기본값({OPERATING_INCOME_GROWTH_YOY})", "inequality": ">", "exp_right_side": -5},  # 영업이익 성장률 완화
                {"name": "C", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 120}, # 부채비율 < 120%
                {"name": "D", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 8} # ROE > 8%
            ],
            "priority_factor": "기본값({ROE})",
            "per_stock_ratio": 10,
            "max_holdings": 15,
            "max_buy_value": 70000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                # 방어적 업종 + 대형 IT 성장 (총 ~347종)
                "selected_themes": ["IT서비스", "전기 / 가스 / 수도", "음식료 / 담배"],
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
                "min_hold_days": 60,
                "max_hold_days": 360,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({ROE})", "inequality": "<", "exp_right_side": 5},
                    {"name": "B", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": "<", "exp_right_side": -10}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            # TODO: 매출 CAGR(3Y), 영업이익 CAGR(3Y) 구현 가능 여부 확인(계산 비용까지 포함해서)
        },
        "peter_lynch": {
            # 🚀 벡터화 평가 활성화: expression + conditions 형식
            "expression": "A and B and C and D and E and F",  # AND 로직
            "conditions": [
                {"id": "A", "factor": "PER", "operator": "<", "value": 40},  # PER < 40
                {"id": "B", "factor": "PEG", "operator": ">", "value": 0},   # PEG > 0
                {"id": "C", "factor": "PEG", "operator": "<", "value": 2.0}, # PEG < 2.0
                {"id": "D", "factor": "DEBT_RATIO", "operator": "<", "value": 180},  # 부채비율 < 180%
                {"id": "E", "factor": "ROE", "operator": ">", "value": 3},   # ROE > 3%
                {"id": "F", "factor": "ROA", "operator": ">", "value": 0.5}, # ROA > 0.5%
            ],
            # UI 표시용 (하위 호환성)
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 40},
                {"name": "B", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0},
                {"name": "C", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 2.0},
                {"name": "D", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 180},
                {"name": "E", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 3},
                {"name": "F", "exp_left_side": "기본값({ROA})", "inequality": ">", "exp_right_side": 0.5},
            ],
            "priority_factor": "기본값({PEG})",
            "priority_order": "asc",
            "per_stock_ratio": 8,
            "max_holdings": 18,
            "max_buy_value": 50000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                # 성장+소비 (총 ~303종)
                "selected_themes": ["IT서비스", "섬유 / 의류"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 25,
                "stop_loss": 15
            },
            "hold_days": {
                "min_hold_days": 90,
                "max_hold_days": 540,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                # 🚀 벡터화 평가 활성화: expression + conditions 형식
                "expression": "A or B",  # OR 로직
                "conditions": [
                    {"id": "A", "factor": "PEG", "operator": ">", "value": 2.5},  # PEG > 2.5
                    {"id": "B", "factor": "DEBT_RATIO", "operator": ">", "value": 200},  # 부채비율 > 200%
                ],
                # UI 표시용 (하위 호환성)
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
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 12}, # ROE > 12%
                # 장기부채비율 제외 (계산 불가)
                {"name": "B", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.2}, # 유동비율 > 1.2
                # FCF 제외 (계산 불가)
                {"name": "C", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20}, # PER < 20
                {"name": "D", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.0}, # PBR < 2.0
                {"name": "E", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 170}, # 부채비율 < 170%
                {"name": "F", "exp_left_side": "기본값({EARNINGS_GROWTH_1Y})", "inequality": ">", "exp_right_side": 5} # EPS(주당순이익) 성장률 > 5% 조건을 순이익증가율(1Y)로 대체
            ],
            "priority_factor": "기본값({PBR})",
            "priority_order": "asc",
            "per_stock_ratio": 8,
            "max_holdings": 15,
            "max_buy_value": 100000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                # 대형 IT + 전통 가치 (총 ~392종)
                "selected_themes": ["IT서비스", "금융", "전기 / 가스 / 수도", "보험"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 40,
                "stop_loss": 20
            },
            "hold_days": {
                "min_hold_days": 180,
                "max_hold_days": 720,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({PBR})", "inequality": ">", "exp_right_side": 2.5},
                    {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": "<", "exp_right_side": 8}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            # TODO: FCF, EPS 성장률 추가 (향후 구현)
        },
        "william_oneil": {
            "buy_conditions": [
                # EPS 성장률 (QoQ) 제외 (계산 불가)
                {"name": "A", "exp_left_side": "기본값({EARNINGS_GROWTH_1Y})", "inequality": ">", "exp_right_side": 12}, # EPS(주당순이익) 성장률 > 12% 조건을 순이익증가율(1Y)로 대체
                {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 12}, # ROE > 12%
                {"name": "C", "exp_left_side": "기본값({DISTANCE_FROM_52W_HIGH})", "inequality": ">", "exp_right_side": -25} # 현재가 > 52주 신고가의 75% (팩터 검증 필요)
            ],
            "priority_factor": "기본값({EARNINGS_GROWTH_1Y})",
            "priority_order": "desc",
            "per_stock_ratio": 12,
            "max_holdings": 8,
            "max_buy_value": 50000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                # 고성장 대형 모멘텀 (총 ~395종)
                "selected_themes": ["전기 / 전자", "통신"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 28,
                "stop_loss": 12
            },
            "hold_days": {
                "min_hold_days": 20,
                "max_hold_days": 180,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({DISTANCE_FROM_52W_HIGH})", "inequality": "<", "exp_right_side": -35}
                ],
                "sell_logic": "A",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            # TODO: EPS 성장률 (QoQ) 추가 (향후 구현)
        },
        "bill_ackman": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": ">", "exp_right_side": 10}, # ROIC > 10%
                {"name": "B", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 22}, # PER < 22
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.5}, # PBR < 2.5
                {"name": "D", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 100}, # 부채비율 > 100%
                # FCF 조건 제외 (계산 불가)
                # 배당수익률 조건 제외  (계산 불가)
            ],
            "priority_factor": "기본값({ROIC})",
            "priority_order": "asc",
            "per_stock_ratio": 10,
            "max_holdings": 10,
            "max_buy_value": 100000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                # 리레이팅 대상 업종 (총 ~386종)
                "selected_themes": ["IT서비스", "금융", "증권"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 30,
                "stop_loss": 15
            },
            "hold_days": {
                "min_hold_days": 90,
                "max_hold_days": 360,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({PER})", "inequality": ">", "exp_right_side": 25},
                    {"name": "B", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 5}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            # TODO: FCF 추가 (향후 구현)
        },
        "charlie_munger": {
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": ">", "exp_right_side": 12}, # ROIC > 12%
                {"name": "B", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 14}, # PER < 14
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.0}, # PBR < 2.0
                {"name": "D", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 12}, # ROE > 12
                {"name": "E", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": ">", "exp_right_side": 10}, # 매출 성장률 > 10%
                {"name": "F", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 70}, # 부채비율 < 70%
                {"name": "G", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.5} # 유동비율 > 1.5
            ],
            "priority_factor": "기본값({ROIC})",
            "priority_order": "desc",
            "per_stock_ratio": 10,
            "max_holdings": 12,
            "max_buy_value": 80000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                # 고품질 소재/제조 (총 ~277종)
                "selected_themes": ["화학", "비금속", "전기 / 가스 / 수도"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 35,
                "stop_loss": 18
            },
            "hold_days": {
                "min_hold_days": 180,
                "max_hold_days": 900,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
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
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({EV_EBITDA})", "inequality": "<", "exp_right_side": 10}, # EV/EBITDA < 10
                {"name": "B", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 12}, # ROIC < 12%
                {"name": "C", "exp_left_side": "기본값({PBR})", "inequality": "<", "exp_right_side": 2.0}, # PBR < 2.0
                {"name": "D", "exp_left_side": "기본값({PSR})", "inequality": "<", "exp_right_side": 2.0}, # PSR < 2.0
                {"name": "E", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0}, #PEG > 0
                {"name": "F", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 1.2}, #PEG < 1.2
            ],
            "priority_factor": "기본값({EV_EBITDA})",
            "priority_order": "asc",
            "per_stock_ratio": 10,
            "max_holdings": 12,
            "max_buy_value": 70000000,
            "max_daily_stock": 3,
            "trade_targets": {
                "use_all_stocks": False,
                # 스핀오프/턴어라운드 중소형 제조 (총 ~275종)
                "selected_themes": ["기계 / 장비", "기타 제조", "비금속"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 25,
                "stop_loss": 15
            },
            "hold_days": {
                "min_hold_days": 120,
                "max_hold_days": 540,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
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
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0}, #PEG > 0
                {"name": "B", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 2.5}, #PEG < 2.5
                {"name": "C", "exp_left_side": "기본값({PSR})", "inequality": "<", "exp_right_side": 25}, # PSR < 25
                {"name": "D", "exp_left_side": "기본값({REVENUE_GROWTH_1Y})", "inequality": ">", "exp_right_side": 15}, # 매출 성장률 > 15%
                {"name": "E", "exp_left_side": "기본값({CURRENT_RATIO})", "inequality": ">", "exp_right_side": 1.5} # 유동비율 > 1.5
            ],
            "priority_factor": "기본값({REVENUE_GROWTH_1Y})",
            "priority_order": "desc",
            "per_stock_ratio": 8,
            "max_holdings": 14,
            "max_buy_value": 60000000,
            "max_daily_stock": 4,
            "trade_targets": {
                "use_all_stocks": False,
                # 대형 혁신/헬스케어 (총 ~395종)
                "selected_themes": ["전기 / 전자", "통신"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 40,
                "stop_loss": 20
            },
            "hold_days": {
                "min_hold_days": 90,
                "max_hold_days": 360,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
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
            "buy_conditions": [
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 20}, # PER < 20
                {"name": "B", "exp_left_side": "기본값({ROIC})", "inequality": ">", "exp_right_side": 12}, # ROIC > 12%
                {"name": "C", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 70}, # 부채비율 < 70%
                # 총 마진 성장률 조건 제외 (계산 불가)
                # FCF 조건 제외 (계산 불가)
            ],
            "priority_factor": "기본값({ROIC})",
            "priority_order": "desc",
            "per_stock_ratio": 10,
            "max_holdings": 8,
            "max_buy_value": 100000000,
            "max_daily_stock": 2,
            "trade_targets": {
                "use_all_stocks": False,
                # 소수 집중 가치 업종 (총 ~190종)
                "selected_themes": ["유통", "증권", "은행"],
                "selected_stocks": [],
                "selected_stock_count": None,
                "total_stock_count": 2645,
                "total_theme_count": 29
            },
            "target_and_loss": {
                "target_gain": 30,
                "stop_loss": 15
            },
            "hold_days": {
                "min_hold_days": 120,
                "max_hold_days": 540,
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            "condition_sell": {
                "sell_conditions": [
                    {"name": "A", "exp_left_side": "기본값({ROIC})", "inequality": "<", "exp_right_side": 8},
                    {"name": "B", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 90}
                ],
                "sell_logic": "or",
                "sell_price_basis": "전일 종가",
                "sell_price_offset": 0
            },
            # TODO: 총 마진 성장률, FCF 추가 (향후 구현)
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
