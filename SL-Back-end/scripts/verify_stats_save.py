"""
통계 저장 확인 스크립트 - 가장 최근 백테스트의 통계 저장 여부 확인
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def verify_stats(session_id: str = None):
    """통계 저장 확인"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 세션 ID가 없으면 가장 최근 백테스트 조회
            if not session_id:
                result = await session.execute(text("""
                    SELECT session_id, status, created_at, completed_at
                    FROM simulation_sessions
                    ORDER BY created_at DESC
                    LIMIT 1
                """))
                row = result.fetchone()
                if not row:
                    print("❌ 백테스트가 없습니다.")
                    return

                session_id = row[0]
                status = row[1]
                created_at = row[2]
                completed_at = row[3]

                print(f"\n{'='*80}")
                print(f"가장 최근 백테스트")
                print(f"{'='*80}")
                print(f"세션 ID: {session_id}")
                print(f"상태: {status}")
                print(f"생성 시간: {created_at}")
                print(f"완료 시간: {completed_at}")

            # SimulationStatistics 조회
            result = await session.execute(text("""
                SELECT
                    total_return,
                    annualized_return,
                    max_drawdown,
                    volatility,
                    sharpe_ratio,
                    total_trades,
                    winning_trades,
                    losing_trades,
                    win_rate,
                    profit_factor,
                    final_capital
                FROM simulation_statistics
                WHERE session_id = :session_id
            """), {"session_id": session_id})

            stats_row = result.fetchone()

            print(f"\n{'='*80}")
            print(f"SimulationStatistics 테이블 확인")
            print(f"{'='*80}")

            if not stats_row:
                print("❌ SimulationStatistics에 데이터가 없습니다!")
            else:
                print("✅ SimulationStatistics 저장됨")
                print(f"  총 수익률: {stats_row[0]:.2f}%")
                print(f"  연환산 수익률: {stats_row[1]:.2f}%")
                print(f"  최대 낙폭: {stats_row[2]:.2f}%")
                print(f"  변동성: {stats_row[3]:.2f}%")
                print(f"  샤프 비율: {stats_row[4]:.2f}")
                print(f"  총 거래: {stats_row[5]}건")
                print(f"  수익 거래: {stats_row[6]}건")
                print(f"  손실 거래: {stats_row[7]}건")
                print(f"  승률: {stats_row[8]:.2f}%")
                print(f"  손익비: {stats_row[9]:.2f}")
                print(f"  최종 자본: {stats_row[10]:,.0f}원")

            # 종목별 통계는 SimulationTrade에서 집계
            result = await session.execute(text("""
                SELECT
                    stock_code,
                    stock_name,
                    COUNT(*) FILTER (WHERE trade_type = 'SELL') as sell_count,
                    SUM(CASE WHEN trade_type = 'SELL' THEN realized_pnl ELSE 0 END) as total_pnl,
                    AVG(CASE WHEN trade_type = 'SELL' AND return_pct IS NOT NULL THEN return_pct ELSE NULL END) as avg_return,
                    COUNT(*) FILTER (WHERE trade_type = 'SELL' AND realized_pnl > 0) * 100.0 /
                        NULLIF(COUNT(*) FILTER (WHERE trade_type = 'SELL'), 0) as win_rate
                FROM simulation_trades
                WHERE session_id = :session_id
                GROUP BY stock_code, stock_name
                ORDER BY total_pnl DESC
            """), {"session_id": session_id})

            stock_stats = result.fetchall()

            print(f"\n{'='*80}")
            print(f"종목별 수익 통계 (SimulationTrade에서 집계)")
            print(f"{'='*80}")

            if not stock_stats:
                print("⚠️  매도 거래가 없어 종목별 통계가 없습니다.")
            else:
                print(f"✅ {len(stock_stats)}개 종목 거래 기록\n")
                print(f"{'종목코드':<10} {'종목명':<20} {'매도':>6} {'총손익':>15} {'평균수익률':>12} {'승률':>8}")
                print("=" * 80)

                for stat in stock_stats[:10]:  # 상위 10개만 표시
                    stock_code = stat[0]
                    stock_name = stat[1][:18] if stat[1] else 'N/A'
                    sell_count = stat[2] or 0
                    total_pnl = float(stat[3]) if stat[3] else 0
                    avg_return = float(stat[4]) if stat[4] else 0
                    win_rate = float(stat[5]) if stat[5] else 0

                    print(f"{stock_code:<10} {stock_name:<20} {sell_count:>6}건 {total_pnl:>15,.0f}원 {avg_return:>11.2f}% {win_rate:>7.1f}%")

            # 거래 내역 확인
            result = await session.execute(text("""
                SELECT COUNT(*) as trade_count
                FROM simulation_trades
                WHERE session_id = :session_id
            """), {"session_id": session_id})

            trade_count = result.fetchone()[0]

            print(f"\n{'='*80}")
            print(f"SimulationTrade 테이블 확인")
            print(f"{'='*80}")
            print(f"총 거래 기록: {trade_count}건")

            # 최종 평가
            print(f"\n{'='*80}")
            print(f"최종 평가")
            print(f"{'='*80}")

            all_ok = True
            if not stats_row:
                print("❌ SimulationStatistics 저장 실패")
                all_ok = False
            else:
                print("✅ SimulationStatistics 저장 성공")

            if trade_count == 0:
                print("❌ SimulationTrade 저장 실패")
                all_ok = False
            else:
                print("✅ SimulationTrade 저장 성공")

            if stock_stats:
                print("✅ 종목별 통계 조회 가능 (SimulationTrade 기반)")
            else:
                print("⚠️  매도 거래가 없어 종목별 통계 없음 (정상일 수 있음)")

            if all_ok:
                print("\n🎉 모든 통계가 정상적으로 저장되었습니다!")
            else:
                print("\n⚠️  일부 통계 저장에 문제가 있습니다.")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(verify_stats(session_id))
