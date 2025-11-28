"""
조건식 분석 및 팩터 의존성 추출
- 조건식을 파싱하여 사용되는 팩터 추출
- 불필요한 팩터 계산 스킵
"""

import re
from typing import Set, List, Dict, Optional, Any
from app.schemas.backtest import BacktestCondition
import logging

logger = logging.getLogger(__name__)


class FactorDependencyAnalyzer:
    """팩터 의존성 분석기"""

    # 모든 가능한 팩터 목록 (148개+)
    ALL_FACTORS = {
        # Valuation Factors
        'PER', 'PBR', 'PSR', 'PCR', 'PEG', 'EV_EBITDA', 'EV_SALES', 'EV_FCF',
        'DIVIDEND_YIELD', 'EARNINGS_YIELD', 'FCF_YIELD', 'BOOK_TO_MARKET',
        'CAPE_RATIO', 'PTBV', 'GRAHAM_NUMBER', 'GREENBLATT_RANK', 'MAGIC_FORMULA',
        'PRICE_TO_FCF', 'PS_RATIO', 'ENTERPRISE_YIELD', 'EV',

        # Profitability Factors
        'ROE', 'ROA', 'ROIC', 'GPM', 'OPM', 'NPM', 'OPERATING_MARGIN', 'NET_MARGIN',
        'EBITDA_MARGIN', 'DUPONT_ROE', 'EARNINGS_QUALITY',

        # Efficiency/Turnover Factors
        'ASSET_TURNOVER', 'INVENTORY_TURNOVER', 'RECEIVABLES_TURNOVER',
        'FIXED_ASSET_TURNOVER', 'WORKING_CAPITAL_TURNOVER',

        # Liquidity/Solvency Factors
        'CURRENT_RATIO', 'QUICK_RATIO', 'CASH_RATIO', 'DEBT_RATIO', 'DEBT_TO_EQUITY',
        'EQUITY_RATIO', 'INTEREST_COVERAGE', 'WORKING_CAPITAL_RATIO',
        'EQUITY_MULTIPLIER', 'FINANCIAL_LEVERAGE', 'DEBTRATIO',

        # Cash Flow Factors
        'OCF_RATIO', 'FREE_CASH_FLOW', 'FCF_MARGIN', 'FCF_TO_SALES',
        'CAPEX_TO_OCF', 'CAPEX_TO_SALES', 'CFI_TO_ASSETS', 'CFO_TO_SALES',
        'CFF_RATIO', 'CASH_CONVERSION_EFFICIENCY',

        # Growth Factors
        'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'REVENUE_GROWTH_YOY', 'REVENUE_GROWTH_QOQ',
        'EARNINGS_GROWTH_1Y', 'EARNINGS_GROWTH_3Y', 'EARNINGS_GROWTH_YOY',
        'OPERATING_INCOME_GROWTH', 'OPERATING_INCOME_GROWTH_YOY',
        'GROSS_PROFIT_GROWTH', 'OCF_GROWTH_1Y', 'BOOK_VALUE_GROWTH_1Y',
        'ASSET_GROWTH_1Y', 'ASSET_GROWTH_YOY', 'EPS_GROWTH_YOY',
        'NET_INCOME_GROWTH_YOY', 'SUSTAINABLE_GROWTH_RATE',
        'REVENUE_GROWTH', 'EARNINGS_GROWTH',

        # Quality/Score Factors
        'QUALITY_SCORE', 'PROFITABILITY_SCORE', 'STABILITY_SCORE',
        'PIOTROSKI_F_SCORE', 'ALTMAN_Z_SCORE', 'ZMIJEWSKI_SCORE',
        'ASSET_QUALITY', 'ACCRUALS_RATIO',

        # Dividend Factors
        'DIVIDENDYIELD', 'DIVIDEND_GROWTH_3Y', 'DIVIDEND_GROWTH_YOY',
        'SHAREHOLDER_YIELD',

        # Market/Size Factors
        'MARKET_CAP',

        # Momentum/Technical Factors (price-based)
        'RETURN_1M', 'RETURN_3M', 'RETURN_6M', 'RETURN_12M', 'RET_3D', 'RET_8D',
        'MOMENTUM_20D', 'MOMENTUM_60D', 'RELATIVE_STRENGTH', 'VOLUME_MOMENTUM',
        'RSI', 'RSI_14', 'MACD', 'MACD_SIGNAL', 'STOCHASTIC_K', 'STOCHASTIC_D',
        'MA_5', 'MA_10', 'MA_20', 'MA_50', 'MA_60', 'MA_120', 'MA_200',
        'EMA_12', 'EMA_26', 'BOLLINGER_UPPER', 'BOLLINGER_LOWER', 'BOLLINGER_WIDTH',
        'SMA',

        # Volatility/Risk Factors
        'VOLATILITY_20D', 'VOLATILITY_60D', 'VOLATILITY_90D',
        'HISTORICAL_VOLATILITY_20', 'HISTORICAL_VOLATILITY_60',
        'PARKINSON_VOLATILITY', 'DOWNSIDE_VOLATILITY',
        'MAX_DRAWDOWN', 'BETA', 'SHARPE_RATIO', 'SORTINO_RATIO',

        # Volume/Microstructure Factors
        'VOLUME_RATIO_20D', 'AMIHUD_ILLIQUIDITY', 'EASE_OF_MOVEMENT',
        'FORCE_INDEX', 'INTRADAY_VOLATILITY', 'VOLUME_PRICE_TREND',

        # Position Factors
        'DAYS_FROM_52W_HIGH', 'DAYS_FROM_52W_LOW', 'WEEK_52_POSITION',

        # Additional Factors
        'OPERATING_LEVERAGE', 'REINVESTMENT_RATE', 'PEG_RATIO',
    }

    # 조건 연산자 (팩터가 아님)
    OPERATORS = {'AND', 'OR', 'NOT', 'TRUE', 'FALSE'}

    # 숫자 패턴 (팩터가 아님)
    NUMBER_PATTERN = re.compile(r'^-?\d+(\.\d+)?$')

    @staticmethod
    def extract_factors_from_conditions(
        conditions: Optional[List[Any]] = None,
        buy_expression: Optional[Dict[str, Any]] = None
    ) -> Set[str]:
        """
        조건식에서 사용되는 팩터 추출

        Args:
            conditions: 백테스트 조건 리스트 (기존 방식)
            buy_expression: 논리식 조건 (새로운 방식)

        Returns:
            사용되는 팩터 집합
        """
        required_factors = set()

        # 1. 기존 방식 조건에서 팩터 추출
        if conditions:
            for condition in conditions:
                # Dict 형태로 전달되는 경우
                if isinstance(condition, dict):
                    factor_name = condition.get('factor')
                    if factor_name:
                        required_factors.add(factor_name.upper())
                    # 🔥 FIX: exp_left_side에서 팩터명 추출 (예: "기본값({PER})" → "PER")
                    elif 'exp_left_side' in condition:
                        exp_left = condition.get('exp_left_side', '')
                        # {FACTOR_NAME} 패턴 추출
                        import re
                        match = re.search(r'\{([^}]+)\}', exp_left)
                        if match:
                            extracted_factor = match.group(1).upper()
                            required_factors.add(extracted_factor)
                            logger.debug(f"exp_left_side에서 팩터 추출: {extracted_factor}")
                # Pydantic 모델인 경우
                elif hasattr(condition, 'factor'):
                    if condition.factor:
                        required_factors.add(condition.factor.upper())
                    # 🔥 FIX: exp_left_side에서도 추출
                    elif hasattr(condition, 'exp_left_side') and condition.exp_left_side:
                        import re
                        match = re.search(r'\{([^}]+)\}', condition.exp_left_side)
                        if match:
                            extracted_factor = match.group(1).upper()
                            required_factors.add(extracted_factor)

        # 2. 논리식 조건에서 팩터 추출
        if buy_expression:
            # 논리식에서 팩터 추출
            if isinstance(buy_expression, dict):
                expression = buy_expression.get('expression', '')
                conditions_list = buy_expression.get('conditions', [])
            else:
                expression = getattr(buy_expression, 'expression', '')
                conditions_list = getattr(buy_expression, 'conditions', [])

            # expression 파싱
            if expression:
                factors = FactorDependencyAnalyzer._extract_factors_from_expression(expression)
                required_factors.update(factors)

            # conditions 리스트에서 팩터 추출
            if conditions_list:
                for cond in conditions_list:
                    if isinstance(cond, dict):
                        factor_name = cond.get('factor')
                    else:
                        factor_name = getattr(cond, 'factor', None)

                    if factor_name:
                        required_factors.add(factor_name.upper())

        logger.info(f"📊 조건식 분석: {len(required_factors)}개 팩터 필요 (전체 {len(FactorDependencyAnalyzer.ALL_FACTORS)}개 중)")
        if required_factors:
            logger.debug(f"필요 팩터: {sorted(required_factors)}")
        else:
            logger.warning("⚠️ 조건식에서 팩터를 추출하지 못했습니다. 모든 팩터를 계산합니다.")

        return required_factors

    @staticmethod
    def _extract_factors_from_expression(expression: str) -> Set[str]:
        """
        표현식에서 팩터명 추출

        Args:
            expression: 논리식 (예: "(PER < 10 and PBR < 1) or ROE > 15")

        Returns:
            팩터명 집합
        """
        factors = set()

        # 정규식으로 팩터명 추출 (대문자로 시작하는 단어)
        # 패턴: 대문자 + (대문자/숫자/언더스코어)*
        pattern = r'\b([A-Z][A-Z0-9_]*)\b'
        matches = re.findall(pattern, expression.upper())

        for match in matches:
            # 연산자 제외
            if match in FactorDependencyAnalyzer.OPERATORS:
                continue

            # 숫자 제외
            if FactorDependencyAnalyzer.NUMBER_PATTERN.match(match):
                continue

            # 실제 팩터인지 확인
            if match in FactorDependencyAnalyzer.ALL_FACTORS:
                factors.add(match)
            else:
                # 알려지지 않은 팩터 (새로 추가된 팩터일 수 있음)
                logger.debug(f"알 수 없는 팩터: {match} (계산 대상에 포함)")
                factors.add(match)

        return factors

    @staticmethod
    def get_factor_compute_mask(required_factors: Optional[Set[str]] = None) -> Dict[str, bool]:
        """
        팩터 계산 마스크 생성

        Args:
            required_factors: 필요한 팩터 집합 (None이면 모든 팩터 계산)

        Returns:
            {'PER': True, 'PBR': False, ...}
        """
        # required_factors가 None이거나 비어있으면 모든 팩터 계산
        if not required_factors:
            logger.info("필요 팩터가 없음 → 모든 팩터 계산")
            return {factor: True for factor in FactorDependencyAnalyzer.ALL_FACTORS}

        # 마스크 생성
        mask = {
            factor: (factor in required_factors)
            for factor in FactorDependencyAnalyzer.ALL_FACTORS
        }

        # 통계 출력
        enabled_count = sum(1 for v in mask.values() if v)
        logger.info(f"✅ 팩터 계산 마스크 생성: {enabled_count}/{len(mask)}개 팩터 활성화")

        return mask

    @staticmethod
    def analyze_condition_complexity(
        conditions: Optional[List[Any]] = None,
        buy_expression: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        조건식의 복잡도 분석

        Returns:
            {
                'factor_count': int,
                'condition_count': int,
                'has_logical_expression': bool,
                'estimated_speedup': float  # 예상 속도 향상 배수
            }
        """
        required_factors = FactorDependencyAnalyzer.extract_factors_from_conditions(
            conditions, buy_expression
        )

        total_factors = len(FactorDependencyAnalyzer.ALL_FACTORS)
        used_factors = len(required_factors) if required_factors else total_factors

        # 예상 속도 향상 계산
        # (계산 안 하는 팩터 비율에 비례)
        speedup = total_factors / max(used_factors, 1)

        return {
            'factor_count': used_factors,
            'total_factors': total_factors,
            'condition_count': len(conditions) if conditions else 0,
            'has_logical_expression': buy_expression is not None,
            'estimated_speedup': round(speedup, 2),
            'optimization_enabled': used_factors < total_factors
        }


# 싱글톤 인스턴스
factor_analyzer = FactorDependencyAnalyzer()
