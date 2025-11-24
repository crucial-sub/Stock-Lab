#!/usr/bin/env python3
"""
캐시 키 생성 테스트 스크립트
워밍업과 백테스트가 동일한 키를 생성하는지 확인
"""
import sys
import os
from datetime import date

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.backtest_cache_optimized import OptimizedCacheManager


def test_cache_key_generation():
    """캐시 키 생성 테스트"""
    print("=" * 80)
    print("🔍 캐시 키 생성 테스트")
    print("=" * 80)

    cache_manager = OptimizedCacheManager()

    # 피터 린치 전략 설정
    test_date = date(2024, 1, 1)
    themes = ["IT서비스", "섬유 / 의류"]
    factors = ["PEG", "ROE", "DEBT_RATIO", "PER"]

    # 백테스트에서 생성될 캐시 키
    cache_key = cache_manager._generate_factor_cache_key(
        calc_date=test_date,
        factor_names=factors,
        target_themes=themes,
        target_stocks=None
    )

    print(f"\n📅 테스트 날짜: {test_date}")
    print(f"📊 테마: {themes}")
    print(f"📈 팩터: {factors}")
    print(f"\n🔑 생성된 캐시 키:")
    print(f"   {cache_key}")

    # 워밍업 스크립트에서 생성될 키
    themes_str = ','.join(sorted(themes))
    expected_key = f"backtest_optimized:factors:{test_date}:{themes_str}"

    print(f"\n🎯 워밍업 스크립트 예상 키:")
    print(f"   {expected_key}")

    # 일치 여부 확인
    if cache_key == expected_key:
        print(f"\n✅ 성공! 키가 일치합니다!")
        print(f"   캐시 히트가 정상 작동할 것입니다.")
        return True
    else:
        print(f"\n❌ 실패! 키가 일치하지 않습니다!")
        print(f"   캐시 히트가 작동하지 않을 것입니다.")
        print(f"\n차이점:")
        print(f"   백테스트: {cache_key}")
        print(f"   워밍업:   {expected_key}")
        return False


def test_multiple_dates():
    """여러 날짜로 테스트"""
    print("\n" + "=" * 80)
    print("🔍 여러 날짜 테스트")
    print("=" * 80)

    cache_manager = OptimizedCacheManager()
    themes = ["IT서비스", "섬유 / 의류"]
    factors = ["PEG", "ROE"]

    test_dates = [
        date(2024, 1, 1),
        date(2024, 2, 1),
        date(2024, 3, 1),
    ]

    print(f"\n테스트 날짜: {len(test_dates)}개")
    for test_date in test_dates:
        cache_key = cache_manager._generate_factor_cache_key(
            calc_date=test_date,
            factor_names=factors,
            target_themes=themes,
            target_stocks=None
        )
        print(f"  {test_date}: {cache_key}")


if __name__ == "__main__":
    print("\n")
    success = test_cache_key_generation()
    test_multiple_dates()

    print("\n" + "=" * 80)
    if success:
        print("✅ 모든 테스트 통과!")
        print("캐시 워밍업과 백테스트가 동일한 키를 사용합니다.")
        sys.exit(0)
    else:
        print("❌ 테스트 실패!")
        print("코드 수정이 필요합니다.")
        sys.exit(1)
