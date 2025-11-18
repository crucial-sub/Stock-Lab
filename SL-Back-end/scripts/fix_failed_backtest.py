"""
FAILED 상태인 백테스트를 COMPLETED로 변경
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def fix_status(session_id: str):
    """백테스트 상태를 COMPLETED로 변경"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 상태 업데이트
            result = await session.execute(text("""
                UPDATE simulation_sessions
                SET status = 'COMPLETED', progress = 100
                WHERE session_id = :session_id
                RETURNING session_id, status, progress
            """), {"session_id": session_id})

            await session.commit()

            row = result.fetchone()
            if row:
                print(f"✅ 백테스트 상태 업데이트 성공")
                print(f"   Session ID: {row[0]}")
                print(f"   Status: {row[1]}")
                print(f"   Progress: {row[2]}%")
            else:
                print(f"❌ 백테스트를 찾을 수 없습니다: {session_id}")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "b62f5182-4ef6-4b4b-ba23-a6063db2d266"
    asyncio.run(fix_status(session_id))
