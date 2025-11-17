"""
자동매매 매도 조건 체크
- 백테스트와 동일한 로직 적용
- 목표가/손절가, 보유기간, 조건 매도
"""
import logging
from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import pandas as pd

from app.models.auto_trading import AutoTradingStrategy, LivePosition
from app.models.stock_price import StockPrice
from app.models.company import Company

logger = logging.getLogger(__name__)


class AutoTradingSellChecker:
    """자동매매 매도 조건 체커 (백테스트 로직과 동일)"""

    @staticmethod
    async def check_sell_conditions(
        db: AsyncSession,
        strategy: AutoTradingStrategy,
        positions: List[LivePosition]
    ) -> List[Dict[str, Any]]:
        """
        보유 종목 중 매도 조건을 만족하는 종목 찾기

        Args:
            db: 데이터베이스 세션
            strategy: 자동매매 전략
            positions: 현재 보유 종목 리스트

        Returns:
            매도할 종목 리스트 [{position, reason, price}, ...]
        """
        stocks_to_sell = []
        today = date.today()

        # 현재가 조회 (일괄)
        stock_codes = [p.stock_code for p in positions]
        current_prices = await AutoTradingSellChecker._get_current_prices(db, stock_codes, today)

        for position in positions:
            try:
                # 현재가
                price_info = current_prices.get(position.stock_code)
                if not price_info:
                    logger.warning(f"현재가 없음: {position.stock_code}")
                    continue

                current_price = Decimal(str(price_info['close_price']))
                high_price = Decimal(str(price_info.get('high_price', price_info['close_price'])))
                low_price = Decimal(str(price_info.get('low_price', price_info['close_price'])))

                # 보유일수
                hold_days = (today - position.buy_date).days

                # 매도 체크 (백테스트와 동일한 순서)
                sell_info = AutoTradingSellChecker._check_position_sell(
                    strategy=strategy,
                    position=position,
                    hold_days=hold_days,
                    current_price=current_price,
                    high_price=high_price,
                    low_price=low_price
                )

                if sell_info:
                    stocks_to_sell.append(sell_info)
                    logger.info(f"매도 조건 충족: {position.stock_code} | {sell_info['reason']}")

            except Exception as e:
                logger.error(f"매도 체크 실패: {position.stock_code} | {e}")
                continue

        return stocks_to_sell

    @staticmethod
    def _check_position_sell(
        strategy: AutoTradingStrategy,
        position: LivePosition,
        hold_days: int,
        current_price: Decimal,
        high_price: Decimal,
        low_price: Decimal
    ) -> Optional[Dict[str, Any]]:
        """
        개별 포지션 매도 조건 체크 (백테스트와 완전히 동일한 로직)

        매도 우선순위:
        1. 최대 보유기간 도달
        2. 목표가/손절가 (최소 보유기간 체크)
        3. 조건 매도 (최소 보유기간 체크) - TODO: 팩터 데이터 필요

        Returns:
            매도할 경우: {position, reason, price, hold_days}
            매도하지 않을 경우: None
        """
        should_sell = False
        sell_reason = ""
        sell_price = current_price

        # 최소 보유기간 체크
        min_hold = strategy.min_hold_days
        max_hold = strategy.max_hold_days
        enforce_min_hold = min_hold is not None and hold_days < min_hold

        # 1. 최대 보유기간 체크 (최우선)
        if max_hold and hold_days >= max_hold:
            should_sell = True
            sell_reason = f"Max hold days reached ({hold_days}d)"
            # 보유기간 가격 조정 적용
            if strategy.hold_days_sell_price_basis and strategy.hold_days_sell_price_offset:
                sell_price = current_price * (Decimal("1") + strategy.hold_days_sell_price_offset / Decimal("100"))

        # 2. 목표가/손절가 체크 (최소 보유기간 준수)
        if not should_sell and not enforce_min_hold:
            target_gain = strategy.target_gain
            stop_loss = strategy.stop_loss

            # 일중 최고가 기준 목표가 체크
            high_profit_rate = ((high_price / position.avg_buy_price) - Decimal("1")) * Decimal("100")
            # 일중 최저가 기준 손절가 체크
            low_profit_rate = ((low_price / position.avg_buy_price) - Decimal("1")) * Decimal("100")

            # 손절가 우선 체크 (저가 기준)
            if stop_loss is not None and low_profit_rate <= -stop_loss:
                should_sell = True
                # 손절가에 정확히 매도된 것으로 간주
                target_stop_price = position.avg_buy_price * (Decimal("1") - stop_loss / Decimal("100"))
                sell_price = target_stop_price
                actual_loss_rate = ((sell_price / position.avg_buy_price) - Decimal("1")) * Decimal("100")
                sell_reason = f"Stop loss {actual_loss_rate:.2f}%"

            # 목표가 체크 (고가 기준)
            elif target_gain is not None and high_profit_rate >= target_gain:
                should_sell = True
                # 목표가에 정확히 매도된 것으로 간주
                target_gain_price = position.avg_buy_price * (Decimal("1") + target_gain / Decimal("100"))
                sell_price = target_gain_price
                actual_profit_rate = ((sell_price / position.avg_buy_price) - Decimal("1")) * Decimal("100")
                sell_reason = f"Take profit {actual_profit_rate:.2f}%"

        # 3. 조건 매도 체크 (TODO: 팩터 데이터 필요)
        # if not should_sell and not enforce_min_hold and strategy.sell_conditions:
        #     # 팩터 데이터를 가져와서 조건 평가
        #     # condition_evaluator 사용 필요
        #     pass

        if should_sell:
            return {
                "position": position,
                "reason": sell_reason,
                "price": sell_price,
                "hold_days": hold_days
            }

        return None

    @staticmethod
    async def _get_current_prices(
        db: AsyncSession,
        stock_codes: List[str],
        target_date: date
    ) -> Dict[str, Dict]:
        """
        종목들의 현재가 조회 (일괄)

        Returns:
            {stock_code: {close_price, high_price, low_price}, ...}
        """
        # 최근 영업일 찾기
        search_date = target_date
        for _ in range(5):  # 최대 5일 전까지
            query = select(
                StockPrice.stock_code,
                StockPrice.close_price,
                StockPrice.high_price,
                StockPrice.low_price
            ).join(
                Company, StockPrice.company_id == Company.company_id
            ).where(
                and_(
                    Company.stock_code.in_(stock_codes),
                    StockPrice.trade_date == search_date,
                    StockPrice.close_price.isnot(None)
                )
            )

            result = await db.execute(query)
            rows = result.mappings().all()

            if rows:
                return {
                    row['stock_code']: {
                        'close_price': row['close_price'],
                        'high_price': row['high_price'],
                        'low_price': row['low_price']
                    }
                    for row in rows
                }

            # 데이터 없으면 하루 전으로
            from datetime import timedelta
            search_date -= timedelta(days=1)

        logger.warning(f"현재가 조회 실패: {len(stock_codes)}개 종목")
        return {}
