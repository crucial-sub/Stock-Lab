"""
백테스트 WebSocket 실시간 업데이트

시뮬레이션 진행 중 차트 데이터를 실시간으로 클라이언트에 전송
- Delta 프로토콜 지원: 변경된 필드만 전송하여 네트워크 효율성 향상
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional, Any
import json
import logging
from uuid import UUID
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ProgressState:
    """진행 상황 상태 (Delta 비교용)"""
    date: str
    portfolio_value: float
    cash: float
    position_value: float
    daily_return: float
    cumulative_return: float
    progress_percent: int
    current_mdd: float
    buy_count: int
    sell_count: int


class BacktestWebSocketManager:
    """백테스트 WebSocket 연결 관리자"""

    def __init__(self):
        # {backtest_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # {backtest_id: ProgressState} - Delta 비교를 위한 이전 상태 저장
        self._last_progress_state: Dict[str, ProgressState] = {}
        # Delta 모드 활성화 여부 (기본: True)
        self.delta_mode_enabled: bool = True

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
                # 연결 종료 시 상태도 정리
                if backtest_id in self._last_progress_state:
                    del self._last_progress_state[backtest_id]
                logger.info(f"🔌 백테스트 {backtest_id} 모든 연결 종료")
            else:
                logger.info(f"🔌 WebSocket 연결 해제: {backtest_id} (남은 {len(self.active_connections[backtest_id])}개)")

    async def send_preparation_stage(
        self,
        backtest_id: str,
        stage: str,
        stage_number: int,
        total_stages: int,
        message: str = ""
    ):
        """
        백테스트 준비 단계 전송

        Args:
            backtest_id: 백테스트 세션 ID
            stage: 현재 단계 이름 (LOADING_PRICE_DATA, LOADING_FINANCIAL_DATA, CALCULATING_FACTORS, PREPARING_SIMULATION)
            stage_number: 현재 단계 번호 (1-4)
            total_stages: 총 단계 수 (4)
            message: 추가 메시지 (선택)
        """
        if backtest_id not in self.active_connections:
            logger.warning(f"⚠️ 준비 단계 전송 실패: {backtest_id} - 활성 연결 없음")
            return

        logger.info(f"📊 준비 단계 전송: {backtest_id} - [{stage_number}/{total_stages}] {stage}")

        preparation_message = {
            "type": "preparation",
            "stage": stage,
            "stage_number": stage_number,
            "total_stages": total_stages,
            "message": message
        }

        disconnected = set()
        for websocket in self.active_connections[backtest_id]:
            try:
                await websocket.send_json(preparation_message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)

        for ws in disconnected:
            self.disconnect(backtest_id, ws)

    def _calculate_delta(
        self,
        backtest_id: str,
        current_state: ProgressState
    ) -> Optional[Dict[str, Any]]:
        """
        이전 상태와 비교하여 변경된 필드만 추출

        Args:
            backtest_id: 백테스트 세션 ID
            current_state: 현재 진행 상태

        Returns:
            변경된 필드만 포함된 딕셔너리 (변경 없으면 None)
        """
        # 이전 상태가 없으면 Delta 불가 (첫 메시지)
        if backtest_id not in self._last_progress_state:
            return None

        last_state = self._last_progress_state[backtest_id]
        changes: Dict[str, Any] = {}

        # 각 필드 비교 (date는 항상 포함하지 않음 - 메시지 레벨에서 처리)
        if current_state.portfolio_value != last_state.portfolio_value:
            changes["portfolio_value"] = current_state.portfolio_value
        if current_state.cash != last_state.cash:
            changes["cash"] = current_state.cash
        if current_state.position_value != last_state.position_value:
            changes["position_value"] = current_state.position_value
        if current_state.daily_return != last_state.daily_return:
            changes["daily_return"] = current_state.daily_return
        if current_state.cumulative_return != last_state.cumulative_return:
            changes["cumulative_return"] = current_state.cumulative_return
        if current_state.progress_percent != last_state.progress_percent:
            changes["progress_percent"] = current_state.progress_percent
        if current_state.current_mdd != last_state.current_mdd:
            changes["current_mdd"] = current_state.current_mdd
        if current_state.buy_count != last_state.buy_count:
            changes["buy_count"] = current_state.buy_count
        if current_state.sell_count != last_state.sell_count:
            changes["sell_count"] = current_state.sell_count

        return changes if changes else None

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
        """
        진행 상황 업데이트 전송

        Delta 모드가 활성화되면 변경된 필드만 전송하여 네트워크 효율성 향상
        첫 번째 메시지는 항상 전체 데이터로 전송 (기준점 설정)
        """
        if backtest_id not in self.active_connections:
            logger.warning(f"⚠️ WebSocket 전송 실패: {backtest_id} - 활성 연결 없음 (현재 연결: {list(self.active_connections.keys())})")
            return

        # 현재 상태 생성
        current_state = ProgressState(
            date=date,
            portfolio_value=portfolio_value,
            cash=cash,
            position_value=position_value,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
            progress_percent=progress_percent,
            current_mdd=current_mdd,
            buy_count=buy_count,
            sell_count=sell_count
        )

        message: Dict[str, Any]

        # Delta 모드가 활성화되고, 이전 상태가 있으면 Delta 전송 시도
        if self.delta_mode_enabled and backtest_id in self._last_progress_state:
            changes = self._calculate_delta(backtest_id, current_state)

            if changes:
                # 변경분이 있으면 Delta 메시지 전송
                message = {
                    "type": "delta",
                    "date": date,
                    "changes": changes
                }
                logger.info(f"📊 [Delta] WebSocket 전송: {backtest_id} - {date} (변경: {list(changes.keys())})")
            else:
                # 변경분이 없으면 전송하지 않음
                logger.debug(f"📊 [Delta] 변경 없음, 전송 스킵: {backtest_id} - {date}")
                # 상태는 업데이트 (date가 달라졌을 수 있음)
                self._last_progress_state[backtest_id] = current_state
                return
        else:
            # 첫 번째 메시지이거나 Delta 모드가 비활성화된 경우: 전체 데이터 전송
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
            logger.info(f"📊 WebSocket 진행률 전송: {backtest_id} - {progress_percent}%")

        # 현재 상태 저장 (다음 Delta 비교용)
        self._last_progress_state[backtest_id] = current_state

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

        # 완료 시 상태 정리
        if backtest_id in self._last_progress_state:
            del self._last_progress_state[backtest_id]

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

        # 에러 시 상태 정리
        if backtest_id in self._last_progress_state:
            del self._last_progress_state[backtest_id]

        disconnected = set()
        for websocket in self.active_connections[backtest_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)

        for ws in disconnected:
            self.disconnect(backtest_id, ws)

    def reset_delta_state(self, backtest_id: str):
        """
        Delta 상태 초기화 (새 백테스트 시작 시 호출)

        다음 메시지는 전체 데이터로 전송됨
        """
        if backtest_id in self._last_progress_state:
            del self._last_progress_state[backtest_id]
            logger.info(f"🔄 Delta 상태 초기화: {backtest_id}")


# 전역 매니저 인스턴스
ws_manager = BacktestWebSocketManager()
