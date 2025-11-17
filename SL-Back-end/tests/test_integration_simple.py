#!/usr/bin/env python
"""
백테스트와 54개 팩터 통합 간단 테스트
"""

print("=" * 60)
print("🧪 백테스트-팩터 통합 테스트")
print("=" * 60)

# 1. 코드 파일 확인
print("\n1️⃣ 백테스트 엔진 코드 확인...")

with open('app/services/backtest.py', 'r') as f:
    backtest_code = f.read()

# 통합 모듈 사용 여부 확인
checks = {
    'FactorIntegration import': 'from app.services.factor_integration import FactorIntegration' in backtest_code,
    '54개 팩터 계산': 'factor_integrator.get_integrated_factor_data' in backtest_code,
    '매수 조건 평가': 'factor_integrator.evaluate_buy_conditions_with_factors' in backtest_code,
    '복합 스코어 계산': 'factor_integrator.rank_stocks_by_composite_score' in backtest_code,
}

for check, result in checks.items():
    if result:
        print(f"✅ {check}")
    else:
        print(f"❌ {check}")

# 2. 팩터 개수 확인
print("\n2️⃣ 팩터 개수 확인...")

with open('app/services/factor_calculator_complete.py', 'r') as f:
    factor_code = f.read()

# 모든 팩터 리스트
all_factors = [
    # 가치 지표 (14개)
    'PER', 'PBR', 'PSR', 'PCR', 'PEG', 'EV_EBITDA', 'EV_SALES',
    'EV_FCF', 'DIVIDEND_YIELD', 'EARNINGS_YIELD', 'FCF_YIELD',
    'BOOK_TO_MARKET', 'CAPE_RATIO', 'PTBV',
    # 수익성 지표 (10개)
    'ROE', 'ROA', 'ROIC', 'GPM', 'OPM', 'NPM',
    'ASSET_TURNOVER', 'INVENTORY_TURNOVER', 'QUALITY_SCORE', 'ACCRUALS_RATIO',
    # 성장성 지표 (8개)
    'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'EARNINGS_GROWTH_1Y',
    'EARNINGS_GROWTH_3Y', 'OCF_GROWTH_1Y', 'ASSET_GROWTH_1Y',
    'BOOK_VALUE_GROWTH_1Y', 'SUSTAINABLE_GROWTH_RATE',
    # 모멘텀 지표 (8개)
    'MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M',
    'DISTANCE_FROM_52W_HIGH', 'DISTANCE_FROM_52W_LOW',
    'RELATIVE_STRENGTH', 'VOLUME_MOMENTUM',
    # 안정성 지표 (8개)
    'DEBT_TO_EQUITY', 'DEBT_RATIO', 'CURRENT_RATIO', 'QUICK_RATIO',
    'INTEREST_COVERAGE', 'ALTMAN_Z_SCORE', 'BETA', 'EARNINGS_QUALITY',
    # 기술적 지표 (6개)
    'RSI_14', 'BOLLINGER_POSITION', 'MACD_SIGNAL',
    'STOCHASTIC_14', 'VOLUME_ROC', 'PRICE_POSITION',
]

# 구현된 팩터 카운트
implemented = 0
for factor in all_factors:
    if f"AS {factor}" in factor_code or f'"{factor}"' in factor_code:
        implemented += 1

print(f"📊 총 {len(all_factors)}개 팩터 중 {implemented}개 구현됨")

# 3. 기존 방식 vs 통합 방식 비교
print("\n3️⃣ 기존 vs 통합 방식 비교...")

# 기존 _calculate_all_factors 사용 여부
if '_calculate_all_factors' in backtest_code and 'await self._calculate_all_factors' in backtest_code:
    print("⚠️ 기존 방식 (_calculate_all_factors) 여전히 폴백으로 사용 중")

# 통합 모듈 우선 사용 여부
if 'factor_integrator = FactorIntegration(self.db)' in backtest_code:
    print("✅ 통합 모듈 우선 사용")

# 4. 최종 평가
print("\n" + "=" * 60)
print("📊 최종 평가:")

score = sum(1 for result in checks.values() if result) * 25

if score >= 100:
    print(f"✅ 통합 점수: {score}/100 - 완벽하게 통합됨!")
elif score >= 75:
    print(f"⚠️ 통합 점수: {score}/100 - 대부분 통합됨")
elif score >= 50:
    print(f"⚠️ 통합 점수: {score}/100 - 부분적으로 통합됨")
else:
    print(f"❌ 통합 점수: {score}/100 - 통합 미완성")

# 5. 추가 확인 사항
print("\n📝 추가 확인:")

# 통합 모듈 파일 존재 여부
import os
if os.path.exists('app/services/factor_integration.py'):
    print("✅ factor_integration.py 파일 존재")
else:
    print("❌ factor_integration.py 파일 없음")

if os.path.exists('app/services/factor_calculator_complete.py'):
    print("✅ factor_calculator_complete.py 파일 존재")
else:
    print("❌ factor_calculator_complete.py 파일 없음")

print("=" * 60)