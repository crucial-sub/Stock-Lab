from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Database
    DATABASE_URL: str
    DATABASE_SYNC_URL: str = ""  # 동기 URL (선택사항)
    DATABASE_ECHO: bool = False  # SQL 로깅 (선택사항)
    DATABASE_POOL_SIZE: int = 50  # 20 → 50 (동시 백테스트 지원)
    DATABASE_MAX_OVERFLOW: int = 100  # 40 → 100 (피크 타임 대응)
    DATABASE_POOL_TIMEOUT: int = 60  # 30 → 60 (타임아웃 여유)
    DATABASE_POOL_RECYCLE: int = 1800  # 3600 → 1800 (더 자주 재활용)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_TTL: int = 3600
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    CACHE_PREFIX: str = "quant"
    ENABLE_CACHE: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Quant Investment API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7일 (7 * 24 * 60)

    # Performance
    CHUNK_SIZE: int = 10000  # 대용량 데이터 청크 크기
    MAX_WORKERS: int = 4
    ENABLE_QUERY_CACHE: bool = True

    # Backtesting
    BACKTEST_MAX_CONCURRENT_JOBS: int = 2
    BACKTEST_MEMORY_LIMIT_GB: int = 8

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://54.180.34.167:3000",  # EC2 public IP
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/quant_api.log"

    # External APIs
    DART_API_KEY: str = ""  # OpenDart API Key

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤"""
    return Settings()


# 전역 settings 인스턴스
settings = get_settings()
