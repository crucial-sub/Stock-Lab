"""
데이터베이스 테이블 생성 스크립트
"""
import asyncio
from app.core.database import engine, Base
from app.models.user import User  # User 모델 import 필수


async def create_tables():
    """모든 테이블 생성"""
    async with engine.begin() as conn:
        # 모든 테이블 생성
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 데이터베이스 테이블이 생성되었습니다!")
    print("생성된 테이블:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")


if __name__ == "__main__":
    asyncio.run(create_tables())
