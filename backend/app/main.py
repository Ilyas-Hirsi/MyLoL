from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.utils.database import init_db
from app.api import auth, users, matchups, champions
from config.settings import settings
import logging

_debug_enabled = settings.debug_enabled
logging.basicConfig(
    level=logging.DEBUG if _debug_enabled else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting League Analytics API...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down League Analytics API...")


app = FastAPI(
    title="League Analytics API",
    description="Personal League of Legends match analytics.",
    version="1.0.0",
    lifespan=lifespan,
    # The schema browser enumerates every route and model. Useful locally,
    # free reconnaissance in a deployment.
    docs_url="/docs" if _debug_enabled else None,
    redoc_url="/redoc" if _debug_enabled else None,
    openapi_url="/openapi.json" if _debug_enabled else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Auth is a Bearer token, not a cookie, so the browser never needs to send
    # credentials cross-origin. Leaving this on widens the origin check for no
    # benefit.
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(matchups.router)
app.include_router(champions.router)


@app.get("/")
async def root():
    return {"message": "League Analytics API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
