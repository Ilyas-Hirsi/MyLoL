from pydantic_settings import BaseSettings
from typing import Optional, Union


class Settings(BaseSettings):
    # Riot API Configuration
    RIOT_API_KEY: str  # Required - must be set in .env file
    RIOT_API_REGION: str = "na1"
    RIOT_API_ACCOUNT_REGION: str = "americas"
    
    # PostgreSQL Database Configuration
    # DATABASE_URL can be provided directly, or constructed from individual components
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "league_analytics"
    DB_USER: str = "postgres"
    DB_PASSWORD: str  # Required - must be set in .env file
    
    # Redis Configuration (for caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT Authentication
    SECRET_KEY: str  # Required - must be set in .env file
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Server Configuration
    # Comma-separated origins allowed to call the API from a browser.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    # Failed account lookups allowed per client IP per window, to keep the one
    # unauthenticated endpoint from being used to enumerate Riot IDs or to burn
    # the server's Riot API quota.
    LOGIN_RATE_LIMIT: int = 10
    LOGIN_RATE_WINDOW_SECONDS: float = 60.0

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: Union[bool, str] = False  # opt in locally; never default-on in a deployment
    
    # Cache TTL (in seconds)
    CACHE_MATCH_HISTORY_TTL: int = 3600
    CACHE_CHAMPION_MASTERY_TTL: int = 7200
    CACHE_MATCHUP_DATA_TTL: int = 86400
    
    # Rate limiting: RIOT_API_RATE_LIMIT requests per RIOT_API_RATE_WINDOW_SECONDS
    RIOT_API_RATE_LIMIT: int = 2000
    RIOT_API_RATE_WINDOW_SECONDS: float = 10.0

    MATCH_HISTORY_MAX: int = 1000       # matches to back-fill on a full refresh
    FETCH_MATCH_TIMELINE: bool = True   # fetch per-minute timeline (extra call per match)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construct DATABASE_URL if not provided directly
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def debug_enabled(self) -> bool:
        return str(self.DEBUG).strip().lower() in ("1", "true", "yes", "on")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # tolerate stale/unknown keys in .env


settings = Settings()
