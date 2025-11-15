"""
자동매매 실행기
- 종목 선정 (매일 8시)
- 매수/매도 주문 실행 (매일 9시)
"""
import logging
import time
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import pandas as pd
import numpy as np

from app.models.auto_trading import AutoTradingStrategy, LivePosition, LiveTrade, AutoTradingLog
from app.models.simulation import SimulationSession, TradingRule, StrategyFactor
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement
from app.models.balance_sheet import BalanceSheet
from app.models.income_statement import IncomeStatement
from app.models.user import User
from app.services.kiwoom_service import KiwoomService

logger = logging.getLogger(__name__)


class AutoTradingExecutor:
    """자동매매 실행기"""

    @staticmethod
    async def select_stocks_for_strategy(
        db: AsyncSession,
        strategy: AutoTradingStrategy
    ) -> List[Dict[str, Any]]:
        """
        전략 조건에 맞는 종목 선정

        Args:
            db: 데이터베이스 세션
            strategy: 자동매매 전략

        Returns:
            선정된 종목 리스트
        """
        try:
            # 1. 전략의 매수 조건 조회
            session_query = select(SimulationSession).where(
                SimulationSession.session_id == strategy.simulation_session_id
            )
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                logger.error(f"세션을 찾을 수 없음: {strategy.simulation_session_id}")
                return []

            # 2. TradingRule 조회 (매수 조건)
            trading_rule_query = select(TradingRule).where(
                TradingRule.strategy_id == session.strategy_id
            )
            trading_rule_result = await db.execute(trading_rule_query)
            trading_rule = trading_rule_result.scalar_one_or_none()

            if not trading_rule or not trading_rule.buy_condition:
                logger.error("매수 조건을 찾을 수 없음")
                return []

            buy_condition = trading_rule.buy_condition
            logger.info(f"매수 조건: {buy_condition}")

            # 3. 오늘 날짜 기준으로 종목 데이터 조회
            today = date.today()

            # 최근 영업일 찾기 (오늘이 주말이면 금요일)
            while today.weekday() >= 5:  # 토요일(5), 일요일(6)
                today -= timedelta(days=1)

            # 4. 전체 종목의 최신 가격 및 재무 데이터 조회
            stock_data = await AutoTradingExecutor._get_latest_stock_data(db, today)

            if stock_data.empty:
                logger.warning("종목 데이터가 없음")
                return []

            # 5. 매수 조건 필터링 (간단한 버전)
            selected_stocks = await AutoTradingExecutor._apply_buy_conditions(
                stock_data, buy_condition, strategy.max_positions
            )

            logger.info(f"✅ 종목 선정 완료: {len(selected_stocks)}개")

            return selected_stocks

        except Exception as e:
            logger.error(f"종목 선정 실패: {e}", exc_info=True)
            return []

    @staticmethod
    async def _get_latest_stock_data(
        db: AsyncSession,
        target_date: date
    ) -> pd.DataFrame:
        """
        최신 종목 데이터 조회 (가격 + 재무)
        """
        # 최근 5영업일 데이터 조회
        start_date = target_date - timedelta(days=10)

        # 주가 데이터 조회
        price_query = select(
            StockPrice.company_id,
            Company.stock_code,
            Company.company_name,
            StockPrice.close_price,
            StockPrice.market_cap,
            StockPrice.trade_date
        ).join(
            Company, StockPrice.company_id == Company.company_id
        ).where(
            and_(
                StockPrice.trade_date >= start_date,
                StockPrice.trade_date <= target_date,
                StockPrice.close_price.isnot(None)
            )
        ).order_by(StockPrice.company_id, StockPrice.trade_date.desc())

        price_result = await db.execute(price_query)
        price_rows = price_result.mappings().all()

        if not price_rows:
            return pd.DataFrame()

        price_df = pd.DataFrame(price_rows)

        # 각 종목의 최신 데이터만 선택
        price_df = price_df.sort_values('trade_date', ascending=False).groupby('company_id').first().reset_index()

        # 재무 데이터 로드 및 병합
        financial_df = await AutoTradingExecutor._load_financial_ratios(db, target_date)

        if not financial_df.empty:
            # company_id로 병합
            df = pd.merge(price_df, financial_df, on='company_id', how='left')

            # PER, PBR 계산 (백테스트와 동일한 로직)
            # PER = 시가총액 / 당기순이익
            if '당기순이익' in df.columns and 'market_cap' in df.columns:
                df['per'] = df.apply(
                    lambda row: float(row['market_cap'] / row['당기순이익'])
                    if pd.notna(row.get('당기순이익')) and row['당기순이익'] > 0
                    else None,
                    axis=1
                )

            # PBR = 시가총액 / 자본총계
            if '자본총계' in df.columns and 'market_cap' in df.columns:
                df['pbr'] = df.apply(
                    lambda row: float(row['market_cap'] / row['자본총계'])
                    if pd.notna(row.get('자본총계')) and row['자본총계'] > 0
                    else None,
                    axis=1
                )

            logger.info(f"종목 데이터 조회 완료: {len(df)}개 종목 (PER, PBR, ROE 포함)")
        else:
            df = price_df
            logger.warning("재무 데이터를 불러올 수 없습니다")

        return df

    @staticmethod
    async def _load_financial_ratios(
        db: AsyncSession,
        target_date: date
    ) -> pd.DataFrame:
        """
        재무 비율 계산 (백테스트와 동일한 로직)
        - PER = 시가총액 / 당기순이익
        - PBR = 시가총액 / 자본총계
        - ROE = (당기순이익 / 자본총계) * 100
        """
        try:
            # 1~2년 전 데이터부터 조회
            start_year = str(target_date.year - 2)
            end_year = str(target_date.year)

            # 손익계산서 데이터 조회
            income_query = select(
                FinancialStatement.company_id,
                Company.stock_code,
                FinancialStatement.bsns_year.label('fiscal_year'),
                FinancialStatement.reprt_code.label('report_code'),
                IncomeStatement.account_nm,
                IncomeStatement.thstrm_amount.label('current_amount')
            ).join(
                IncomeStatement, FinancialStatement.stmt_id == IncomeStatement.stmt_id
            ).join(
                Company, FinancialStatement.company_id == Company.company_id
            ).where(
                and_(
                    FinancialStatement.bsns_year >= start_year,
                    FinancialStatement.bsns_year <= end_year,
                    IncomeStatement.account_nm.in_([
                        '매출액', '매출', '영업수익',
                        '영업이익', '영업이익(손실)',
                        '당기순이익', '당기순이익(손실)'
                    ])
                )
            )

            # 재무상태표 데이터 조회
            balance_query = select(
                FinancialStatement.company_id,
                Company.stock_code,
                FinancialStatement.bsns_year.label('fiscal_year'),
                FinancialStatement.reprt_code.label('report_code'),
                BalanceSheet.account_nm,
                BalanceSheet.thstrm_amount.label('current_amount')
            ).join(
                BalanceSheet, FinancialStatement.stmt_id == BalanceSheet.stmt_id
            ).join(
                Company, FinancialStatement.company_id == Company.company_id
            ).where(
                and_(
                    FinancialStatement.bsns_year >= start_year,
                    FinancialStatement.bsns_year <= end_year,
                    BalanceSheet.account_nm.in_([
                        '자산총계', '자본총계', '부채총계'
                    ])
                )
            )

            # 데이터 실행
            income_result = await db.execute(income_query)
            balance_result = await db.execute(balance_query)

            income_df = pd.DataFrame(income_result.mappings().all())
            balance_df = pd.DataFrame(balance_result.mappings().all())

            if income_df.empty and balance_df.empty:
                return pd.DataFrame()

            # 계정 과목 정규화
            if not income_df.empty:
                income_df['account_nm'] = income_df['account_nm'].str.replace('당기순이익(손실)', '당기순이익', regex=False)
                income_df['account_nm'] = income_df['account_nm'].str.replace('영업이익(손실)', '영업이익', regex=False)

            # 데이터 피벗 (계정과목을 컬럼으로)
            if not income_df.empty:
                income_pivot = income_df.pivot_table(
                    index=['company_id', 'stock_code', 'fiscal_year', 'report_code'],
                    columns='account_nm',
                    values='current_amount',
                    aggfunc='first'
                ).reset_index()
            else:
                income_pivot = pd.DataFrame()

            if not balance_df.empty:
                balance_pivot = balance_df.pivot_table(
                    index=['company_id', 'stock_code', 'fiscal_year', 'report_code'],
                    columns='account_nm',
                    values='current_amount',
                    aggfunc='first'
                ).reset_index()
            else:
                balance_pivot = pd.DataFrame()

            # 두 데이터프레임 병합
            if not income_pivot.empty and not balance_pivot.empty:
                financial_df = pd.merge(
                    income_pivot, balance_pivot,
                    on=['company_id', 'stock_code', 'fiscal_year', 'report_code'],
                    how='outer'
                )
            elif not income_pivot.empty:
                financial_df = income_pivot
            elif not balance_pivot.empty:
                financial_df = balance_pivot
            else:
                return pd.DataFrame()

            # report_date 생성 (백테스트와 동일한 로직)
            def make_report_date(row):
                year = int(row['fiscal_year'])
                code = row['report_code']
                if code == '11011':  # 사업보고서 - 연말
                    return pd.Timestamp(year, 12, 31)
                elif code == '11012':  # 반기보고서 - 6월말
                    return pd.Timestamp(year, 6, 30)
                elif code == '11013':  # 1분기 - 3월말
                    return pd.Timestamp(year, 3, 31)
                elif code == '11014':  # 3분기 - 9월말
                    return pd.Timestamp(year, 9, 30)
                else:
                    return pd.Timestamp(year, 12, 31)  # 기본값

            financial_df['report_date'] = financial_df.apply(make_report_date, axis=1)

            # target_date 이전의 최신 재무 데이터만 선택
            financial_df = financial_df[financial_df['report_date'] <= pd.Timestamp(target_date)]
            financial_df = financial_df.sort_values('report_date', ascending=False).groupby('company_id').first().reset_index()

            # ROE 계산 (당기순이익 / 자본총계 * 100)
            if '당기순이익' in financial_df.columns and '자본총계' in financial_df.columns:
                financial_df['roe'] = (financial_df['당기순이익'] / financial_df['자본총계']) * 100
            else:
                financial_df['roe'] = None

            # PBR, PER은 시가총액이 필요하므로 여기서는 필요한 데이터만 준비
            # (나중에 시가총액과 병합 후 계산)
            # stock_code는 price_df에 이미 있으므로 제외 (중복 방지)
            result_df = financial_df[['company_id', '당기순이익', '자본총계', 'roe']].copy()

            logger.info(f"재무 비율 조회 완료: {len(result_df)}개 종목")

            return result_df

        except Exception as e:
            logger.error(f"재무 비율 조회 실패: {e}", exc_info=True)
            return pd.DataFrame()

    @staticmethod
    async def _apply_buy_conditions(
        stock_data: pd.DataFrame,
        buy_condition: Dict[str, Any],
        max_positions: int
    ) -> List[Dict[str, Any]]:
        """
        매수 조건 적용하여 종목 필터링
        """
        try:
            conditions = buy_condition.get('conditions', [])
            priority_factor = buy_condition.get('priority_factor')
            priority_order = buy_condition.get('priority_order', 'desc')

            # 필터링된 데이터프레임
            filtered_df = stock_data.copy()

            # 각 조건 적용
            for cond in conditions:
                exp_left = cond.get('exp_left_side', '')
                inequality = cond.get('inequality', '>')
                threshold = cond.get('exp_right_side', 0)

                # 팩터 추출 (예: "{PER}" -> "per")
                import re
                match = re.search(r'\{([^}]+)\}', exp_left)
                if match:
                    factor_name = match.group(1).strip().lower()

                    # PBR, PER 등 컬럼명 매핑
                    column_map = {
                        'pbr': 'pbr',
                        'per': 'per',
                        'roe': 'roe',
                        '부채비율': 'debt_ratio'
                    }

                    column_name = column_map.get(factor_name)

                    if column_name and column_name in filtered_df.columns:
                        # 해당 컬럼의 NaN 제거 (조건 적용 전)
                        filtered_df = filtered_df[filtered_df[column_name].notna()]

                        # 조건 적용
                        if inequality == '<':
                            filtered_df = filtered_df[filtered_df[column_name] < threshold]
                        elif inequality == '>':
                            filtered_df = filtered_df[filtered_df[column_name] > threshold]
                        elif inequality == '<=':
                            filtered_df = filtered_df[filtered_df[column_name] <= threshold]
                        elif inequality == '>=':
                            filtered_df = filtered_df[filtered_df[column_name] >= threshold]
                        elif inequality == '==':
                            filtered_df = filtered_df[filtered_df[column_name] == threshold]

                        logger.info(f"조건 적용: {factor_name} {inequality} {threshold} -> 남은 종목: {len(filtered_df)}개")
                    else:
                        logger.warning(f"재무 비율 '{factor_name}' 컬럼 없음 - 조건 스킵")

            # 우선순위 팩터로 정렬
            if priority_factor and len(filtered_df) > 0:
                sort_column = priority_factor.lower()
                column_map = {'pbr': 'pbr', 'per': 'per', 'roe': 'roe'}
                sort_column = column_map.get(sort_column, 'market_cap')

                if sort_column in filtered_df.columns:
                    ascending = (priority_order == 'asc')
                    filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)

            # 상위 N개 선택
            filtered_df = filtered_df.head(max_positions)

            # 결과 반환
            selected_stocks = []
            for _, row in filtered_df.iterrows():
                selected_stocks.append({
                    'stock_code': row['stock_code'],
                    'company_name': row['company_name'],
                    'current_price': float(row['close_price']),
                    'market_cap': float(row.get('market_cap', 0)),
                    'per': float(row.get('per', 0)) if pd.notna(row.get('per')) else None,
                    'pbr': float(row.get('pbr', 0)) if pd.notna(row.get('pbr')) else None,
                })

            return selected_stocks

        except Exception as e:
            logger.error(f"조건 적용 실패: {e}", exc_info=True)
            return []

    @staticmethod
    async def execute_buy_orders(
        db: AsyncSession,
        strategy: AutoTradingStrategy,
        selected_stocks: List[Dict[str, Any]]
    ) -> int:
        """
        매수 주문 실행

        Args:
            db: 데이터베이스 세션
            strategy: 자동매매 전략
            selected_stocks: 선정된 종목 리스트

        Returns:
            매수 성공한 종목 수
        """
        success_count = 0

        # 사용자 조회 (키움 토큰)
        user_query = select(User).where(User.user_id == strategy.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user or not user.kiwoom_access_token:
            logger.error("키움 토큰이 없습니다")
            return 0

        # 종목당 투자금액 계산
        per_stock_amount = strategy.cash_balance * (strategy.per_stock_ratio / Decimal("100"))

        for stock in selected_stocks:
            try:
                stock_code = stock['stock_code']
                current_price = Decimal(str(stock['current_price']))

                # 매수 수량 계산
                quantity = int(per_stock_amount / current_price)

                if quantity == 0:
                    logger.warning(f"수량이 0: {stock_code}")
                    continue

                # 키움 API 매수 주문
                order_result = KiwoomService.buy_stock(
                    access_token=user.kiwoom_access_token,
                    stock_code=stock_code,
                    quantity=quantity,
                    price=0,  # 시장가
                    trade_type="03",  # 시장가
                    dmst_stex_tp="1"
                )

                # 실제 체결 금액
                total_amount = current_price * quantity
                commission = total_amount * Decimal("0.00015")

                # 매매 내역 저장
                trade = LiveTrade(
                    strategy_id=strategy.strategy_id,
                    trade_date=date.today(),
                    trade_type="BUY",
                    stock_code=stock_code,
                    stock_name=stock.get('company_name'),
                    quantity=quantity,
                    price=current_price,
                    amount=total_amount,
                    commission=commission,
                    tax=Decimal("0"),
                    selection_reason=f"자동선정 - PER: {stock.get('per')}, PBR: {stock.get('pbr')}",
                    factors=stock,
                    order_number=order_result.get("order_no"),
                    order_status="FILLED"
                )
                db.add(trade)

                # 포지션 생성
                position = LivePosition(
                    strategy_id=strategy.strategy_id,
                    stock_code=stock_code,
                    stock_name=stock.get('company_name'),
                    quantity=quantity,
                    avg_buy_price=current_price,
                    current_price=current_price,
                    buy_date=date.today(),
                    hold_days=0,
                    buy_factors=stock,
                    selection_reason=f"자동선정"
                )
                db.add(position)

                # 현금 차감
                strategy.cash_balance -= (total_amount + commission)

                logger.info(f"✅ 매수 완료: {stock_code}, 수량={quantity}, 금액={total_amount:,.0f}원")
                success_count += 1

                # Rate Limit 방지 (키움 API)
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"매수 실패: {stock.get('stock_code')}, {e}")
                time.sleep(0.5)  # 실패해도 딜레이
                continue

        await db.commit()

        # 로그 기록
        log = AutoTradingLog(
            strategy_id=strategy.strategy_id,
            event_type="BUY_ORDERS_EXECUTED",
            event_level="INFO",
            message=f"매수 주문 실행 완료 - 성공: {success_count}/{len(selected_stocks)}",
            details={"success_count": success_count, "total_selected": len(selected_stocks)}
        )
        db.add(log)
        await db.commit()

        return success_count
