"""
수정주가 계산 모듈

공공데이터포털에서 받아온 원주가를 수정주가로 변환합니다.
- 무상증자, 유상증자, 액면분할, 액면병합 등 기업행동 반영
- 과거 가격을 소급 조정하여 연속적인 가격 흐름 유지

사용법:
    adjuster = PriceAdjuster(db)
    adjusted_df = await adjuster.adjust_prices(df, start_date, end_date)
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Optional
from decimal import Decimal

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# 비정상 변동 감지 임계값
ABNORMAL_CHANGE_THRESHOLD = 50.0  # 50% 이상 변동 시 기업행동으로 의심


class PriceAdjuster:
    """수정주가 계산기"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_corporate_actions(
        self,
        df: pd.DataFrame,
        threshold: float = ABNORMAL_CHANGE_THRESHOLD
    ) -> pd.DataFrame:
        """
        기업행동(무상증자, 액면분할 등) 감지

        Args:
            df: 주가 데이터 (stock_code, date, close_price 필수)
            threshold: 변동률 임계값 (%)

        Returns:
            기업행동 이벤트 DataFrame (stock_code, date, change_rate, adjustment_factor)
        """
        if df.empty:
            return pd.DataFrame()

        df = df.sort_values(['stock_code', 'date'])
        df['prev_close'] = df.groupby('stock_code')['close_price'].shift(1)
        df['change_rate'] = ((df['close_price'] - df['prev_close']) / df['prev_close'] * 100)

        # 급등/급락 감지
        abnormal_mask = df['change_rate'].abs() > threshold
        events = df[abnormal_mask][['stock_code', 'stock_name', 'date', 'prev_close', 'close_price', 'change_rate']].copy()

        if events.empty:
            return pd.DataFrame()

        # 조정 비율 계산
        # 예: 1923 → 9920 (415% 상승) → adjustment_factor = 1923/9920 = 0.1938
        # 과거 가격에 이 비율을 곱하면 연속적인 가격 흐름 유지
        events['adjustment_factor'] = events['prev_close'] / events['close_price']

        logger.info(f"🔍 기업행동 감지: {len(events)}건")
        for _, row in events.iterrows():
            action_type = "급등(무상증자 추정)" if row['change_rate'] > 0 else "급락(감자 추정)"
            logger.info(
                f"  - {row['stock_name']}({row['stock_code']}) {row['date'].strftime('%Y-%m-%d')}: "
                f"{row['prev_close']:.0f}원 → {row['close_price']:.0f}원 ({row['change_rate']:+.1f}%) "
                f"[{action_type}] 조정비율={row['adjustment_factor']:.4f}"
            )

        return events

    async def adjust_prices(
        self,
        df: pd.DataFrame,
        corporate_events: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        수정주가 계산

        기업행동 발생 시 해당 종목의 과거 가격을 모두 조정합니다.

        Args:
            df: 원주가 데이터
            corporate_events: 기업행동 이벤트 (없으면 자동 감지)

        Returns:
            수정주가가 적용된 DataFrame
        """
        if df.empty:
            return df

        df = df.copy()
        df = df.sort_values(['stock_code', 'date'])

        # 기업행동 자동 감지
        if corporate_events is None:
            corporate_events = await self.detect_corporate_actions(df)

        if corporate_events.empty:
            logger.info("✅ 기업행동 없음 - 수정주가 조정 불필요")
            return df

        # 가격 컬럼 목록
        price_columns = ['open_price', 'high_price', 'low_price', 'close_price']
        available_price_cols = [col for col in price_columns if col in df.columns]

        adjusted_count = 0

        # 각 기업행동 이벤트에 대해 과거 가격 조정
        for _, event in corporate_events.iterrows():
            stock_code = event['stock_code']
            event_date = event['date']
            factor = event['adjustment_factor']

            # 해당 종목의 이벤트 발생일 이전 데이터 선택
            mask = (df['stock_code'] == stock_code) & (df['date'] < event_date)
            rows_to_adjust = mask.sum()

            if rows_to_adjust > 0:
                # 가격 조정 적용
                for col in available_price_cols:
                    df.loc[mask, col] = df.loc[mask, col] * factor

                adjusted_count += rows_to_adjust
                logger.info(
                    f"  📊 {event['stock_name']}({stock_code}): "
                    f"{rows_to_adjust}건 가격 조정 완료 (factor={factor:.4f})"
                )

        logger.info(f"✅ 수정주가 적용 완료: 총 {adjusted_count}건 조정")

        return df

    async def get_adjustment_factors(
        self,
        stock_codes: List[str],
        start_date: date,
        end_date: date
    ) -> Dict[str, List[Dict]]:
        """
        DB에서 기업행동 이력 조회 (추후 구현)

        실제 기업행동 데이터가 있다면 이를 활용하여 더 정확한 조정이 가능합니다.
        - 무상증자: 증자비율로 조정
        - 액면분할: 분할비율로 조정
        - 유상증자: 신주인수권 가치 반영

        현재는 가격 변동률 기반 자동 감지 방식을 사용합니다.
        """
        # TODO: 기업행동 테이블 구현 시 활용
        # 예: corporate_actions 테이블에서 무상증자, 액면분할 정보 조회
        return {}


class PriceValidator:
    """주가 데이터 검증기"""

    @staticmethod
    def validate_price_continuity(df: pd.DataFrame, threshold: float = 50.0) -> Dict:
        """
        가격 연속성 검증

        Args:
            df: 주가 데이터
            threshold: 비정상 변동 임계값 (%)

        Returns:
            검증 결과 딕셔너리
        """
        if df.empty:
            return {"valid": True, "issues": []}

        df = df.sort_values(['stock_code', 'date'])
        df['prev_close'] = df.groupby('stock_code')['close_price'].shift(1)
        df['change_rate'] = ((df['close_price'] - df['prev_close']) / df['prev_close'] * 100)

        # 비정상 변동 검출
        abnormal = df[df['change_rate'].abs() > threshold]

        issues = []
        for _, row in abnormal.iterrows():
            issues.append({
                "stock_code": row['stock_code'],
                "stock_name": row.get('stock_name', 'N/A'),
                "date": row['date'],
                "prev_close": row['prev_close'],
                "close_price": row['close_price'],
                "change_rate": row['change_rate']
            })

        return {
            "valid": len(issues) == 0,
            "total_records": len(df),
            "abnormal_count": len(issues),
            "issues": issues
        }

    @staticmethod
    def validate_zero_prices(df: pd.DataFrame) -> Dict:
        """
        0원 가격 검증

        Args:
            df: 주가 데이터

        Returns:
            검증 결과 딕셔너리
        """
        if df.empty:
            return {"valid": True, "issues": []}

        price_cols = ['open_price', 'high_price', 'low_price', 'close_price']
        available_cols = [col for col in price_cols if col in df.columns]

        issues = []
        for col in available_cols:
            zero_mask = df[col] == 0
            if zero_mask.any():
                zero_rows = df[zero_mask]
                for _, row in zero_rows.iterrows():
                    issues.append({
                        "stock_code": row['stock_code'],
                        "stock_name": row.get('stock_name', 'N/A'),
                        "date": row['date'],
                        "column": col,
                        "value": 0
                    })

        return {
            "valid": len(issues) == 0,
            "total_records": len(df),
            "zero_price_count": len(issues),
            "issues": issues
        }
