"""
팩터 계산과 백테스트 엔진 연동 모듈
backtest.py와 factor_calculator_complete.py를 연결
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.factor_calculator_complete import CompleteFactorCalculator

try:
    from app.services.condition_evaluator_vectorized import VectorizedConditionEvaluator
    USE_VECTORIZED = True
    logger = logging.getLogger(__name__)
    logger.info("✅ 벡터화 조건 평가기 로드 완료")
except ImportError:
    from app.services.condition_evaluator import ConditionEvaluator
    USE_VECTORIZED = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ 벡터화 조건 평가기 없음 - 기본 모드 사용")


class FactorIntegration:
    """팩터와 백테스트 연동 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.factor_calculator = CompleteFactorCalculator(db)

        if USE_VECTORIZED:
            self.condition_evaluator = VectorizedConditionEvaluator()
            self.use_vectorized = True
        else:
            self.condition_evaluator = ConditionEvaluator()
            self.use_vectorized = False

    async def get_integrated_factor_data(
        self,
        start_date: date,
        end_date: date,
        stock_codes: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        백테스트 엔진에서 사용할 통합 팩터 데이터 생성

        Returns:
            DataFrame with columns:
            - date, stock_code, stock_name
            - 54개 팩터 값
            - 각 팩터의 _RANK 컬럼
        """
        logger.info(f"팩터 데이터 통합 시작: {start_date} ~ {end_date}")

        # 거래일 리스트 생성
        trading_days = pd.date_range(start_date, end_date, freq='B')

        all_factor_data = []

        for trading_day in trading_days:
            try:
                # 54개 팩터 모두 계산
                daily_factors = await self.factor_calculator.get_factor_data_for_date(
                    date=trading_day,
                    factor_names=None  # 모든 팩터
                )

                if not daily_factors.empty:
                    daily_factors['date'] = trading_day
                    all_factor_data.append(daily_factors)

            except Exception as e:
                logger.error(f"팩터 계산 실패 ({trading_day}): {e}")
                continue

        if not all_factor_data:
            logger.warning("팩터 데이터가 없습니다")
            return pd.DataFrame()

        # 모든 날짜 데이터 합치기
        factor_df = pd.concat(all_factor_data, ignore_index=True)

        # stock_codes 필터링 (제공된 경우)
        if stock_codes:
            factor_df = factor_df[factor_df['stock_code'].isin(stock_codes)]

        logger.info(f"팩터 데이터 통합 완료: {len(factor_df)}개 레코드, {len(factor_df.columns)-3}개 팩터")

        return factor_df

    def evaluate_buy_conditions_with_factors(
        self,
        factor_data: pd.DataFrame,
        stock_codes: List[str],
        buy_conditions: Dict[str, Any],
        trading_date: pd.Timestamp
    ) -> List[str]:
        """
        팩터 데이터를 사용하여 매수 조건 평가

        Args:
            factor_data: 통합 팩터 데이터
            stock_codes: 평가할 종목 리스트
            buy_conditions: 매수 조건 (논리식 또는 일반)
            trading_date: 거래일

        Returns:
            조건을 만족하는 종목 코드 리스트
        """

        # 논리식 조건인 경우
        if isinstance(buy_conditions, dict) and 'expression' in buy_conditions:
            if self.use_vectorized:
                selected_stocks = self.condition_evaluator.evaluate_buy_conditions_vectorized(
                    factor_data=factor_data,
                    stock_codes=stock_codes,
                    buy_expression=buy_conditions,
                    trading_date=trading_date
                )
                return selected_stocks
            else:
                # 기본 평가기 (폴백)
                selected_stocks, _ = self.condition_evaluator.evaluate_buy_conditions(
                    factor_data=factor_data,
                    stock_codes=stock_codes,
                    buy_expression=buy_conditions,
                    trading_date=trading_date
                )
                return selected_stocks

        # 일반 조건인 경우 (AND 로직)
        selected_stocks = []

        for stock_code in stock_codes:
            # 해당 종목의 팩터 데이터 추출
            stock_mask = (factor_data['stock_code'] == stock_code)
            date_mask = (pd.to_datetime(factor_data['date']) == trading_date)
            stock_data = factor_data[stock_mask & date_mask]

            if stock_data.empty:
                continue

            # 모든 조건 체크
            all_conditions_met = True

            for condition in buy_conditions:
                # factor 키가 없으면 exp_left_side에서 추출
                if 'factor' in condition:
                    factor_name = condition['factor']
                    operator = condition.get('operator', '>')
                    threshold = condition.get('value', 0)
                else:
                    # exp_left_side에서 팩터명 추출: "기본값({debt_ratio})" → "debt_ratio"
                    import re
                    exp_left_side = condition.get('exp_left_side', '')
                    match = re.search(r'\{([^}]+)\}', exp_left_side)
                    if not match:
                        logger.warning(f"조건에서 팩터명 추출 실패: {condition}")
                        all_conditions_met = False
                        break
                    factor_name = match.group(1)
                    operator = condition.get('inequality', '>')
                    threshold = condition.get('exp_right_side', 0)

                # 대소문자 구분 없이 팩터 값 가져오기
                factor_name_upper = factor_name.upper()

                if factor_name_upper in stock_data.columns:
                    factor_value = float(stock_data[factor_name_upper].iloc[0])
                elif f"{factor_name_upper}_RANK" in stock_data.columns:
                    factor_value = float(stock_data[f"{factor_name_upper}_RANK"].iloc[0])
                else:
                    all_conditions_met = False
                    break

                # 조건 평가
                if not self._evaluate_condition(factor_value, operator, threshold):
                    all_conditions_met = False
                    break

            if all_conditions_met:
                selected_stocks.append(stock_code)
        # 결과 일관성을 위해 stock_code 정렬 (환경 간 동일한 순서 보장)
        return sorted(selected_stocks)

    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """단일 조건 평가"""
        if pd.isna(value):
            return False

        operators = {
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
        }

        op_func = operators.get(operator)
        if op_func:
            return op_func(value, threshold)

        return False

    def rank_stocks_by_composite_score(
        self,
        factor_data: pd.DataFrame,
        stock_codes: List[str],
        factor_weights: Dict[str, float],
        trading_date: pd.Timestamp,
        top_n: int = None
    ) -> List[tuple]:
        """
        복합 스코어로 종목 순위 매기기

        Args:
            factor_data: 팩터 데이터
            stock_codes: 종목 리스트
            factor_weights: 팩터 가중치
            trading_date: 거래일
            top_n: 상위 N개 종목만 반환

        Returns:
            [(stock_code, score), ...] 정렬된 리스트
        """
        scores = []

        # 해당 날짜 데이터만 필터
        date_mask = pd.to_datetime(factor_data['date']) == trading_date
        date_data = factor_data[date_mask]

        if date_data.empty:
            return []

        for stock_code in stock_codes:
            stock_data = date_data[date_data['stock_code'] == stock_code]

            if stock_data.empty:
                continue

            # 복합 스코어 계산
            total_score = 0.0
            weight_sum = 0.0

            for factor_name, weight in factor_weights.items():
                # 랭킹 사용 (정규화된 값)
                rank_col = f"{factor_name}_RANK"

                if rank_col in stock_data.columns:
                    rank_value = stock_data[rank_col].iloc[0]
                    if not pd.isna(rank_value):
                        # 랭킹을 0-1 사이로 정규화
                        max_rank = date_data[rank_col].max()
                        if max_rank > 0:
                            normalized_rank = 1 - (rank_value / max_rank)
                            total_score += normalized_rank * weight
                            weight_sum += abs(weight)

            if weight_sum > 0:
                final_score = total_score / weight_sum
                scores.append((stock_code, final_score))

        # 스코어로 정렬 (동점 시 종목코드 순으로 정렬하여 일관성 보장)
        scores.sort(key=lambda x: (-x[1], x[0]))

        # 상위 N개만 반환
        if top_n:
            scores = scores[:top_n]

        return scores

    def get_factor_values_for_trade(
        self,
        factor_data: pd.DataFrame,
        stock_code: str,
        trading_date: pd.Timestamp,
        factor_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        거래 시점의 팩터 값 추출 (거래 기록용)

        Args:
            factor_data: 팩터 데이터
            stock_code: 종목 코드
            trading_date: 거래일
            factor_names: 추출할 팩터 이름 리스트 (None이면 모두)

        Returns:
            {factor_name: value} 딕셔너리
        """
        # 해당 종목과 날짜의 데이터 추출
        stock_mask = (factor_data['stock_code'] == stock_code)
        date_mask = (pd.to_datetime(factor_data['date']) == trading_date)
        stock_data = factor_data[stock_mask & date_mask]

        if stock_data.empty:
            return {}

        # 팩터 값 추출
        factor_values = {}

        if factor_names is None:
            # 모든 팩터 추출 (메타 컬럼 제외)
            meta_columns = ['date', 'stock_code', 'stock_name']
            factor_names = [col for col in stock_data.columns
                          if col not in meta_columns and not col.endswith('_RANK')]

        for factor_name in factor_names:
            if factor_name in stock_data.columns:
                value = stock_data[factor_name].iloc[0]
                if not pd.isna(value):
                    factor_values[factor_name] = float(value)

        return factor_values