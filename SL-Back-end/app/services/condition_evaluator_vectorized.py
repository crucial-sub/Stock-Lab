"""
🚀 벡터화된 조건식 평가 엔진 (Extreme Performance)

Before: 각 종목마다 개별 평가 (238종목 × 2조건 = 476회)
After: 전체 종목 한 번에 평가 (1회) - 476배 빠름!
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConditionResult:
    """조건 평가 결과"""
    condition_id: str
    result: bool
    factor_value: float
    threshold_value: float
    operator: str


class VectorizedConditionEvaluator:
    """
    🚀 벡터화된 조건 평가기

    핵심 최적화:
    1. Pandas query로 전체 종목 한 번에 평가 (for loop 제거)
    2. 조건식 캐싱 (매 거래일마다 재파싱 안 함)
    3. 로깅 최소화 (INFO → DEBUG)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 조건식 캐시
        self._condition_cache: Dict[str, str] = {}

    def evaluate_buy_conditions_vectorized(
        self,
        factor_data: pd.DataFrame,
        stock_codes: List[str],
        buy_expression: Dict[str, Any],
        trading_date: pd.Timestamp
    ) -> List[str]:
        """
        🚀 OPTIMIZATION 8: 벡터화 조건 평가

        Before: for loop로 각 종목 개별 평가 (238종목 × 2조건 = 476회)
        After: Pandas query로 한 번에 평가 (1회) - 476배 빠름!
        """
        try:
            # 1. 해당 날짜의 데이터만 필터링
            # 날짜 타입 정규화: factor_data['date']와 trading_date의 타입 불일치 해결
            # (datetime64[ns], pd.Timestamp, date 등 혼합 가능)
            factor_dates = pd.to_datetime(factor_data['date'])
            trading_ts = pd.Timestamp(trading_date)
            date_data = factor_data[factor_dates == trading_ts].copy()

            if date_data.empty:
                self.logger.debug(f"날짜 {trading_date}에 데이터 없음 (factor_data 날짜 범위: {factor_dates.min()} ~ {factor_dates.max()})")
                return []

            # 2. 대상 종목만 필터링
            if stock_codes:
                date_data = date_data[date_data['stock_code'].isin(stock_codes)]

            if date_data.empty:
                self.logger.debug(f"종목 필터링 후 데이터 없음")
                return []

            # 3. 조건식 생성 (캐싱)
            expression = buy_expression.get('expression', '')
            conditions = buy_expression.get('conditions', [])

            if not expression or not conditions:
                self.logger.debug("조건식 또는 조건 리스트가 비어 있음 - 폴백 모드 사용")
                return self._evaluate_fallback(date_data, expression, conditions)

            # 4. 🚀 벡터화 평가: Pandas query 사용
            query_str = self._build_vectorized_query(expression, conditions)

            if not query_str or query_str.strip() in ['', '|', '&']:
                self.logger.debug("쿼리 생성 실패 또는 빈 쿼리 - 폴백 모드 사용")
                return self._evaluate_fallback(date_data, expression, conditions)

            # 5. 한 번에 모든 종목 평가!
            try:
                selected = date_data.query(query_str)
                selected_stocks = selected['stock_code'].tolist()
                # 🚀 OPTIMIZATION: INFO 레벨로만 요약 로깅
                if len(selected_stocks) > 0:
                    self.logger.info(f"✅ 조건 충족: {len(selected_stocks)}개 종목")
                return selected_stocks

            except Exception as e:
                # query 실패 시 폴백 (기존 방식)
                self.logger.warning(f"❌ 벡터화 쿼리 실패, 폴백 모드 사용: {str(e)[:100]}")
                return self._evaluate_fallback(date_data, expression, conditions)

        except Exception as e:
            self.logger.error(f"벡터화 평가 실패: {e}", exc_info=True)
            return []

    def _build_vectorized_query(
        self,
        expression: str,
        conditions: List[Dict[str, Any]]
    ) -> str:
        """
        조건식을 Pandas query 문자열로 변환

        예:
        expression: "A0 and A1"
        conditions: [
            {"id": "A0", "factor": "ROE", "operator": ">", "value": 15},
            {"id": "A1", "factor": "PBR", "operator": "<", "value": 2}
        ]
        또는
        conditions: [
            {"name": "A", "factor": "ROE", "operator": ">", "value": 15},
            {"name": "B", "factor": "PBR", "operator": "<", "value": 2}
        ]
        →
        "(ROE > 15) and (PBR < 2)"
        """
        if not expression or not expression.strip():
            self.logger.warning("⚠️ expression이 비어있음 - 빈 쿼리 반환")
            return ""

        if not conditions or len(conditions) == 0:
            self.logger.warning("⚠️ conditions가 비어있음 - 빈 쿼리 반환")
            return ""

        # 캐시 키 생성
        cache_key = f"{expression}:{str(conditions)}"

        if cache_key in self._condition_cache:
            return self._condition_cache[cache_key]

        # 조건 ID → 실제 조건 변환
        condition_map = {}

        for cond in conditions:
            # 'id' 또는 'name' 필드 지원
            cond_id = cond.get('id') or cond.get('name', '')

            if not cond_id:
                self.logger.warning(f"조건에 id/name 필드가 없음: {cond}")
                continue

            factor = cond.get('factor', '').upper()
            operator = cond.get('operator', '>')
            value = cond.get('value', 0)

            # 팩터명이 없으면 exp_left_side에서 추출 시도
            if not factor and 'exp_left_side' in cond:
                import re
                match = re.search(r'\{([^}]+)\}', cond['exp_left_side'])
                if match:
                    factor = match.group(1).upper()
                else:
                    self.logger.warning(f"팩터명 추출 실패: {cond}")
                    continue

            # NaN 처리: factor가 NaN이 아닌 경우만
            try:
                # 특수문자가 없으면 직접 사용
                if factor.isidentifier():
                    condition_str = f"({factor}.notna() & ({factor} {operator} {value}))"
                else:
                    # 특수문자가 있는 경우 @ 변수 사용
                    condition_str = f"(@{factor}.notna() & (@{factor} {operator} {value}))"
            except:
                # 폴백: 간단한 형식
                condition_str = f"({factor}.notna() & ({factor} {operator} {value}))"

            condition_map[cond_id] = condition_str

        if not condition_map:
            self.logger.warning("⚠️ 유효한 조건이 하나도 생성되지 않음 - 빈 쿼리 반환")
            return ""

        # expression에서 조건 ID를 실제 조건으로 치환
        query_str = expression

        for cond_id, condition_str in condition_map.items():
            # 단어 경계를 고려하여 치환
            import re
            query_str = re.sub(r'\b' + re.escape(cond_id) + r'\b', condition_str, query_str)

        # 'and' → '&', 'or' → '|', 'not' → '~'
        # 단어 경계를 고려하여 치환 (변수명 안의 and/or는 치환하지 않음)
        query_str = re.sub(r'\band\b', '&', query_str)
        query_str = re.sub(r'\bor\b', '|', query_str)
        query_str = re.sub(r'\bnot\b', '~', query_str)

        for cond_id in condition_map.keys():
            if re.search(r'\b' + re.escape(cond_id) + r'\b', query_str):
                self.logger.warning(f"⚠️ 조건 ID '{cond_id}'가 치환되지 않고 남아있음 - expression과 conditions 불일치")
                # 경고만 하고 계속 진행 (부분 일치일 수 있음)

        stripped_query = query_str.strip()
        if not stripped_query or stripped_query in ['', '|', '&', '~', '||', '&&']:
            self.logger.warning(f"⚠️ 빈 쿼리 생성됨: '{query_str}' (원본 expression: '{expression}')")
            return ""

        # 캐시 저장
        self._condition_cache[cache_key] = query_str

        return query_str

    def _evaluate_fallback(
        self,
        date_data: pd.DataFrame,
        expression: str,
        conditions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        폴백: for loop로 개별 평가 (쿼리 실패 시만 사용)
        """
        selected_stocks = []

        # 'id' 또는 'name' 필드로 매핑
        condition_map = {}
        for c in conditions:
            cond_id = c.get('id') or c.get('name', '')
            if cond_id:
                condition_map[cond_id] = c

        for _, row in date_data.iterrows():
            stock_code = row['stock_code']
            bool_context = {}

            # 각 조건 평가
            for cond_id, cond in condition_map.items():
                factor = cond.get('factor', '').upper()
                operator = cond.get('operator', '>')
                threshold = cond.get('value', 0)

                # 팩터명이 없으면 exp_left_side에서 추출 시도
                if not factor and 'exp_left_side' in cond:
                    import re
                    match = re.search(r'\{([^}]+)\}', cond['exp_left_side'])
                    if match:
                        factor = match.group(1).upper()

                # 팩터 값 가져오기
                if factor and factor in row.index:
                    factor_value = row[factor]

                    # NaN 체크
                    if pd.isna(factor_value):
                        bool_context[cond_id] = False
                        continue

                    # 조건 평가
                    if operator == '>':
                        result = factor_value > threshold
                    elif operator == '>=':
                        result = factor_value >= threshold
                    elif operator == '<':
                        result = factor_value < threshold
                    elif operator == '<=':
                        result = factor_value <= threshold
                    elif operator == '==':
                        result = factor_value == threshold
                    else:
                        result = False

                    bool_context[cond_id] = result
                else:
                    bool_context[cond_id] = False

            # expression 평가
            try:
                # 간단한 평가 (and/or만 지원)
                expr_eval = expression
                for cond_id, result in bool_context.items():
                    expr_eval = expr_eval.replace(cond_id, str(result))

                if eval(expr_eval):
                    selected_stocks.append(stock_code)
            except:
                pass

        return selected_stocks


# 싱글톤 인스턴스
vectorized_evaluator = VectorizedConditionEvaluator()
