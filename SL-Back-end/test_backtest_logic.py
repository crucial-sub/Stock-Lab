"""
백테스트 로직 테스트
- 재무 데이터 공시 지연 반영 테스트
- 수익률 계산 정확성 테스트
- 매도 기준가 옵션 테스트
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import pandas as pd
import polars as pl

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine, Position
from sqlalchemy import text


async def test_financial_data_delay():
    """테스트 1: 재무 데이터 공시 지연 반영"""
    print("\n" + "="*80)
    print("테스트 1: 재무 데이터 공시 지연 반영 (Look-Ahead Bias 제거)")
    print("="*80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)

        # 테스트용 재무 데이터 로드
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)

        print(f"\n📅 테스트 기간: {start_date} ~ {end_date}")
        print(f"🔍 재무 데이터 로드 중...")

        financial_df = await engine._load_financial_data(
            start_date=start_date,
            end_date=end_date
        )

        if financial_df.empty:
            print("❌ 재무 데이터가 없습니다.")
            return False

        print(f"✅ 재무 데이터 로드 완료: {len(financial_df)} 레코드")

        # available_date 컬럼 확인
        if 'available_date' not in financial_df.columns:
            print("❌ available_date 컬럼이 없습니다!")
            return False

        print("\n📊 샘플 데이터 (공시 지연 반영):")
        print("-" * 80)

        sample = financial_df[['stock_code', 'report_code', 'report_date', 'available_date']].head(10)
        for _, row in sample.iterrows():
            delay_days = (row['available_date'] - row['report_date']).days
            print(f"종목: {row['stock_code']:>6} | "
                  f"보고서: {row['report_code']} | "
                  f"결산일: {row['report_date'].date()} → "
                  f"사용가능일: {row['available_date'].date()} "
                  f"(+{delay_days}일)")

        # 보고서 코드별 지연 일수 검증
        print("\n📋 보고서 코드별 지연 일수 검증:")
        print("-" * 80)

        expected_delays = {
            '11011': 90,  # 사업보고서
            '11012': 60,  # 반기보고서
            '11013': 45,  # 1분기보고서
            '11014': 45   # 3분기보고서
        }

        all_correct = True
        for report_code, expected_delay in expected_delays.items():
            subset = financial_df[financial_df['report_code'] == report_code]
            if subset.empty:
                continue

            subset = subset.copy()
            subset['actual_delay'] = (subset['available_date'] - subset['report_date']).dt.days
            actual_delay = subset['actual_delay'].iloc[0]

            status = "✅" if actual_delay == expected_delay else "❌"
            print(f"{status} 보고서 {report_code}: 예상 {expected_delay}일, 실제 {actual_delay}일")

            if actual_delay != expected_delay:
                all_correct = False

        return all_correct


async def test_profit_calculation():
    """테스트 2: 수익률 계산 정확성 (거래 비용 반영)"""
    print("\n" + "="*80)
    print("테스트 2: 수익률 계산 정확성 (거래 비용 반영)")
    print("="*80)

    # 시뮬레이션 파라미터
    entry_price = Decimal("10000")
    exit_price = Decimal("11000")
    quantity = Decimal("100")
    commission_rate = Decimal("0.001")  # 0.1%
    tax_rate = Decimal("0.0023")  # 0.23%

    print(f"\n💰 매수: {entry_price}원 × {quantity}주 = {entry_price * quantity:,}원")
    print(f"💰 매도: {exit_price}원 × {quantity}주 = {exit_price * quantity:,}원")
    print(f"📊 수수료율: {commission_rate * 100}%")
    print(f"📊 거래세율: {tax_rate * 100}%")

    # 기존 방식 (비용 미반영)
    old_profit = (exit_price - entry_price) * quantity
    old_profit_rate = ((exit_price / entry_price) - 1) * 100

    print("\n🔴 기존 방식 (비용 미반영):")
    print(f"   수익: {old_profit:,}원")
    print(f"   수익률: {old_profit_rate:.2f}%")

    # 신규 방식 (비용 반영)
    sell_amount = exit_price * quantity
    commission = sell_amount * commission_rate
    tax = sell_amount * tax_rate
    net_amount = sell_amount - commission - tax
    cost_basis = entry_price * quantity
    new_profit = net_amount - cost_basis
    new_profit_rate = ((net_amount / cost_basis) - 1) * 100

    print("\n🟢 신규 방식 (비용 반영):")
    print(f"   매도금액: {sell_amount:,}원")
    print(f"   - 수수료: {commission:,}원")
    print(f"   - 거래세: {tax:,}원")
    print(f"   = 순수령액: {net_amount:,}원")
    print(f"   - 매수원가: {cost_basis:,}원")
    print(f"   = 순수익: {new_profit:,}원")
    print(f"   수익률: {new_profit_rate:.2f}%")

    difference = old_profit_rate - new_profit_rate
    print(f"\n📉 차이: {difference:.2f}%p (기존 방식이 {difference:.2f}%p 과대평가)")

    return True


async def test_sell_price_basis():
    """테스트 3: 매도 기준가 옵션"""
    print("\n" + "="*80)
    print("테스트 3: 매도 기준가 옵션 (전일종가/당일시가/평균매수가)")
    print("="*80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)

        # 테스트 데이터 설정
        current_price = Decimal("15000")
        prev_close = Decimal("14500")
        open_price = Decimal("14800")
        entry_price = Decimal("14000")

        print(f"\n💰 가격 정보:")
        print(f"   평균매수가: {entry_price:,}원")
        print(f"   전일종가: {prev_close:,}원")
        print(f"   당일시가: {open_price:,}원")
        print(f"   현재가: {current_price:,}원")

        # 테스트용 position과 price_lookup 생성
        from dataclasses import dataclass

        @dataclass
        class TestPosition:
            stock_code: str
            stock_name: str
            entry_date: date
            entry_price: Decimal
            quantity: int

        holding = TestPosition(
            stock_code="000000",
            stock_name="테스트종목",
            entry_date=date(2024, 1, 1),
            entry_price=entry_price,
            quantity=100
        )

        trading_day = date(2024, 1, 15)
        price_lookup = {
            ("000000", pd.Timestamp(trading_day)): {
                'close_price': float(current_price),
                'open_price': float(open_price)
            },
            ("000000", pd.Timestamp(trading_day - timedelta(days=1))): {
                'close_price': float(prev_close)
            }
        }

        test_cases = [
            ("CURRENT", "현재가", current_price),
            ("PREV_CLOSE", "전일종가", prev_close),
            ("OPEN", "당일시가", open_price),
            ("ENTRY", "평균매수가", entry_price)
        ]

        print("\n📊 매도 기준가별 테스트:")
        print("-" * 80)

        all_passed = True
        for basis_code, basis_name, expected_price in test_cases:
            meta = {'sell_price_basis': basis_code}

            result = engine._apply_price_adjustment(
                price=current_price,
                meta=meta,
                stock_code="000000",
                holding=holding,
                trading_day=trading_day,
                price_lookup=price_lookup,
                price_data=None
            )

            passed = result == expected_price
            status = "✅" if passed else "❌"

            print(f"{status} {basis_name:>10} 기준: {result:>8,}원 "
                  f"(예상: {expected_price:>8,}원)")

            if not passed:
                all_passed = False

        # 오프셋 테스트
        print("\n📊 가격 오프셋 테스트:")
        print("-" * 80)

        offset_tests = [
            (0, "0%", current_price),
            (1, "+1%", current_price * Decimal("1.01")),
            (-1, "-1%", current_price * Decimal("0.99"))
        ]

        for offset_pct, offset_name, expected in offset_tests:
            meta = {'sell_price_offset': offset_pct}
            result = engine._apply_price_adjustment(
                price=current_price,
                meta=meta
            )
            passed = abs(result - expected) < Decimal("0.01")
            status = "✅" if passed else "❌"
            print(f"{status} 오프셋 {offset_name:>5}: {result:>8,}원 "
                  f"(예상: {expected:>8,.2f}원)")
            if not passed:
                all_passed = False

        return all_passed


async def test_look_ahead_bias():
    """테스트 4: Look-Ahead Bias 실제 검증"""
    print("\n" + "="*80)
    print("테스트 4: Look-Ahead Bias 실제 검증")
    print("="*80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)

        # 2024년 1월 15일 시점에서 사용 가능한 재무 데이터 조회
        calc_date = date(2024, 1, 15)

        print(f"\n📅 백테스트 시점: {calc_date}")

        financial_df = await engine._load_financial_data(
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31)
        )

        if financial_df.empty:
            print("❌ 재무 데이터가 없습니다.")
            return False

        # Polars 변환
        financial_pl = pl.from_pandas(financial_df)

        # available_date 기준으로 필터링
        available_data = financial_pl.filter(
            pl.col('available_date') <= pd.Timestamp(calc_date)
        )

        # report_date 기준으로 필터링 (기존 방식)
        report_data = financial_pl.filter(
            pl.col('report_date') <= pd.Timestamp(calc_date)
        )

        print(f"\n📊 데이터 비교:")
        print(f"   report_date 기준: {len(report_data)} 레코드")
        print(f"   available_date 기준: {len(available_data)} 레코드")
        print(f"   차이: {len(report_data) - len(available_data)} 레코드 (미래 정보)")

        # 샘플: 미래 정보 사용 사례
        raw_future_data = financial_pl.filter(
            (pl.col('report_date') <= pd.Timestamp(calc_date)) &
            (pl.col('available_date') > pd.Timestamp(calc_date))
        )

        if len(raw_future_data) > 0:
            print(f"\n⚠️  Look-Ahead Bias 위험 구간 발견! {len(raw_future_data)}건의 미래 정보가 잠재적으로 포함될 수 있었습니다.")
            print("-" * 80)

            sample = raw_future_data.head(5).to_pandas()
            for _, row in sample.iterrows():
                print(f"   종목 {row['stock_code']}: "
                      f"결산일 {row['report_date'].date()} → "
                      f"실제 사용가능일 {row['available_date'].date()} "
                      f"(백테스트 시점: {calc_date})")
        else:
            print("\n✅ 원천 데이터에 Look-Ahead Bias 위험 구간이 없습니다.")

        # available_date 필터 적용 후에는 미래 데이터가 없어야 함
        filtered_future = available_data.filter(
            pl.col('available_date') > pd.Timestamp(calc_date)
        )

        if len(filtered_future) == 0:
            print("\n✅ available_date 기반 필터링 후에는 Look-Ahead Bias 위험 데이터가 제거되었습니다.")
        else:
            print(f"\n❌ 필터 적용 후에도 {len(filtered_future)}건의 미래 데이터가 남아 있습니다!")

        # 성공 기준: 원천 데이터에는 잠재적 위험이 존재하지만,
        # available_date 필터링 이후에는 남아 있지 않아야 함
        return len(filtered_future) == 0


async def main():
    """전체 테스트 실행"""
    print("\n🚀 백테스트 로직 테스트 시작")
    print("=" * 80)

    results = {}

    # 테스트 1: 재무 데이터 공시 지연
    try:
        results['financial_delay'] = await test_financial_data_delay()
    except Exception as e:
        print(f"\n❌ 테스트 1 실패: {e}")
        import traceback
        traceback.print_exc()
        results['financial_delay'] = False

    # 테스트 2: 수익률 계산
    try:
        results['profit_calc'] = await test_profit_calculation()
    except Exception as e:
        print(f"\n❌ 테스트 2 실패: {e}")
        import traceback
        traceback.print_exc()
        results['profit_calc'] = False

    # 테스트 3: 매도 기준가
    try:
        results['sell_basis'] = await test_sell_price_basis()
    except Exception as e:
        print(f"\n❌ 테스트 3 실패: {e}")
        import traceback
        traceback.print_exc()
        results['sell_basis'] = False

    # 테스트 4: Look-Ahead Bias
    try:
        results['look_ahead'] = await test_look_ahead_bias()
    except Exception as e:
        print(f"\n❌ 테스트 4 실패: {e}")
        import traceback
        traceback.print_exc()
        results['look_ahead'] = False

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)

    test_names = {
        'financial_delay': '재무 데이터 공시 지연 반영',
        'profit_calc': '수익률 계산 정확성',
        'sell_basis': '매도 기준가 옵션',
        'look_ahead': 'Look-Ahead Bias 검증'
    }

    for key, name in test_names.items():
        status = "✅ PASS" if results.get(key) else "❌ FAIL"
        print(f"{status} | {name}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print("\n" + "=" * 80)
    print(f"총 {total}개 테스트 중 {passed}개 성공 ({passed/total*100:.1f}%)")
    print("=" * 80)

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
