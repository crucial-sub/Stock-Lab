#!/usr/bin/env python
"""
확장된 백테스트 테이블 생성 스크립트
- 논리식 저장을 위한 컬럼 추가
- 주문/체결/포지션 추적 테이블
- 월별/연도별 통계 테이블
- 낙폭 분석 및 팩터 기여도 테이블
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine
from app.models.backtest_genport_extended import (
    BacktestSessionExtended,
    BacktestOrder,
    BacktestExecution,
    BacktestPosition,
    BacktestPositionHistory,
    BacktestMonthlyStats,
    BacktestYearlyStats,
    BacktestDrawdownPeriod,
    BacktestFactorContribution
)
from app.core.database import Base


async def drop_existing_tables():
    """기존 테이블 삭제"""
    async with engine.begin() as conn:
        print("🗑️ 기존 확장 테이블 삭제 중...")

        tables_to_drop = [
            "backtest_factor_contributions",
            "backtest_drawdown_periods",
            "backtest_yearly_stats",
            "backtest_monthly_stats",
            "backtest_position_history",
            "backtest_positions",
            "backtest_executions",
            "backtest_orders",
            "backtest_sessions_extended"
        ]

        for table in tables_to_drop:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"   - {table} 삭제됨")
            except Exception as e:
                print(f"   - {table} 삭제 실패: {e}")


async def create_extended_tables():
    """확장 테이블 생성"""
    async with engine.begin() as conn:
        print("\n📊 확장 백테스트 테이블 생성 중...")

        # 모든 테이블 생성
        await conn.run_sync(Base.metadata.create_all)

        print("   ✅ 백테스트 세션 (확장) 테이블 생성")
        print("   ✅ 주문 테이블 생성")
        print("   ✅ 체결 테이블 생성")
        print("   ✅ 포지션 테이블 생성")
        print("   ✅ 포지션 히스토리 테이블 생성")
        print("   ✅ 월별 통계 테이블 생성")
        print("   ✅ 연도별 통계 테이블 생성")
        print("   ✅ 낙폭 기간 테이블 생성")
        print("   ✅ 팩터 기여도 테이블 생성")


async def migrate_existing_data():
    """기존 데이터 마이그레이션 (필요시)"""
    async with engine.begin() as conn:
        print("\n🔄 기존 데이터 마이그레이션...")

        # 기존 backtest_sessions 데이터가 있다면 마이그레이션
        result = await conn.execute(
            text("SELECT COUNT(*) FROM backtest_sessions")
        )
        count = result.scalar()

        if count > 0:
            print(f"   - {count}개의 기존 백테스트 세션 발견")

            # 마이그레이션 쿼리
            migration_query = """
            INSERT INTO backtest_sessions_extended (
                backtest_id, backtest_name, status,
                start_date, end_date, initial_capital,
                rebalance_frequency, max_positions, position_sizing,
                commission_rate, tax_rate, slippage,
                created_at, completed_at
            )
            SELECT
                backtest_id, backtest_name, status,
                start_date, end_date, initial_capital,
                rebalance_frequency, max_positions, position_sizing,
                commission_rate, tax_rate, slippage,
                created_at, completed_at
            FROM backtest_sessions
            ON CONFLICT (backtest_id) DO NOTHING
            """

            try:
                await conn.execute(text(migration_query))
                print(f"   ✅ {count}개 세션 마이그레이션 완료")
            except Exception as e:
                print(f"   ❌ 마이그레이션 실패: {e}")
        else:
            print("   - 마이그레이션할 데이터 없음")


async def update_existing_tables():
    """기존 테이블에 컬럼 추가 (ALTER TABLE)"""
    async with engine.begin() as conn:
        print("\n🔧 기존 테이블 업데이트...")

        # BacktestCondition 테이블에 논리식 관련 컬럼 추가
        alter_queries = [
            """
            ALTER TABLE backtest_conditions
            ADD COLUMN IF NOT EXISTS condition_label VARCHAR(10) DEFAULT NULL
            """,
            """
            ALTER TABLE backtest_conditions
            ADD COLUMN IF NOT EXISTS expression_json JSONB DEFAULT NULL
            """,
            """
            ALTER TABLE backtest_sessions
            ADD COLUMN IF NOT EXISTS buy_expression TEXT DEFAULT NULL
            """,
            """
            ALTER TABLE backtest_sessions
            ADD COLUMN IF NOT EXISTS buy_conditions_json JSONB DEFAULT NULL
            """,
            """
            ALTER TABLE backtest_sessions
            ADD COLUMN IF NOT EXISTS sell_conditions_json JSONB DEFAULT NULL
            """,
            """
            ALTER TABLE backtest_sessions
            ADD COLUMN IF NOT EXISTS factor_weights JSONB DEFAULT NULL
            """
        ]

        for query in alter_queries:
            try:
                await conn.execute(text(query))
                print(f"   ✅ 컬럼 추가 성공")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"   - 컬럼이 이미 존재함")
                else:
                    print(f"   ❌ 컬럼 추가 실패: {e}")


async def verify_tables():
    """테이블 생성 확인"""
    async with engine.begin() as conn:
        print("\n🔍 테이블 생성 확인...")

        # 생성된 테이블 목록 확인
        result = await conn.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'backtest%'
            ORDER BY table_name
            """)
        )

        tables = result.fetchall()
        print(f"\n   총 {len(tables)}개의 백테스트 관련 테이블:")
        for table in tables:
            print(f"   - {table[0]}")

        # 각 테이블의 레코드 수 확인
        print("\n📈 테이블별 레코드 수:")
        for table in tables:
            try:
                count_result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM {table[0]}")
                )
                count = count_result.scalar()
                print(f"   - {table[0]}: {count}개")
            except Exception as e:
                print(f"   - {table[0]}: 조회 실패 ({e})")


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 백테스트 확장 테이블 생성 스크립트")
    print("=" * 60)

    try:
        # 1. 기존 확장 테이블 삭제 (개발 중에만)
        # await drop_existing_tables()

        # 2. 확장 테이블 생성
        await create_extended_tables()

        # 3. 기존 테이블 업데이트
        await update_existing_tables()

        # 4. 데이터 마이그레이션
        # await migrate_existing_data()

        # 5. 생성 확인
        await verify_tables()

        print("\n✅ 모든 작업 완료!")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())