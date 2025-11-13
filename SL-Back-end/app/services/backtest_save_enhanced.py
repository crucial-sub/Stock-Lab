"""
백테스트 결과 저장 강화 모듈
- 논리식 조건 저장
- 주문/체결/포지션 데이터 저장
- 월별/연도별 통계 저장
- 낙폭 기간 및 팩터 기여도 저장
"""
from typing import Dict, List, Any, Optional
from uuid import UUID
from decimal import Decimal
import json
from datetime import datetime
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

logger = logging.getLogger(__name__)


class EnhancedBacktestSaver:
    """백테스트 결과 저장 클래스 (확장)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_complete_result(
        self,
        backtest_id: UUID,
        result: Any,  # BacktestResult
        buy_conditions: Any,  # 논리식 또는 일반 조건
        sell_conditions: List[Dict],
        orders: List[Any] = None,
        executions: List[Any] = None,
        positions: List[Any] = None,
        position_history: List[Any] = None,
        monthly_stats: List[Dict] = None,
        yearly_stats: List[Dict] = None,
        drawdown_periods: List[Dict] = None,
        factor_contributions: Dict[str, Dict] = None
    ):
        """완전한 백테스트 결과 저장"""

        try:
            # 1. 확장 세션 테이블 저장
            await self._save_extended_session(
                backtest_id, result, buy_conditions, sell_conditions
            )

            # 2. 주문/체결 데이터 저장
            if orders:
                await self._save_orders(backtest_id, orders)
            if executions:
                await self._save_executions(backtest_id, executions)

            # 3. 포지션 데이터 저장
            if positions:
                await self._save_positions(backtest_id, positions)
            if position_history:
                await self._save_position_history(backtest_id, position_history)

            # 4. 통계 저장
            if monthly_stats:
                await self._save_monthly_stats(backtest_id, monthly_stats)
            if yearly_stats:
                await self._save_yearly_stats(backtest_id, yearly_stats)

            # 5. 분석 데이터 저장
            if drawdown_periods:
                await self._save_drawdown_periods(backtest_id, drawdown_periods)
            if factor_contributions:
                await self._save_factor_contributions(backtest_id, factor_contributions)

            # 6. 기존 테이블 저장 (하위 호환성)
            await self._save_legacy_tables(backtest_id, result)

            # 커밋
            await self.db.commit()
            logger.info(f"✅ 백테스트 {backtest_id} 저장 완료")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ 백테스트 저장 실패: {e}")
            raise

    async def _save_extended_session(
        self,
        backtest_id: UUID,
        result: Any,
        buy_conditions: Any,
        sell_conditions: List[Dict]
    ):
        """확장 세션 정보 저장"""
        from app.models.backtest_extended import BacktestSessionExtended

        # 논리식 조건 처리
        buy_expression = None
        buy_conditions_json = None
        factor_weights = None

        if isinstance(buy_conditions, dict):
            if 'expression' in buy_conditions:
                # 논리식 형태
                buy_expression = buy_conditions['expression']
                buy_conditions_json = buy_conditions.get('conditions', [])
                factor_weights = buy_conditions.get('factor_weights', {})
            else:
                # 일반 조건 (딕셔너리 형태)
                buy_conditions_json = buy_conditions
        elif isinstance(buy_conditions, list):
            # 리스트 형태의 조건
            buy_conditions_json = buy_conditions

        session = BacktestSessionExtended(
            backtest_id=backtest_id,
            backtest_name=result.backtest_name,
            status=result.status,
            start_date=result.statistics.start_date,
            end_date=result.statistics.end_date,
            initial_capital=result.statistics.initial_capital,
            rebalance_frequency=result.settings.rebalance_frequency,
            max_positions=result.settings.max_positions,
            position_sizing=result.settings.position_sizing,
            buy_expression=buy_expression,
            buy_conditions_json=buy_conditions_json,
            sell_conditions_json=sell_conditions,
            factor_weights=factor_weights,
            commission_rate=Decimal(str(result.settings.commission_rate)),
            tax_rate=Decimal(str(result.settings.tax_rate)),
            slippage=Decimal(str(result.settings.slippage)),
            created_at=result.created_at,
            completed_at=result.completed_at
        )
        self.db.add(session)
        logger.info(f"  - 확장 세션 저장: {backtest_id}")

    async def _save_orders(self, backtest_id: UUID, orders: List[Any]):
        """주문 데이터 저장"""
        from app.models.backtest_extended import BacktestOrder

        for order_data in orders:
            order = BacktestOrder(
                order_id=order_data.order_id if hasattr(order_data, 'order_id') else UUID(),
                backtest_id=backtest_id,
                order_date=order_data.order_date,
                stock_code=order_data.stock_code,
                stock_name=order_data.stock_name,
                order_side=order_data.order_side,
                order_type=order_data.order_type if hasattr(order_data, 'order_type') else 'MARKET',
                quantity=order_data.quantity,
                order_price=Decimal(str(order_data.order_price)) if hasattr(order_data, 'order_price') else None,
                status=order_data.status if hasattr(order_data, 'status') else 'FILLED',
                filled_quantity=order_data.filled_quantity if hasattr(order_data, 'filled_quantity') else order_data.quantity,
                reason=order_data.reason if hasattr(order_data, 'reason') else None,
                factor_scores=order_data.factor_scores if hasattr(order_data, 'factor_scores') else None,
                condition_results=order_data.condition_results if hasattr(order_data, 'condition_results') else None
            )
            self.db.add(order)

        logger.info(f"  - {len(orders)}개 주문 저장")

    async def _save_executions(self, backtest_id: UUID, executions: List[Any]):
        """체결 데이터 저장"""
        from app.models.backtest_extended import BacktestExecution

        for exec_data in executions:
            execution = BacktestExecution(
                execution_id=exec_data.execution_id if hasattr(exec_data, 'execution_id') else UUID(),
                backtest_id=backtest_id,
                order_id=exec_data.order_id if hasattr(exec_data, 'order_id') else UUID(),
                execution_date=exec_data.execution_date,
                stock_code=exec_data.stock_code,
                stock_name=exec_data.stock_name,
                execution_side=exec_data.side if hasattr(exec_data, 'side') else 'BUY',
                quantity=exec_data.quantity,
                price=Decimal(str(exec_data.price)),
                amount=Decimal(str(exec_data.amount)),
                commission=Decimal(str(exec_data.commission)),
                tax=Decimal(str(exec_data.tax)) if hasattr(exec_data, 'tax') else Decimal('0'),
                slippage_cost=Decimal(str(exec_data.slippage_cost)) if hasattr(exec_data, 'slippage_cost') else Decimal('0'),
                total_cost=Decimal(str(exec_data.total_cost))
            )
            self.db.add(execution)

        logger.info(f"  - {len(executions)}개 체결 저장")

    async def _save_positions(self, backtest_id: UUID, positions: List[Any]):
        """포지션 데이터 저장"""
        from app.models.backtest_extended import BacktestPosition

        for pos_data in positions:
            position = BacktestPosition(
                position_id=pos_data.position_id if hasattr(pos_data, 'position_id') else UUID(),
                backtest_id=backtest_id,
                stock_code=pos_data.stock_code,
                stock_name=pos_data.stock_name,
                quantity=pos_data.quantity,
                avg_price=Decimal(str(pos_data.avg_price)),
                current_price=Decimal(str(pos_data.current_price)),
                market_value=Decimal(str(pos_data.market_value)),
                unrealized_pnl=Decimal(str(pos_data.unrealized_pnl)),
                unrealized_pnl_pct=Decimal(str(pos_data.unrealized_pnl_pct)),
                realized_pnl=Decimal(str(pos_data.realized_pnl)) if hasattr(pos_data, 'realized_pnl') else Decimal('0'),
                entry_date=pos_data.entry_date,
                last_update=pos_data.last_update if hasattr(pos_data, 'last_update') else pos_data.entry_date,
                hold_days=pos_data.hold_days if hasattr(pos_data, 'hold_days') else 0,
                is_active=pos_data.is_active if hasattr(pos_data, 'is_active') else True,
                exit_date=pos_data.exit_date if hasattr(pos_data, 'exit_date') else None,
                exit_reason=pos_data.exit_reason if hasattr(pos_data, 'exit_reason') else None,
                entry_factors=pos_data.entry_factors if hasattr(pos_data, 'entry_factors') else None,
                current_factors=pos_data.current_factors if hasattr(pos_data, 'current_factors') else None
            )
            self.db.add(position)

        logger.info(f"  - {len(positions)}개 포지션 저장")

    async def _save_position_history(self, backtest_id: UUID, position_history: List[Any]):
        """포지션 히스토리 저장"""
        from app.models.backtest_extended import BacktestPositionHistory

        for hist_data in position_history:
            history = BacktestPositionHistory(
                backtest_id=backtest_id,
                snapshot_date=hist_data['snapshot_date'],
                stock_code=hist_data['stock_code'],
                stock_name=hist_data['stock_name'],
                quantity=hist_data['quantity'],
                avg_price=Decimal(str(hist_data['avg_price'])),
                close_price=Decimal(str(hist_data['close_price'])),
                market_value=Decimal(str(hist_data['market_value'])),
                daily_pnl=Decimal(str(hist_data.get('daily_pnl', 0))),
                cumulative_pnl=Decimal(str(hist_data.get('cumulative_pnl', 0))),
                pnl_pct=Decimal(str(hist_data.get('pnl_pct', 0))),
                weight=Decimal(str(hist_data.get('weight', 0))),
                max_profit=Decimal(str(hist_data['max_profit'])) if 'max_profit' in hist_data else None,
                max_loss=Decimal(str(hist_data['max_loss'])) if 'max_loss' in hist_data else None
            )
            self.db.add(history)

        logger.info(f"  - {len(position_history)}개 포지션 히스토리 저장")

    async def _save_monthly_stats(self, backtest_id: UUID, monthly_stats: List[Dict]):
        """월별 통계 저장"""
        from app.models.backtest_extended import BacktestMonthlyStats

        for stat in monthly_stats:
            monthly = BacktestMonthlyStats(
                backtest_id=backtest_id,
                year=stat['year'],
                month=stat['month'],
                monthly_return=Decimal(str(stat.get('return_rate', 0))),
                cumulative_return=Decimal(str(stat.get('cumulative_return', 0))),
                monthly_volatility=Decimal(str(stat.get('volatility', 0))),
                max_drawdown=Decimal(str(stat.get('max_drawdown', 0))),
                total_trades=stat.get('trade_count', 0),
                winning_trades=stat.get('winning_trades', 0),
                losing_trades=stat.get('losing_trades', 0),
                win_rate=Decimal(str(stat.get('win_rate', 0))),
                avg_positions=Decimal(str(stat.get('avg_positions', 0))),
                turnover_rate=Decimal(str(stat.get('turnover_rate', 0))),
                start_capital=Decimal(str(stat.get('start_capital', 0))),
                end_capital=Decimal(str(stat.get('end_capital', 0)))
            )
            self.db.add(monthly)

        logger.info(f"  - {len(monthly_stats)}개 월별 통계 저장")

    async def _save_yearly_stats(self, backtest_id: UUID, yearly_stats: List[Dict]):
        """연도별 통계 저장"""
        from app.models.backtest_extended import BacktestYearlyStats

        for stat in yearly_stats:
            yearly = BacktestYearlyStats(
                backtest_id=backtest_id,
                year=stat['year'],
                yearly_return=Decimal(str(stat.get('return_rate', 0))),
                cumulative_return=Decimal(str(stat.get('cumulative_return', 0))),
                yearly_volatility=Decimal(str(stat.get('volatility', 0))),
                sharpe_ratio=Decimal(str(stat.get('sharpe_ratio', 0))),
                sortino_ratio=Decimal(str(stat.get('sortino_ratio', 0))),
                max_drawdown=Decimal(str(stat.get('max_drawdown', 0))),
                total_trades=stat.get('trade_count', 0),
                win_rate=Decimal(str(stat.get('win_rate', 0))),
                profit_factor=Decimal(str(stat.get('profit_factor', 1))),
                start_capital=Decimal(str(stat.get('start_capital', 0))),
                end_capital=Decimal(str(stat.get('end_capital', 0))),
                peak_capital=Decimal(str(stat.get('peak_capital', 0)))
            )
            self.db.add(yearly)

        logger.info(f"  - {len(yearly_stats)}개 연도별 통계 저장")

    async def _save_drawdown_periods(self, backtest_id: UUID, drawdown_periods: List[Dict]):
        """낙폭 기간 저장"""
        from app.models.backtest_extended import BacktestDrawdownPeriod

        for period in drawdown_periods:
            drawdown = BacktestDrawdownPeriod(
                backtest_id=backtest_id,
                start_date=period['start_date'],
                end_date=period.get('end_date'),
                duration_days=period['duration'],
                peak_value=Decimal(str(period['peak_value'])),
                trough_value=Decimal(str(period['trough_value'])),
                drawdown_amount=Decimal(str(period['drawdown_amount'])),
                drawdown_pct=Decimal(str(period['drawdown_pct'])),
                is_recovered=period.get('is_recovered', False),
                recovery_days=period.get('recovery_days')
            )
            self.db.add(drawdown)

        logger.info(f"  - {len(drawdown_periods)}개 낙폭 기간 저장")

    async def _save_factor_contributions(self, backtest_id: UUID, factor_contributions: Dict[str, Dict]):
        """팩터 기여도 저장"""
        from app.models.backtest_extended import BacktestFactorContribution

        for factor_name, contrib in factor_contributions.items():
            factor = BacktestFactorContribution(
                backtest_id=backtest_id,
                factor_name=factor_name,
                factor_category=self._get_factor_category(factor_name),
                total_trades=contrib.get('total_trades', 0),
                winning_trades=contrib.get('winning_trades', 0),
                win_rate=Decimal(str(contrib.get('win_rate', 0))),
                total_return=Decimal(str(contrib.get('total_profit', 0))),
                avg_return=Decimal(str(contrib.get('avg_profit', 0))),
                contribution_score=Decimal(str(contrib.get('contribution_score', 0))),
                importance_rank=contrib.get('importance_rank', 999),
                correlation_with_return=None  # 추후 계산
            )
            self.db.add(factor)

        logger.info(f"  - {len(factor_contributions)}개 팩터 기여도 저장")

    async def _save_legacy_tables(self, backtest_id: UUID, result: Any):
        """기존 테이블 저장 (하위 호환성)"""
        from app.models.backtest import (
            BacktestSession, BacktestCondition, BacktestStatistics,
            BacktestDailySnapshot, BacktestTrade, BacktestHolding
        )

        # 1. 백테스트 세션
        session = BacktestSession(
            backtest_id=backtest_id,
            backtest_name=result.backtest_name,
            status=result.status,
            start_date=result.statistics.start_date,
            end_date=result.statistics.end_date,
            initial_capital=result.statistics.initial_capital,
            rebalance_frequency=result.settings.rebalance_frequency,
            max_positions=result.settings.max_positions,
            position_sizing=result.settings.position_sizing,
            benchmark=result.settings.benchmark or "NONE",
            commission_rate=Decimal(str(result.settings.commission_rate)),
            tax_rate=Decimal(str(result.settings.tax_rate)),
            slippage=Decimal(str(result.settings.slippage)),
            created_at=result.created_at,
            completed_at=result.completed_at
        )
        self.db.add(session)

        # 2. 통계
        stats = BacktestStatistics(
            backtest_id=backtest_id,
            total_return=Decimal(str(result.statistics.total_return)),
            annualized_return=Decimal(str(result.statistics.annualized_return)),
            benchmark_return=Decimal('0'),  # 벤치마크 제외
            excess_return=Decimal('0'),
            max_drawdown=Decimal(str(result.statistics.max_drawdown)),
            volatility=Decimal(str(result.statistics.volatility)),
            downside_volatility=Decimal(str(result.statistics.downside_volatility)),
            sharpe_ratio=Decimal(str(result.statistics.sharpe_ratio)),
            sortino_ratio=Decimal(str(result.statistics.sortino_ratio)),
            calmar_ratio=Decimal(str(result.statistics.calmar_ratio)),
            total_trades=result.statistics.total_trades,
            winning_trades=result.statistics.winning_trades,
            losing_trades=result.statistics.losing_trades,
            win_rate=Decimal(str(result.statistics.win_rate)),
            avg_win=Decimal(str(result.statistics.avg_win)),
            avg_loss=Decimal(str(result.statistics.avg_loss)),
            profit_loss_ratio=Decimal(str(result.statistics.profit_loss_ratio)),
            initial_capital=result.statistics.initial_capital,
            final_capital=result.statistics.final_capital,
            peak_capital=result.statistics.peak_capital,
            start_date=result.statistics.start_date,
            end_date=result.statistics.end_date,
            trading_days=result.statistics.trading_days
        )
        self.db.add(stats)

        # 3. 일별 스냅샷
        for snapshot in result.daily_performance:
            daily = BacktestDailySnapshot(
                backtest_id=backtest_id,
                snapshot_date=snapshot['date'],
                portfolio_value=Decimal(str(snapshot['portfolio_value'])),
                cash_balance=Decimal(str(snapshot['cash_balance'])),
                invested_amount=Decimal(str(snapshot['invested_amount'])),
                daily_return=Decimal(str(snapshot['daily_return'])),
                cumulative_return=Decimal(str(snapshot['cumulative_return'])),
                drawdown=Decimal(str(snapshot['drawdown'])),
                benchmark_return=Decimal('0'),
                trade_count=snapshot.get('trade_count', 0)
            )
            self.db.add(daily)

        # 4. 거래 내역
        for trade in result.trades:
            trade_record = BacktestTrade(
                backtest_id=backtest_id,
                trade_date=trade['date'],
                trade_type=trade['trade_type'],
                stock_code=trade['stock_code'],
                stock_name=trade['stock_name'],
                quantity=trade['quantity'],
                price=Decimal(str(trade['price'])),
                amount=Decimal(str(trade['amount'])),
                commission=Decimal(str(trade.get('commission', 0))),
                tax=Decimal(str(trade.get('tax', 0))),
                profit=Decimal(str(trade.get('profit', 0))) if trade['trade_type'] == 'SELL' else None,
                profit_rate=Decimal(str(trade.get('profit_rate', 0))) if trade['trade_type'] == 'SELL' else None,
                hold_days=trade.get('hold_days') if trade['trade_type'] == 'SELL' else None,
                factors=trade.get('factors'),
                selection_reason=trade.get('selection_reason')
            )
            self.db.add(trade_record)

        # 5. 최종 보유 종목
        for holding in result.holdings:
            hold = BacktestHolding(
                backtest_id=backtest_id,
                stock_code=holding['stock_code'],
                stock_name=holding['stock_name'],
                quantity=holding['quantity'],
                avg_price=Decimal(str(holding['avg_price'])),
                current_price=Decimal(str(holding['current_price'])),
                value=Decimal(str(holding['value'])),
                profit=Decimal(str(holding['profit'])),
                profit_rate=Decimal(str(holding['profit_rate'])),
                weight=Decimal(str(holding['weight'])),
                buy_date=holding['buy_date'],
                hold_days=holding['hold_days'],
                factors=holding.get('factors')
            )
            self.db.add(hold)

        logger.info(f"  - 기존 테이블 저장 완료")

    def _get_factor_category(self, factor_name: str) -> str:
        """팩터 카테고리 분류"""
        value_factors = ['PER', 'PBR', 'PCR', 'PSR', 'PEG', 'EV_EBITDA', 'EV_SALES']
        quality_factors = ['ROE', 'ROA', 'ROI', 'GPM', 'OPM', 'NPM']
        growth_factors = ['REVENUE_GROWTH', 'EARNINGS_GROWTH', 'ASSET_GROWTH']
        momentum_factors = ['MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M']
        stability_factors = ['DEBT_RATIO', 'CURRENT_RATIO', 'QUICK_RATIO']

        if factor_name in value_factors:
            return 'VALUE'
        elif factor_name in quality_factors:
            return 'QUALITY'
        elif factor_name in growth_factors:
            return 'GROWTH'
        elif factor_name in momentum_factors:
            return 'MOMENTUM'
        elif factor_name in stability_factors:
            return 'STABILITY'
        else:
            return 'OTHER'