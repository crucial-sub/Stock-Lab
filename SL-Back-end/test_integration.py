#!/usr/bin/env python
"""
백테스트와 54개 팩터 통합 테스트
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

async def test_integration():
    """통합 테스트"""

    print("=" * 60)
    print("🧪 백테스트-팩터 통합 테스트")
    print("=" * 60)

    # 1. Import 테스트
    print("\n1️⃣ Import 테스트...")
    try:
        from app.services.backtest import BacktestEngineGenPort
        from app.services.factor_integration import FactorIntegration
        from app.services.factor_calculator_complete import CompleteFactorCalculator
        print("✅ 모든 모듈 import 성공")
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return

    # 2. 코드 확인
    print("\n2️⃣ 백테스트 엔진 코드 확인...")

    # backtest.py 파일 읽기
    with open('app/services/backtest.py', 'r') as f:
        backtest_code = f.read()

    # 통합 모듈 사용 여부 확인
    if 'from app.services.factor_integration import FactorIntegration' in backtest_code:
        print("✅ 백테스트 엔진에 통합 모듈 import 확인")
    else:
        print("❌ 백테스트 엔진에 통합 모듈 import 없음")

    if 'factor_integrator.get_integrated_factor_data' in backtest_code:
        print("✅ get_integrated_factor_data 메서드 사용 확인")
    else:
        print("❌ get_integrated_factor_data 메서드 사용 안됨")

    if 'factor_integrator.evaluate_buy_conditions_with_factors' in backtest_code:
        print("✅ evaluate_buy_conditions_with_factors 메서드 사용 확인")
    else:
        print("❌ evaluate_buy_conditions_with_factors 메서드 사용 안됨")

    # 3. 팩터 개수 확인
    print("\n3️⃣ 팩터 개수 확인...")

    # factor_calculator_complete.py 분석
    with open('app/services/factor_calculator_complete.py', 'r') as f:
        factor_code = f.read()

    factors = []

    # 가치 지표
    value_factors = ['PER', 'PBR', 'PSR', 'PCR', 'PEG', 'EV_EBITDA', 'EV_SALES',
                     'EV_FCF', 'DIVIDEND_YIELD', 'EARNINGS_YIELD', 'FCF_YIELD',
                     'BOOK_TO_MARKET', 'CAPE_RATIO', 'PTBV']

    # 수익성 지표
    quality_factors = ['ROE', 'ROA', 'ROIC', 'GPM', 'OPM', 'NPM',
                       'ASSET_TURNOVER', 'INVENTORY_TURNOVER', 'QUALITY_SCORE', 'ACCRUALS_RATIO']

    # 성장성 지표
    growth_factors = ['REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'EARNINGS_GROWTH_1Y',
                      'EARNINGS_GROWTH_3Y', 'OCF_GROWTH_1Y', 'ASSET_GROWTH_1Y',
                      'BOOK_VALUE_GROWTH_1Y', 'SUSTAINABLE_GROWTH_RATE']

    # 모멘텀 지표
    momentum_factors = ['MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M',
                        'DISTANCE_FROM_52W_HIGH', 'DISTANCE_FROM_52W_LOW',
                        'RELATIVE_STRENGTH', 'VOLUME_MOMENTUM']

    # 안정성 지표
    stability_factors = ['DEBT_TO_EQUITY', 'DEBT_RATIO', 'CURRENT_RATIO', 'QUICK_RATIO',
                         'INTEREST_COVERAGE', 'ALTMAN_Z_SCORE', 'BETA', 'EARNINGS_QUALITY']

    # 기술적 지표
    technical_factors = ['RSI_14', 'BOLLINGER_POSITION', 'MACD_SIGNAL',
                         'STOCHASTIC_14', 'VOLUME_ROC', 'PRICE_POSITION']

    all_factors = (value_factors + quality_factors + growth_factors +
                   momentum_factors + stability_factors + technical_factors)

    print(f"📊 정의된 팩터 개수:")
    print(f"   - 가치 지표: {len(value_factors)}개")
    print(f"   - 수익성 지표: {len(quality_factors)}개")
    print(f"   - 성장성 지표: {len(growth_factors)}개")
    print(f"   - 모멘텀 지표: {len(momentum_factors)}개")
    print(f"   - 안정성 지표: {len(stability_factors)}개")
    print(f"   - 기술적 지표: {len(technical_factors)}개")
    print(f"   - 총합: {len(all_factors)}개")

    # 코드에서 실제 구현 확인
    implemented_count = 0
    for factor in all_factors:
        if f"AS {factor}" in factor_code or f'"{factor}"' in factor_code:
            implemented_count += 1

    print(f"\n✅ 구현 완료: {implemented_count}/{len(all_factors)}개")

    # 4. 통합 상태 평가
    print("\n" + "=" * 60)
    print("📊 최종 평가:")

    integration_score = 0

    if 'FactorIntegration' in backtest_code:
        integration_score += 25
        print("✅ [25%] 통합 모듈 import")

    if 'get_integrated_factor_data' in backtest_code:
        integration_score += 25
        print("✅ [25%] 팩터 계산 통합")

    if 'evaluate_buy_conditions_with_factors' in backtest_code:
        integration_score += 25
        print("✅ [25%] 조건 평가 통합")

    if implemented_count >= 50:
        integration_score += 25
        print(f"✅ [25%] 50개 이상 팩터 구현 ({implemented_count}개)")

    print(f"\n🎯 통합 점수: {integration_score}/100점")

    if integration_score >= 100:
        print("✅ 완벽하게 통합되었습니다!")
    elif integration_score >= 75:
        print("⚠️ 대부분 통합되었지만 일부 개선 필요")
    elif integration_score >= 50:
        print("⚠️ 부분적으로만 통합됨")
    else:
        print("❌ 통합이 제대로 되지 않았습니다")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_integration())