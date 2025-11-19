from pydantic_settings import BaseSettings
from functools import lru_cache
import os
import sys


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Deployment Environment
    DEPLOYMENT_ENV: Literal["local", "ec2"] = "local"

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

    # CORS - 환경 변수로 설정 가능, 기본값은 와일드카드
    BACKEND_CORS_ORIGINS: str = "*"  # 환경변수로 쉼표 구분 리스트 전달 가능

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/quant_api.log"

    # External APIs
    DART_API_KEY: str = ""  # OpenDart API Key

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_settings(self) -> None:
        """설정 값 검증 및 경고 출력"""
        errors = []
        warnings = []

        # 필수 환경 변수 검증
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")

        if self.DATABASE_URL and "YOUR_DB" in self.DATABASE_URL:
            errors.append("DATABASE_URL contains placeholder values. Please update .env file")

        if not self.SECRET_KEY or self.SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32":
            if self.DEPLOYMENT_ENV == "ec2" or not self.DEBUG:
                errors.append("SECRET_KEY must be set to a secure random value in production")
            else:
                warnings.append("Using default SECRET_KEY. Generate a new one for production: openssl rand -hex 32")

        # Redis 연결 검증
        if self.ENABLE_CACHE:
            if "YOUR_ELASTICACHE" in self.REDIS_HOST:
                errors.append("REDIS_HOST contains placeholder values. Please update .env file")

        # CORS 설정 검증
        if self.DEPLOYMENT_ENV == "ec2":
            if "*" not in str(self.BACKEND_CORS_ORIGINS) and "localhost" in str(self.BACKEND_CORS_ORIGINS):
                warnings.append("BACKEND_CORS_ORIGINS includes localhost in EC2 environment. Update with actual domain/IP")

        # DEBUG 모드 검증
        if self.DEPLOYMENT_ENV == "ec2" and self.DEBUG:
            warnings.append("DEBUG=True in EC2 environment. Consider setting DEBUG=False for production")

        # 에러가 있으면 종료
        if errors:
            print("\n" + "="*60)
            print("CONFIGURATION ERRORS:")
            print("="*60)
            for error in errors:
                print(f"  ERROR: {error}")
            print("="*60)
            print("\nPlease fix the errors above and restart the application.")
            print("Refer to .env.example for correct configuration.\n")
            sys.exit(1)

        # 경고 출력
        if warnings:
            print("\n" + "="*60)
            print("CONFIGURATION WARNINGS:")
            print("="*60)
            for warning in warnings:
                print(f"  WARNING: {warning}")
            print("="*60 + "\n")

    def get_connection_info(self) -> dict:
        """연결 정보 요약 (민감 정보 마스킹)"""
        def mask_password(url: str) -> str:
            """비밀번호 마스킹"""
            if "@" in url:
                parts = url.split("@")
                if ":" in parts[0]:
                    user_pass = parts[0].split("://")[1]
                    user = user_pass.split(":")[0]
                    return url.replace(user_pass, f"{user}:****")
            return url

        return {
            "deployment_env": self.DEPLOYMENT_ENV,
            "database": mask_password(self.DATABASE_URL),
            "redis_host": self.REDIS_HOST,
            "redis_port": self.REDIS_PORT,
            "cache_enabled": self.ENABLE_CACHE,
            "debug_mode": self.DEBUG,
            "cors_origins": self.BACKEND_CORS_ORIGINS[:3] if len(self.BACKEND_CORS_ORIGINS) > 3 else self.BACKEND_CORS_ORIGINS,
        }


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤"""
    settings = Settings()
    # 설정 검증 실행
    settings.validate_settings()
    return settings


# 전역 settings 인스턴스
settings = get_settings()


# 애플리케이션 시작 시 연결 정보 출력
def print_startup_info():
    """시작 정보 출력"""
    info = settings.get_connection_info()
    print("\n" + "="*60)
    print("Stock Lab Backend - Configuration Info")
    print("="*60)
    print(f"Environment: {info['deployment_env'].upper()}")
    print(f"Database: {info['database']}")
    print(f"Redis: {info['redis_host']}:{info['redis_port']}")
    print(f"Cache: {'Enabled' if info['cache_enabled'] else 'Disabled'}")
    print(f"Debug Mode: {'ON' if info['debug_mode'] else 'OFF'}")
    print(f"CORS Origins: {', '.join(info['cors_origins'])}")
    print("="*60 + "\n")
