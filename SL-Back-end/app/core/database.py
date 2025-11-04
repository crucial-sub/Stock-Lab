"""
대용량 데이터 처리를 위한 데이터베이스 연결 설정
- 비동기 SQLAlchemy (asyncpg)
- 커넥션 풀링
- 쿼리 최적화
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text
from typing import AsyncGenerator
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 비동기 엔진 생성 (대용량 데이터 처리 최적화)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO if hasattr(settings, 'DATABASE_ECHO') else False,
    pool_size=settings.DATABASE_POOL_SIZE if hasattr(settings, 'DATABASE_POOL_SIZE') else 5,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if hasattr(settings, 'DATABASE_MAX_OVERFLOW') else 10,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT if hasattr(settings, 'DATABASE_POOL_TIMEOUT') else 30,
    pool_recycle=settings.DATABASE_POOL_RECYCLE if hasattr(settings, 'DATABASE_POOL_RECYCLE') else 3600,
    pool_pre_ping=True,  # 커넥션 유효성 검증
)

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 커밋 후 객체 만료 방지
    autoflush=False,  # 자동 플러시 비활성화 (성능 향상)
    autocommit=False,
)

# Base 모델
Base = declarative_base()


# 데이터베이스 세션 의존성
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성으로 사용할 DB 세션 생성기

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# 데이터베이스 초기화
async def init_db():
    """데이터베이스 테이블 생성 (개발용)"""
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # 주의: 모든 테이블 삭제
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")


# 데이터베이스 종료
async def close_db():
    """데이터베이스 연결 종료"""
    await engine.dispose()
    logger.info("Database connections closed")


# PostgreSQL 성능 최적화 설정 (asyncpg 사용 시 비활성화)
# asyncpg는 psycopg2와 다른 드라이버이므로 이벤트 리스너를 다르게 처리해야 함
# 성능 설정은 필요시 각 세션에서 개별적으로 적용

# # 쿼리 성능 모니터링 (개발 환경)
# @event.listens_for(engine.sync_engine, "before_cursor_execute")
# def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
#     """쿼리 실행 전 로깅"""
#     if settings.DEBUG:
#         logger.debug(f"SQL Query: {statement}")


# 대용량 데이터 배치 처리 헬퍼
class BulkInsertHelper:
    """
    대용량 데이터 배치 삽입 헬퍼

    Example:
        async with BulkInsertHelper(session, chunk_size=10000) as bulk:
            await bulk.insert(StockPrice, price_data_list)
    """

    def __init__(self, session: AsyncSession, chunk_size: int = 10000):
        self.session = session
        self.chunk_size = chunk_size

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()

    async def insert(self, model_class, data_list: list):
        """대용량 데이터 청크 단위로 삽입"""
        total = len(data_list)
        for i in range(0, total, self.chunk_size):
            chunk = data_list[i:i + self.chunk_size]
            self.session.add_all([model_class(**data) for data in chunk])
            await self.session.flush()
            logger.info(f"Inserted {min(i + self.chunk_size, total)}/{total} records")

        await self.session.commit()
        logger.info(f"Bulk insert completed: {total} records")


# 읽기 전용 세션 (분석/백테스팅용 - 트랜잭션 오버헤드 최소화)
async def get_readonly_db() -> AsyncGenerator[AsyncSession, None]:
    """
    읽기 전용 세션 (백테스팅, 팩터 계산용)
    - autocommit=True로 트랜잭션 오버헤드 최소화
    """
    async with AsyncSessionLocal() as session:
        try:
            # 읽기 전용 모드 설정
            await session.execute(text("SET TRANSACTION READ ONLY"))
            yield session
        finally:
            await session.close()
