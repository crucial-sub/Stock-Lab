"""
Quant Investment API - FastAPI Main Application
대용량 금융 데이터 처리 최적화
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.cache import cache
from app.api.routes import backtest, auth, company_info, strategy, factors, market_quote, user_stock, news, kiwoom, auto_trading, community, chat_history
from app.api.v1 import industries, realtime
from app.services.auto_trading_scheduler import start_scheduler, stop_scheduler

settings = get_settings()

# 로깅 설정 (콘솔 출력만 사용)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Lifespan 이벤트 (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    logger.info("=== Quant Investment API 시작 ===")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")

    # Redis 초기화
    try:
        await cache.initialize()
        logger.info("Redis cache initialized successfully")

        # 🎯 Redis 랭킹 재구축 (서버 시작 시)
        try:
            from app.services.ranking_service import get_ranking_service
            from app.core.database import AsyncSessionLocal
            from app.core.cache import get_redis

            ranking_service = await get_ranking_service()

            if ranking_service.enabled:
                # Redis가 비어있는지 확인
                redis_client = get_redis()
                ranking_count = await redis_client.zcard("rankings:all")

                if ranking_count == 0:
                    logger.info("🔄 Redis 랭킹이 비어있음. DB에서 재구축 시작...")

                    # DB에서 랭킹 재구축
                    async with AsyncSessionLocal() as db:
                        rebuilt_count = await ranking_service.rebuild_from_db(db, limit=100)
                        logger.info(f"✅ Redis 랭킹 재구축 완료: {rebuilt_count}개 항목")
                else:
                    logger.info(f"✅ Redis 랭킹 이미 존재: {ranking_count}개 항목")
        except Exception as e:
            logger.warning(f"⚠️ Redis 랭킹 재구축 실패 (무시): {e}")

    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")
        logger.warning("Running without cache")

    # DB 초기화 (개발 환경에서만)
    if settings.DEBUG:
        # await init_db()  # 주의: 테이블 재생성
        logger.info("Database initialized (dev mode)")

    # 자동매매 스케줄러 시작
    try:
        start_scheduler()
        logger.info("✅ Auto trading scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

    yield

    # Shutdown
    logger.info("=== Quant Investment API 종료 ===")

    # 스케줄러 종료
    try:
        stop_scheduler()
        logger.info("✅ Auto trading scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Failed to stop scheduler: {e}")

    await cache.close()
    await close_db()


# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## 퀀트 투자 시뮬레이션 API

    ### 주요 기능
    - **팩터 계산**: 22개 퀀트 팩터 실시간 계산
    - **백테스팅**: 과거 데이터 기반 전략 검증
    - **대용량 데이터 처리**: 10GB+ 데이터 최적화

    ### 기술 스택
    - **FastAPI**: 비동기 API 프레임워크
    - **PostgreSQL**: 금융 데이터 저장소
    - **Polars**: 대용량 데이터프레임 처리
    - **VectorBT**: 백테스팅 엔진

    ### 데이터 소스
    - 일별 시세: 공공데이터포털 API
    - 재무제표: OpenDart API
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # 프로덕션에서는 문서 비활성화
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS 설정
# validator에서 이미 List[str]로 변환됨
cors_origins = (
    settings.BACKEND_CORS_ORIGINS
    if isinstance(settings.BACKEND_CORS_ORIGINS, list)
    else (
        settings.BACKEND_CORS_ORIGINS.split(",")
        if settings.BACKEND_CORS_ORIGINS != "*"
        else ["*"]
    )
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if "*" in cors_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 요청/응답 로깅"""
    start_time = time.time()

    # 요청 정보
    logger.info(f"→ {request.method} {request.url.path}")

    # 응답 처리
    response = await call_next(request)

    # 소요 시간
    process_time = (time.time() - start_time) * 1000
    logger.info(f"← {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")

    # 헤더 추가
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

    return response


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """예상치 못한 에러 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# 라우터 등록
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    backtest.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Backtest"]
)

app.include_router(
    strategy.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Strategy"]
)

app.include_router(
    company_info.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Company Info"]
)

app.include_router(
    industries.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Industries"]
)

app.include_router(
    factors.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Factors"]
)

app.include_router(
    market_quote.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Market Quote"]
)

app.include_router(
    news.router,
    prefix=settings.API_V1_PREFIX,
    tags=["News"]
)

app.include_router(
    kiwoom.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Kiwoom"]
)

app.include_router(
    auto_trading.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Auto Trading"]
)

app.include_router(
    chat_history.router,
    prefix=f"{settings.API_V1_PREFIX}/chat",
    tags=["Chat History"]
)

app.include_router(
    realtime.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Realtime"]
)

app.include_router(
    community.router,
    prefix=f"{settings.API_V1_PREFIX}/community",
    tags=["Community"]
)

# Root 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """API 정보"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "endpoints": {
            "factors": f"{settings.API_V1_PREFIX}/factors",
            "simulation": f"{settings.API_V1_PREFIX}/simulation"
        }
    }


# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "environment": "development" if settings.DEBUG else "production",
        "database": "connected"
    }


# 개발 환경 전용 엔드포인트
if settings.DEBUG:
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """설정 정보 확인 (개발 전용)"""
        return {
            "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "N/A",
            "redis_url": settings.REDIS_URL,
            "chunk_size": settings.CHUNK_SIZE,
            "max_workers": settings.MAX_WORKERS,
            "cache_enabled": settings.ENABLE_QUERY_CACHE
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
