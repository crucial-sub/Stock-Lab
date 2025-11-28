"""
시장 관련 유틸리티 함수
"""
from datetime import datetime, time


def is_market_hours(now: datetime = None) -> bool:
    """
    현재 시각이 한국 주식 시장 거래 시간인지 확인

    Args:
        now: 확인할 시각 (None이면 현재 시각)

    Returns:
        거래 시간이면 True, 아니면 False
    """
    if now is None:
        now = datetime.now()

    # 주말 체크 (토요일=5, 일요일=6)
    if now.weekday() >= 5:
        return False

    # 거래 시간: 09:00 ~ 15:30
    market_open = time(9, 0)
    market_close = time(15, 30)

    current_time = now.time()
    return market_open <= current_time <= market_close


def is_pre_market_hours(now: datetime = None) -> bool:
    """
    장 시작 전 시간인지 확인 (08:00 ~ 08:59)

    Args:
        now: 확인할 시각 (None이면 현재 시각)

    Returns:
        장 시작 전 시간이면 True, 아니면 False
    """
    if now is None:
        now = datetime.now()

    # 주말 체크
    if now.weekday() >= 5:
        return False

    # 장 시작 전: 08:00 ~ 08:59
    pre_market_start = time(8, 0)
    pre_market_end = time(8, 59)

    current_time = now.time()
    return pre_market_start <= current_time <= pre_market_end
