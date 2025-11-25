"""
백테스트 엔진 설정 파일
Phase 0 최적화: 즉시 적용 가능한 개선사항
"""

import os
from datetime import timedelta

# ==================== 성능 설정 ====================

# 멀티프로세싱 설정
# Phase 0 최적화: False로 변경 (가짜 멀티프로세싱 비활성화)
# 실제로는 ProcessPool 없이 이름만 멀티프로세싱이므로 비활성화하는게 더 빠름
USE_MULTIPROCESSING = False  # 변경: True → False

# Redis 캐시 설정
# Phase 0 최적화: True 유지 (캐시 활성화로 2회차부터 50-70% 속도 향상)
USE_CACHE = True  # 유지: True

# ==================== 데이터 로드 설정 ====================

# 가격 데이터 lookback 기간 설정
# Phase 0 최적화: 365일 → 필요한 만큼만
def get_lookback_days(required_factors: list = None) -> int:
    """
    필요한 팩터에 따라 lookback 기간 동적 계산

    Args:
        required_factors: 필요한 팩터 리스트

    Returns:
        lookback 일수
    """
    if not required_factors:
        return 60  # 기본값: 60일

    # 팩터별 필요 기간 체크
    lookback_days = 20  # 기본 이동평균용

    for factor in required_factors:
        factor_upper = factor.upper()
        if 'MOMENTUM' in factor_upper:
            # 모멘텀 팩터는 60일 필요
            lookback_days = max(lookback_days, 60)
        elif 'MA_240' in factor_upper or 'TREND_240' in factor_upper:
            # 240일 이동평균
            lookback_days = max(lookback_days, 240)
        elif 'MA_120' in factor_upper or 'TREND_120' in factor_upper:
            # 120일 이동평균
            lookback_days = max(lookback_days, 120)
        elif 'MA_60' in factor_upper or 'TREND_60' in factor_upper:
            # 60일 이동평균
            lookback_days = max(lookback_days, 60)
        elif 'VOLATILITY' in factor_upper:
            # 변동성 계산용
            lookback_days = max(lookback_days, 60)

    return lookback_days

# 기본 lookback 설정 (환경변수로 오버라이드 가능)
DEFAULT_LOOKBACK_DAYS = int(os.getenv('BACKTEST_LOOKBACK_DAYS', '60'))

# ==================== 진행률 업데이트 설정 ====================

# 진행률 업데이트 주기
# Phase 0 최적화: 매일 → 10% 단위로 변경 (DB I/O 90% 감소)
PROGRESS_UPDATE_INTERVAL = 10  # 변경: 1 → 10 (10% 단위로만 업데이트)

# 진행률 커밋 주기
# Phase 0 최적화: 진행률 업데이트마다 즉시 커밋 (UI 실시간 반영)
# 변경 이유: 50일로 설정 시 진행 중에 커밋이 안돼서 UI에 진행률이 표시되지 않음
PROGRESS_COMMIT_INTERVAL = 1  # 변경: 50 → 1 (진행률 업데이트마다 커밋)

# ==================== 캐시 설정 ====================

# 캐시 TTL (Time To Live) 설정
CACHE_TTL_SECONDS = {
    'price_data': 3600,      # 1시간
    'financial_data': 7200,  # 2시간
    'factor_data': 1800,     # 30분
    'stock_info': 86400,     # 24시간
}

# 캐시 키 생성 설정
# Phase 0 최적화: 필터 정보를 캐시 키에 포함
def get_cache_key(data_type: str, start_date, end_date,
                  target_themes: list = None, target_stocks: list = None,
                  target_universes: list = None) -> str:
    """
    필터 정보를 포함한 캐시 키 생성

    Args:
        data_type: 데이터 타입 (price_data, financial_data 등)
        start_date: 시작일
        end_date: 종료일
        target_themes: 테마 필터
        target_stocks: 종목 필터
        target_universes: 유니버스 필터

    Returns:
        캐시 키 문자열
    """
    # 필터 정보를 정렬하여 일관된 키 생성
    themes_str = ','.join(sorted(target_themes or []))
    stocks_str = ','.join(sorted(target_stocks or []))[:100]  # 너무 길면 잘라냄
    universes_str = ','.join(sorted(target_universes or []))

    # 필터 해시 생성 (긴 필터 리스트의 경우)
    import hashlib
    filter_str = f"{themes_str}:{stocks_str}:{universes_str}"
    filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8] if filter_str != "::" else "nofilter"

    return f"{data_type}:{start_date}:{end_date}:{filter_hash}"

# ==================== 배치 처리 설정 ====================

# 팩터 계산 배치 크기
FACTOR_CALC_BATCH_SIZE = 100  # 종목 100개씩 배치 처리

# DB INSERT 배치 크기
# Phase 0 최적화: 단건 INSERT → 배치 INSERT
DB_INSERT_BATCH_SIZE = 1000  # 변경: 1 → 1000

# ==================== 성능 모니터링 설정 ====================

# 성능 모니터링 활성화
ENABLE_PERFORMANCE_MONITORING = bool(os.getenv('ENABLE_MONITORING', 'true').lower() == 'true')

# 성능 로그 레벨
PERFORMANCE_LOG_LEVEL = os.getenv('PERF_LOG_LEVEL', 'INFO')

# ==================== 최적화 모드 설정 ====================

# 극한 최적화 모드 (실험적)
ENABLE_EXTREME_OPTIMIZATION = False

# Numba JIT 컴파일 사용
ENABLE_NUMBA_JIT = True

# Polars 벡터화 사용
ENABLE_POLARS_VECTORIZATION = True

# ==================== 디버그 설정 ====================

# 디버그 모드
DEBUG_MODE = os.getenv('BACKTEST_DEBUG', 'false').lower() == 'true'

# 상세 로깅
VERBOSE_LOGGING = os.getenv('VERBOSE_LOG', 'false').lower() == 'true'