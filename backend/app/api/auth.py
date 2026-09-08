from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.user import User
from app.utils.auth import create_access_token
from app.services.riot_api import riot_api
from config.settings import settings
from datetime import timedelta
from pydantic import BaseModel
from datetime import datetime  #
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


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
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Resolve a Riot ID to an account.

    There is no sign-up and no password. The Riot ID is checked against Riot's
    account service; the matching user row is returned if we have seen this
    PUUID before, and created if we have not.
    """
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
        try:
            user = User(riot_id=user_data.riot_id, tag=user_data.tag, puuid=puuid)
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.puuid}, expires_delta=access_token_expires
    )

    # Return token payload expected by frontend
    return {"access_token": access_token, "token_type": "bearer"}
