"""
백테스트 성능 모니터링 모듈
실행 시간, 메모리 사용량, 캐시 히트율 등을 측정하고 로깅
"""

import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import json
import psutil

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """백테스트 성능 모니터링 클래스"""

    def __init__(self):
        """성능 메트릭 초기화"""
        self.metrics = {
            # 시간 메트릭 (초 단위)
            'data_load_time': 0.0,
            'factor_calc_time': 0.0,
            'simulation_time': 0.0,
            'save_time': 0.0,
            'total_time': 0.0,

            # 캐시 메트릭
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_hit_rate': 0.0,

            # DB 메트릭
            'db_queries': 0,
            'db_query_time': 0.0,

            # 메모리 메트릭 (GB 단위)
            'memory_start': 0.0,
            'memory_peak': 0.0,
            'memory_current': 0.0,

            # CPU 메트릭 (%)
            'cpu_peak': 0.0,
            'cpu_average': 0.0,

            # 데이터 볼륨 메트릭
            'total_dates': 0,
            'total_stocks': 0,
            'total_factors': 0,
            'total_trades': 0,

            # 타임스탬프
            'start_time': None,
            'end_time': None
        }

        # 임시 측정용 변수
        self._timers = {}
        self._cpu_samples = []
        self.process = psutil.Process()

    def start(self):
        """전체 모니터링 시작"""
        self.metrics['start_time'] = datetime.now().isoformat()
        self.metrics['memory_start'] = self.process.memory_info().rss / (1024 ** 3)  # GB
        self._timers['total'] = time.time()
        logger.info("🚀 성능 모니터링 시작")

    def stop(self):
        """전체 모니터링 종료"""
        if 'total' in self._timers:
            self.metrics['total_time'] = time.time() - self._timers['total']
        self.metrics['end_time'] = datetime.now().isoformat()
        self.metrics['memory_current'] = self.process.memory_info().rss / (1024 ** 3)

        # 캐시 히트율 계산
        total_cache_access = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_cache_access > 0:
            self.metrics['cache_hit_rate'] = self.metrics['cache_hits'] / total_cache_access

        # CPU 평균 계산
        if self._cpu_samples:
            self.metrics['cpu_average'] = sum(self._cpu_samples) / len(self._cpu_samples)

        logger.info("🏁 성능 모니터링 종료")

    def start_timer(self, name: str):
        """특정 작업의 시간 측정 시작"""
        self._timers[name] = time.time()
        logger.debug(f"⏱️ {name} 시작")

    def stop_timer(self, name: str) -> float:
        """특정 작업의 시간 측정 종료"""
        if name not in self._timers:
            return 0.0

        elapsed = time.time() - self._timers[name]

        # 메트릭 업데이트
        metric_key = f"{name}_time"
        if metric_key in self.metrics:
            self.metrics[metric_key] = elapsed

        del self._timers[name]
        logger.debug(f"⏱️ {name} 종료: {elapsed:.2f}초")
        return elapsed

    def record_cache_hit(self):
        """캐시 히트 기록"""
        self.metrics['cache_hits'] += 1

    def record_cache_miss(self):
        """캐시 미스 기록"""
        self.metrics['cache_misses'] += 1

    def record_db_query(self, query_time: float = 0.0):
        """DB 쿼리 기록"""
        self.metrics['db_queries'] += 1
        self.metrics['db_query_time'] += query_time

    def update_memory_usage(self):
        """현재 메모리 사용량 업데이트"""
        current_memory = self.process.memory_info().rss / (1024 ** 3)  # GB
        self.metrics['memory_current'] = current_memory
        self.metrics['memory_peak'] = max(self.metrics['memory_peak'], current_memory)

    def update_cpu_usage(self):
        """현재 CPU 사용률 업데이트"""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self._cpu_samples.append(cpu_percent)
            self.metrics['cpu_peak'] = max(self.metrics['cpu_peak'], cpu_percent)
        except Exception as e:
            logger.debug(f"CPU 측정 실패: {e}")

    def set_data_volume(self, total_dates: int = 0, total_stocks: int = 0,
                       total_factors: int = 0, total_trades: int = 0):
        """데이터 볼륨 메트릭 설정"""
        if total_dates:
            self.metrics['total_dates'] = total_dates
        if total_stocks:
            self.metrics['total_stocks'] = total_stocks
        if total_factors:
            self.metrics['total_factors'] = total_factors
        if total_trades:
            self.metrics['total_trades'] = total_trades

    def get_metrics(self) -> Dict[str, Any]:
        """현재까지의 모든 메트릭 반환"""
        return self.metrics.copy()

    def log_metrics(self):
        """성능 메트릭을 로그로 출력"""
        self.stop()  # 최종 메트릭 계산

        # 포맷팅된 출력
        log_message = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                     백테스트 성능 메트릭 리포트                        ║
╠══════════════════════════════════════════════════════════════════════╣
║ ⏱️  실행 시간 분석                                                     ║
║   • 데이터 로드: {self.metrics['data_load_time']:>10.2f}초                    ║
║   • 팩터 계산:   {self.metrics['factor_calc_time']:>10.2f}초                   ║
║   • 시뮬레이션:  {self.metrics['simulation_time']:>10.2f}초                    ║
║   • 결과 저장:   {self.metrics['save_time']:>10.2f}초                         ║
║   • 전체 시간:   {self.metrics['total_time']:>10.2f}초                        ║
╠══════════════════════════════════════════════════════════════════════╣
║ 💾 캐시 성능                                                          ║
║   • 캐시 히트:   {self.metrics['cache_hits']:>10,}회                          ║
║   • 캐시 미스:   {self.metrics['cache_misses']:>10,}회                        ║
║   • 히트율:      {self.metrics['cache_hit_rate']:>10.1%}                      ║
╠══════════════════════════════════════════════════════════════════════╣
║ 🗄️  DB 성능                                                           ║
║   • 쿼리 수:     {self.metrics['db_queries']:>10,}회                          ║
║   • 쿼리 시간:   {self.metrics['db_query_time']:>10.2f}초                     ║
╠══════════════════════════════════════════════════════════════════════╣
║ 💻 리소스 사용량                                                       ║
║   • 시작 메모리: {self.metrics['memory_start']:>10.2f} GB                     ║
║   • 최대 메모리: {self.metrics['memory_peak']:>10.2f} GB                      ║
║   • 현재 메모리: {self.metrics['memory_current']:>10.2f} GB                   ║
║   • 최대 CPU:    {self.metrics['cpu_peak']:>10.1f}%                          ║
║   • 평균 CPU:    {self.metrics['cpu_average']:>10.1f}%                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ 📊 데이터 볼륨                                                        ║
║   • 거래일 수:   {self.metrics['total_dates']:>10,}일                         ║
║   • 종목 수:     {self.metrics['total_stocks']:>10,}개                        ║
║   • 팩터 수:     {self.metrics['total_factors']:>10,}개                       ║
║   • 거래 수:     {self.metrics['total_trades']:>10,}건                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        logger.info(log_message)

        # JSON 형식으로도 로깅 (파싱 가능한 형태)
        logger.debug(f"성능 메트릭 JSON: {json.dumps(self.metrics, indent=2, default=str)}")

    def export_metrics(self, filepath: str):
        """메트릭을 JSON 파일로 내보내기"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, default=str, ensure_ascii=False)
        logger.info(f"📊 성능 메트릭 저장됨: {filepath}")

    @staticmethod
    def compare_metrics(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """두 메트릭 세트 비교"""
        comparison = {}

        # 시간 비교
        time_keys = ['data_load_time', 'factor_calc_time', 'simulation_time', 'save_time', 'total_time']
        for key in time_keys:
            if key in before and key in after:
                improvement = (before[key] - after[key]) / before[key] * 100 if before[key] > 0 else 0
                comparison[key] = {
                    'before': before[key],
                    'after': after[key],
                    'improvement_percent': improvement
                }

        # 캐시 히트율 비교
        if 'cache_hit_rate' in before and 'cache_hit_rate' in after:
            comparison['cache_hit_rate'] = {
                'before': before['cache_hit_rate'],
                'after': after['cache_hit_rate'],
                'improvement': after['cache_hit_rate'] - before['cache_hit_rate']
            }

        # DB 쿼리 비교
        if 'db_queries' in before and 'db_queries' in after:
            reduction = (before['db_queries'] - after['db_queries']) / before['db_queries'] * 100 if before['db_queries'] > 0 else 0
            comparison['db_queries'] = {
                'before': before['db_queries'],
                'after': after['db_queries'],
                'reduction_percent': reduction
            }

        # 메모리 비교
        if 'memory_peak' in before and 'memory_peak' in after:
            reduction = (before['memory_peak'] - after['memory_peak']) / before['memory_peak'] * 100 if before['memory_peak'] > 0 else 0
            comparison['memory_peak'] = {
                'before': before['memory_peak'],
                'after': after['memory_peak'],
                'reduction_percent': reduction
            }

        return comparison


# 전역 모니터 인스턴스 (선택적 사용)
global_monitor = PerformanceMonitor()