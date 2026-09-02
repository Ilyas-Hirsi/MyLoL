from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.utils.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.matchup_analyzer import matchup_analyzer
from app.services import personal_stats
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matchups", tags=["matchups"])


# Helper function to get user and validate match data
def _get_user_with_validation(db: Session, user_id: str):
    """Get user and check if they have match data available."""
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for match data
    from app.models.match import Match
    match_count = db.query(Match).filter(Match.user_id == user.id).count()
    if match_count == 0:
        raise HTTPException(
            status_code=400, 
            detail="No match data available. Please refresh your data."
        )
    
    return user


@router.get("/difficult")
async def get_difficult_matchups(
    role: Optional[str] = Query(None, description="Filter by role (TOP, JUNGLE, MIDDLE, ADC, SUPPORT)"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode (e.g., RANKED_SOLO_5x5, ARAM, NORMAL_DRAFT)"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's most difficult matchups - champions with win rate < 50%."""
    try:
        user = _get_user_with_validation(db, current_user)
        difficult_matchups = matchup_analyzer.analyze_difficult_matchups(db, user.id, role, game_mode)
        
        return {
            "difficult_matchups": difficult_matchups,
            "total_analyzed": len(difficult_matchups),
            "role_filter": role,
            "game_mode_filter": game_mode
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Difficult matchups error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze difficult matchups: {str(e)}")


@router.get("/champion/{champion_name}")
async def get_champion_matchup_data(
    champion_name: str,
    role: Optional[str] = Query(None, description="Filter by role"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """The user's strong and weak matchups while playing this champion.

    Derived from the user's own match history - the opponents they beat most
    and least often when they lock in `champion_name`.
    """
    try:
        user = _get_user_with_validation(db, current_user)
        normalized_role = personal_stats.normalize_role(role)
        normalized_mode = (game_mode or "").strip() or None
        faced = personal_stats.opponents_faced_on_champion(
            db, user.id, champion_name, normalized_role, normalized_mode
        )
        return {
            "champion": champion_name,
            "strong_against": [m for m in faced if m["win_rate"] >= 50][:5],
            "weak_against": [m for m in faced if m["win_rate"] < 50][-5:],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Champion matchup data error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get champion matchup data: {str(e)}")


@router.get("/vs/{champion1}/{champion2}")
async def get_head_to_head_matchup(
    champion1: str,
    champion2: str,
    role: Optional[str] = Query(None, description="Filter by role"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """The user's head-to-head record playing champion1 into champion2."""
    try:
        user = _get_user_with_validation(db, current_user)
        matchup_data = matchup_analyzer.get_champion_matchup_data(
            db, user.id, champion1, champion2, role, game_mode
        )
        return {
            "champion1": champion1,
            "champion2": champion2,
            "matchup_data": matchup_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Head-to-head matchup error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get matchup data: {str(e)}")


@router.get("/timeline/{opponent}")
async def get_matchup_timeline(
    opponent: str,
    role: Optional[str] = Query(None, description="Filter by role (TOP, JUNGLE, MIDDLE, ADC, SUPPORT)"),
    min_games: int = Query(1, ge=1, description="Minimum games required before returning a series"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Averaged laning-phase timeline for the user versus a lane opponent.

    Returns per-minute CS (user and opponent), the CS lead, the gold lead, and
    the @10 / @15 checkpoint differentials - the data behind a "CS/min vs your
    lane opponent" chart, aggregated across every game the user played into
    `opponent`.
    """
    try:
        user = _get_user_with_validation(db, current_user)
        normalized_role = personal_stats.normalize_role(role)
        return personal_stats.lane_timeline_vs_opponent(
            db, user.id, opponent, normalized_role, min_games
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Matchup timeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get matchup timeline: {str(e)}")


@router.get("/details/{opponent}")
async def get_matchup_details(
    opponent: str,
    role: Optional[str] = Query(None, description="Filter by role (TOP, JUNGLE, MIDDLE, ADC, SUPPORT)"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode (e.g., RANKED_SOLO_5x5, ARAM, NORMAL_DRAFT)"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive matchup details against a specific opponent.
    
    Returns detailed stats, distributions, and recent match history.
    """
    try:
        user = _get_user_with_validation(db, current_user)
        details = matchup_analyzer.analyze_matchup_details(db, user.id, opponent, role, game_mode)
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Matchup details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get matchup details: {str(e)}")
