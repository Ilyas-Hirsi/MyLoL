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
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: Union[bool, str] = True
    
    # Cache TTL (in seconds)
    CACHE_MATCH_HISTORY_TTL: int = 3600
    CACHE_CHAMPION_MASTERY_TTL: int = 7200
    CACHE_MATCHUP_DATA_TTL: int = 86400
    
    # Rate Limiting (sliding window: RIOT_API_RATE_LIMIT requests per window)
    # Defaults assume a raised app-rate-limit key (>= 2000 requests / 10s).
    # Lower these to match your key if it is more restrictive.
    RIOT_API_RATE_LIMIT: int = 2000
    RIOT_API_RATE_WINDOW_SECONDS: float = 10.0
    # Legacy per-second / per-two-minute values (kept for backwards compatibility)
    RIOT_API_RATE_LIMIT_PER_SECOND: int = 20
    RIOT_API_RATE_LIMIT_PER_TWO_MINUTES: int = 100

    # How many recent matches to back-fill on a full refresh.
    MATCH_HISTORY_MAX: int = 1000
    # Fetch the per-minute timeline (extra API call per match) for lane games.
    FETCH_MATCH_TIMELINE: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construct DATABASE_URL if not provided directly
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
