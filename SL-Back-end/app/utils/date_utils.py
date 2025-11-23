"""
날짜 유틸리티 함수
"""
from datetime import date, timedelta
from typing import List


def count_business_days(start_date: date, end_date: date) -> int:
    """
    시작일부터 종료일까지의 영업일 수 계산 (주말 제외)

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        영업일 수 (주말 제외)

    Examples:
        >>> count_business_days(date(2024, 1, 1), date(2024, 1, 5))  # 월~금
        5
        >>> count_business_days(date(2024, 1, 6), date(2024, 1, 7))  # 토~일
        0
    """
    if start_date > end_date:
        return 0

    business_days = 0
    current = start_date

    while current <= end_date:
        # 월요일(0) ~ 금요일(4)만 카운트
        if current.weekday() < 5:
            business_days += 1
        current += timedelta(days=1)

    return business_days


def get_previous_business_day(target_date: date) -> date:
    """
    주어진 날짜의 이전 영업일 반환

    Args:
        target_date: 기준 날짜

    Returns:
        이전 영업일

    Examples:
        >>> get_previous_business_day(date(2024, 1, 8))  # 월요일 -> 금요일
        date(2024, 1, 5)
    """
    current = target_date - timedelta(days=1)

    # 주말이면 금요일까지 되돌아감
    while current.weekday() >= 5:
        current -= timedelta(days=1)

    return current


def get_next_business_day(target_date: date) -> date:
    """
    주어진 날짜의 다음 영업일 반환

    Args:
        target_date: 기준 날짜

    Returns:
        다음 영업일

    Examples:
        >>> get_next_business_day(date(2024, 1, 5))  # 금요일 -> 월요일
        date(2024, 1, 8)
    """
    current = target_date + timedelta(days=1)

    # 주말이면 월요일까지 진행
    while current.weekday() >= 5:
        current += timedelta(days=1)

    return current


def is_business_day(target_date: date) -> bool:
    """
    주어진 날짜가 영업일인지 확인 (주말 제외)

    Args:
        target_date: 확인할 날짜

    Returns:
        영업일 여부 (True: 영업일, False: 주말)

    Examples:
        >>> is_business_day(date(2024, 1, 1))  # 월요일
        True
        >>> is_business_day(date(2024, 1, 6))  # 토요일
        False
    """
    return target_date.weekday() < 5


def get_business_days_in_range(start_date: date, end_date: date) -> List[date]:
    """
    시작일부터 종료일까지의 모든 영업일 리스트 반환

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        영업일 날짜 리스트
    """
    business_days = []
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:
            business_days.append(current)
        current += timedelta(days=1)

    return business_days
