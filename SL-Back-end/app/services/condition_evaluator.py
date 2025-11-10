"""
조건식 평가 엔진
논리식 파싱 및 평가 로직
"""
import ast
import operator
from typing import Dict, List, Any, Union, Optional
from decimal import Decimal
import pandas as pd
import re
from dataclasses import dataclass


@dataclass
class ConditionResult:
    """조건 평가 결과"""
    condition_id: str
    result: bool
    factor_value: float
    threshold_value: float
    operator: str


class LogicalExpressionParser:
    """논리식 파서"""

    def __init__(self):
        self.operators = {
            '>': operator.gt,
            '>=': operator.ge,
            '<': operator.lt,
            '<=': operator.le,
            '==': operator.eq,
            '!=': operator.ne,
        }

    def parse_expression(self, expression: str) -> ast.AST:
        """
        논리식을 AST로 파싱
        예: "A and B or C" -> AST
        """
        # 안전한 파싱을 위해 허용된 노드만 사용
        try:
            tree = ast.parse(expression, mode='eval')
            self._validate_ast(tree)
            return tree
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")

    def _validate_ast(self, tree: ast.AST):
        """AST 검증 - 안전한 연산만 허용"""
        allowed_nodes = (
            ast.Expression, ast.BoolOp, ast.And, ast.Or,
            ast.UnaryOp, ast.Not, ast.Name, ast.Load,
            ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE,
            ast.Eq, ast.NotEq
        )

        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                raise ValueError(f"Unsafe operation in expression: {type(node).__name__}")

    def evaluate(self, expression: str, context: Dict[str, bool]) -> bool:
        """
        논리식 평가
        Args:
            expression: "A and B or C"
            context: {"A": True, "B": False, "C": True}
        Returns:
            bool: 평가 결과
        """
        # 모든 조건 ID를 Python 변수 형식으로 변환
        safe_expr = expression
        for cond_id in context.keys():
            safe_expr = re.sub(r'\b' + cond_id + r'\b', f'__{cond_id}__', safe_expr)

        # 컨텍스트도 변환
        safe_context = {f'__{k}__': v for k, v in context.items()}

        try:
            # 안전한 평가
            tree = self.parse_expression(safe_expr)
            code = compile(tree, '<string>', 'eval')
            return eval(code, {"__builtins__": {}}, safe_context)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {e}")


class ConditionEvaluator:
    """조건 평가기"""

    def __init__(self):
        self.parser = LogicalExpressionParser()

    def evaluate_factor_condition(
        self,
        factor_data: pd.DataFrame,
        stock_code: str,
        condition: Dict[str, Any],
        trading_date: pd.Timestamp
    ) -> ConditionResult:
        """
        개별 팩터 조건 평가
        Args:
            factor_data: 팩터 데이터
            stock_code: 종목 코드
            condition: 조건 정의 {"factor": "PER", "operator": "<", "value": 15}
            trading_date: 거래일
        Returns:
            ConditionResult
        """
        factor_name = condition['factor']
        op = condition['operator']
        threshold = condition['value']

        # 팩터 값 추출
        try:
            trading_ts = pd.Timestamp(trading_date)

            stock_mask = (factor_data['stock_code'] == stock_code)
            date_mask = (pd.to_datetime(factor_data['date']) == trading_ts)
            stock_data = factor_data[stock_mask & date_mask]

            if stock_data.empty:
                return ConditionResult(
                    condition_id=condition.get('id', ''),
                    result=False,
                    factor_value=None,
                    threshold_value=threshold,
                    operator=op
                )

            # 팩터 값 가져오기
            if factor_name in stock_data.columns:
                factor_value = float(stock_data[factor_name].iloc[0])
            else:
                # 랭킹 컬럼 확인
                rank_col = f"{factor_name}_RANK"
                if rank_col in stock_data.columns:
                    factor_value = float(stock_data[rank_col].iloc[0])
                else:
                    return ConditionResult(
                        condition_id=condition.get('id', ''),
                        result=False,
                        factor_value=None,
                        threshold_value=threshold,
                        operator=op
                    )

            # 조건 평가
            result = self._evaluate_operator(factor_value, op, threshold)

            return ConditionResult(
                condition_id=condition.get('id', ''),
                result=result,
                factor_value=factor_value,
                threshold_value=threshold,
                operator=op
            )

        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return ConditionResult(
                condition_id=condition.get('id', ''),
                result=False,
                factor_value=None,
                threshold_value=threshold,
                operator=op
            )

    def _evaluate_operator(
        self,
        value: float,
        op: str,
        threshold: Union[float, List[float]]
    ) -> bool:
        """연산자 평가"""
        if op == '>':
            return value > threshold
        elif op == '>=':
            return value >= threshold
        elif op == '<':
            return value < threshold
        elif op == '<=':
            return value <= threshold
        elif op == '==':
            return value == threshold
        elif op == '!=':
            return value != threshold
        elif op == 'BETWEEN':
            if isinstance(threshold, list) and len(threshold) == 2:
                return threshold[0] <= value <= threshold[1]
            return False
        elif op == 'IN':
            return value in threshold if isinstance(threshold, list) else False
        elif op == 'NOT_IN':
            return value not in threshold if isinstance(threshold, list) else True
        else:
            return False

    def evaluate_buy_conditions(
        self,
        factor_data: pd.DataFrame,
        stock_codes: List[str],
        buy_expression: Dict[str, Any],
        trading_date: pd.Timestamp
    ) -> List[str]:
        """
        매수 조건 평가 (논리식 기반)
        Args:
            factor_data: 팩터 데이터
            stock_codes: 평가할 종목 리스트
            buy_expression: {
                "expression": "A and B or C",
                "conditions": [
                    {"id": "A", "factor": "PER", "operator": "<", "value": 15},
                    {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
                    {"id": "C", "factor": "PBR", "operator": "<", "value": 2}
                ]
            }
            trading_date: 거래일
        Returns:
            List[str]: 조건을 만족하는 종목 코드 리스트
        """
        expression = buy_expression['expression']
        conditions = buy_expression['conditions']

        # 조건 ID -> 조건 정의 매핑
        condition_map = {c['id']: c for c in conditions}

        selected_stocks = []

        for stock_code in stock_codes:
            # 각 조건 평가
            condition_results = {}

            for cond_id, condition in condition_map.items():
                result = self.evaluate_factor_condition(
                    factor_data, stock_code, condition, trading_date
                )
                condition_results[cond_id] = result.result

            # 논리식 평가
            try:
                if self.parser.evaluate(expression, condition_results):
                    selected_stocks.append(stock_code)
            except Exception as e:
                print(f"Error evaluating expression for {stock_code}: {e}")
                continue

        return selected_stocks

    def rank_stocks_by_factor_score(
        self,
        factor_data: pd.DataFrame,
        stock_codes: List[str],
        factor_weights: Dict[str, float],
        trading_date: pd.Timestamp
    ) -> List[tuple]:
        """
        팩터 스코어로 종목 순위 매기기
        Args:
            factor_data: 팩터 데이터
            stock_codes: 종목 리스트
            factor_weights: 팩터 가중치 {"PER": -1, "ROE": 1, ...}
            trading_date: 거래일
        Returns:
            List[tuple]: [(stock_code, score), ...] 정렬된 리스트
        """
        scores = []

        for stock_code in stock_codes:
            trading_ts = pd.Timestamp(trading_date)
            stock_mask = (factor_data['stock_code'] == stock_code)
            date_mask = (pd.to_datetime(factor_data['date']) == trading_ts)
            stock_data = factor_data[stock_mask & date_mask]

            if stock_data.empty:
                continue

            # 팩터 스코어 계산
            total_score = 0
            for factor, weight in factor_weights.items():
                if factor in stock_data.columns:
                    value = stock_data[factor].iloc[0]
                    if pd.notna(value):
                        # 정규화 (선택적)
                        total_score += float(value) * weight

            scores.append((stock_code, total_score))

        # 스코어 기준 정렬 (높은 순)
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class SQLAlchemyDataFrameConverter:
    """SQLAlchemy 결과를 DataFrame으로 변환"""

    @staticmethod
    def to_dataframe(result, use_mappings: bool = True) -> pd.DataFrame:
        """
        SQLAlchemy 결과를 DataFrame으로 변환
        Args:
            result: SQLAlchemy 실행 결과
            use_mappings: mappings() 사용 여부
        Returns:
            pd.DataFrame
        """
        if use_mappings:
            # 딕셔너리 매핑 사용 (컬럼명 보존)
            rows = result.mappings().all()
            if rows:
                return pd.DataFrame(rows)
            return pd.DataFrame()
        else:
            # 일반 결과 사용
            rows = result.fetchall()
            if rows:
                # 컬럼명 추출
                columns = result.keys()
                return pd.DataFrame(rows, columns=columns)
            return pd.DataFrame()

    @staticmethod
    def to_polars(result, use_mappings: bool = True):
        """
        SQLAlchemy 결과를 Polars DataFrame으로 변환
        Args:
            result: SQLAlchemy 실행 결과
            use_mappings: mappings() 사용 여부
        Returns:
            pl.DataFrame
        """
        import polars as pl

        if use_mappings:
            rows = result.mappings().all()
            if rows:
                return pl.DataFrame(rows)
            return pl.DataFrame()
        else:
            rows = result.fetchall()
            if rows:
                columns = result.keys()
                # 딕셔너리 리스트로 변환
                data = [dict(zip(columns, row)) for row in rows]
                return pl.DataFrame(data)
            return pl.DataFrame()


# 사용 예시
if __name__ == "__main__":
    # 논리식 파서 테스트
    parser = LogicalExpressionParser()

    # 예시 1: 간단한 AND 조건
    expression1 = "A and B"
    context1 = {"A": True, "B": False}
    result1 = parser.evaluate(expression1, context1)
    print(f"{expression1} with {context1} = {result1}")  # False

    # 예시 2: 복잡한 조건
    expression2 = "(A and B) or (C and not D)"
    context2 = {"A": True, "B": False, "C": True, "D": False}
    result2 = parser.evaluate(expression2, context2)
    print(f"{expression2} with {context2} = {result2}")  # True

    # 예시 3: 실제 백테스트 조건
    buy_expression = {
        "expression": "(A and B) or C",
        "conditions": [
            {"id": "A", "factor": "PER", "operator": "<", "value": 15},
            {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
            {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 20}
        ]
    }

    print(f"Buy expression example: {buy_expression}")
