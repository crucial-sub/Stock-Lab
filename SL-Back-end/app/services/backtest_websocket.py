"""
백테스트 WebSocket 실시간 업데이트

시뮬레이션 진행 중 차트 데이터를 실시간으로 클라이언트에 전송
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class BacktestWebSocketManager:
    """백테스트 WebSocket 연결 관리자"""

    def __init__(self):
        # {backtest_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, backtest_id: str, websocket: WebSocket):
        """클라이언트 연결"""
        await websocket.accept()

        if backtest_id not in self.active_connections:
            self.active_connections[backtest_id] = set()

        self.active_connections[backtest_id].add(websocket)
        logger.info(f"✅ WebSocket 연결: {backtest_id} (총 {len(self.active_connections[backtest_id])}개)")

    def disconnect(self, backtest_id: str, websocket: WebSocket):
        """클라이언트 연결 해제"""
        if backtest_id in self.active_connections:
            self.active_connections[backtest_id].discard(websocket)

            if not self.active_connections[backtest_id]:
                del self.active_connections[backtest_id]
                logger.info(f"🔌 백테스트 {backtest_id} 모든 연결 종료")
            else:
                logger.info(f"🔌 WebSocket 연결 해제: {backtest_id} (남은 {len(self.active_connections[backtest_id])}개)")

    async def send_progress(
        self,
        backtest_id: str,
        date: str,
        portfolio_value: float,
        cash: float,
        position_value: float,
        daily_return: float,
        cumulative_return: float,
        progress_percent: int,
        current_mdd: float = 0.0,
        buy_count: int = 0,
        sell_count: int = 0
    ):
        """진행 상황 업데이트 전송"""
        if backtest_id not in self.active_connections:
            logger.warning(f"⚠️ WebSocket 전송 실패: {backtest_id} - 활성 연결 없음 (현재 연결: {list(self.active_connections.keys())})")
            return

        logger.info(f"📊 WebSocket 진행률 전송: {backtest_id} - {progress_percent}%")

        message = {
            "type": "progress",
            "date": date,
            "portfolio_value": portfolio_value,
            "cash": cash,
            "position_value": position_value,
            "daily_return": daily_return,
            "cumulative_return": cumulative_return,
            "progress_percent": progress_percent,
            "current_mdd": current_mdd,
            "buy_count": buy_count,
            "sell_count": sell_count
        }

        # 모든 연결된 클라이언트에게 전송
        disconnected = set()
        for websocket in self.active_connections[backtest_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)

        # 끊긴 연결 정리
        for ws in disconnected:
            self.disconnect(backtest_id, ws)

    async def send_trade(
        self,
        backtest_id: str,
        trade: Dict
    ):
        """거래 내역 전송"""
        if backtest_id not in self.active_connections:
            return

        message = {
            "type": "trade",
            "trade": trade
        }

        disconnected = set()
        for websocket in self.active_connections[backtest_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)

        for ws in disconnected:
            self.disconnect(backtest_id, ws)

    async def send_completion(
        self,
        backtest_id: str,
        statistics: Dict,
        summary: str = None
    ):
        """백테스트 완료 알림 (summary 포함)"""
        if backtest_id not in self.active_connections:
            return

        message = {
            "type": "completed",
            "statistics": statistics,
            "summary": summary
        }

        logger.info(f"✅ WebSocket 완료 전송: {backtest_id} (summary: {len(summary) if summary else 0}글자)")

        disconnected = set()
        for websocket in self.active_connections[backtest_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)

        for ws in disconnected:
            self.disconnect(backtest_id, ws)

    async def send_error(
        self,
        backtest_id: str,
        error_message: str
    ):
        """에러 전송"""
        if backtest_id not in self.active_connections:
            return

        message = {
            "type": "error",
            "message": error_message
        }

        disconnected = set()
        for websocket in self.active_connections[backtest_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)

        for ws in disconnected:
            self.disconnect(backtest_id, ws)


# 전역 매니저 인스턴스
ws_manager = BacktestWebSocketManager()
