from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.user import User
from app.utils.auth import create_access_token
from app.services.riot_api import riot_api
from config.settings import settings
from datetime import timedelta
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Account entry is the only endpoint that takes no token, and every call spends
# one request from the server's Riot API quota. Without a cap it is both a Riot
# ID enumeration oracle and a cheap way to exhaust that quota for everyone.
# Per-process and in-memory: enough for a single instance, and it fails closed
# rather than pretending to be a distributed limiter.
_login_attempts: dict[str, deque] = defaultdict(deque)
_login_lock = Lock()


def _enforce_login_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    window = settings.LOGIN_RATE_WINDOW_SECONDS
    now = monotonic()

    with _login_lock:
        attempts = _login_attempts[client]
        while attempts and now - attempts[0] >= window:
            attempts.popleft()

        if len(attempts) >= settings.LOGIN_RATE_LIMIT:
            retry_after = int(window - (now - attempts[0])) + 1
            logger.warning("Account lookup rate limit hit for %s", client)
            raise HTTPException(
                status_code=429,
                detail="Too many account lookups. Try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

        attempts.append(now)


class UserLogin(BaseModel):
    riot_id: str
    tag: str

class UserResponse(BaseModel):
    id: int
    riot_id: str
    tag: str
    puuid: str
    created_at: datetime
    last_updated: datetime | None = None

    class Config:
        from_attributes = True


@router.post("/login")
async def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Resolve a Riot ID to an account.

    There is no sign-up and no password. The Riot ID is checked against Riot's
    account service; the matching user row is returned if we have seen this
    PUUID before, and created if we have not.
    """
    _enforce_login_rate_limit(request)

    # Verify the account exists in Riot's system, and say honestly why if it
    # cannot be verified — a dead API key is our problem, not the player's.
    puuid, status = riot_api.resolve_account(user_data.riot_id, user_data.tag)

    if status == "not_found":
        raise HTTPException(
            status_code=404,
            detail=f"Riot has no account for {user_data.riot_id}#{user_data.tag}",
        )
    if status == "unauthorized":
        raise HTTPException(
            status_code=503,
            detail="Account lookup is unavailable: the server's Riot API key is not valid.",
        )
    if status == "rate_limited":
        raise HTTPException(
            status_code=429,
            detail="Riot is rate limiting this server. Try again shortly.",
        )
    if status != "ok" or not puuid:
        raise HTTPException(status_code=502, detail="Could not reach Riot's account service.")
    
    # Find or create user in database (no signup step)
    user = db.query(User).filter(User.puuid == puuid).first()

    if not user:
        # Riot encrypts the PUUID with the API key that asked for it, so rotating
        # the key yields a new ciphertext for the same account and the lookup
        # above misses. The Riot ID does not rotate, so it is what identifies a
        # returning player; re-point the row and the foreign keys cascade the
        # change to their matches, timelines and mastery rows.
        user = db.query(User).filter(
            func.lower(User.riot_id) == user_data.riot_id.lower(),
            func.lower(User.tag) == user_data.tag.lower(),
        ).first()

        if user:
            logger.info(
                "Re-linking %s#%s to a new PUUID after a Riot API key rotation",
                user.riot_id, user.tag,
            )
            user.puuid = puuid
            # Keep the display name in step with what Riot returned.
            user.riot_id = user_data.riot_id
            user.tag = user_data.tag
            try:
                db.commit()
                db.refresh(user)
            except Exception:
                db.rollback()
                logger.exception("Failed to re-link user to new PUUID")
                raise HTTPException(
                    status_code=500, detail="Could not update your account."
                )

    if not user:
        try:
            user = User(riot_id=user_data.riot_id, tag=user_data.tag, puuid=puuid)
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            # The database error text can name tables, columns and constraints;
            # it belongs in the log, not in the response.
            logger.exception("Failed to create user")
            raise HTTPException(status_code=500, detail="Could not create your account.")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.puuid}, expires_delta=access_token_expires
    )

    # Return token payload expected by frontend
    return {"access_token": access_token, "token_type": "bearer"}
