"""
비활성화된 AutoTradingStrategy와 연결된 SimulationSession의 is_active를 false로 업데이트
"""
import asyncio
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL")

async def fix_inactive_sessions():
    # 엔진 생성
    engine = create_async_engine(DATABASE_URL, echo=True)

    # 세션 생성
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 비활성화된 AutoTradingStrategy의 simulation_session_id 조회
        query = text("""
        SELECT ats.simulation_session_id
        FROM auto_trading_strategies ats
        JOIN simulation_sessions ss ON ss.session_id = ats.simulation_session_id
        WHERE ats.is_active = false AND ss.is_active = true
        """)

        result = await session.execute(query)
        session_ids = [row[0] for row in result.all()]

        print(f"업데이트할 세션 수: {len(session_ids)}")

        if session_ids:
            # SimulationSession 업데이트 (한 번에 하나씩)
            for session_id in session_ids:
                update_query = text("""
                UPDATE simulation_sessions
                SET is_active = false
                WHERE session_id = :session_id
                """)

                await session.execute(update_query, {"session_id": session_id})

            await session.commit()

            print(f"✅ {len(session_ids)}개 세션 업데이트 완료")
        else:
            print("업데이트할 세션이 없습니다.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_inactive_sessions())
