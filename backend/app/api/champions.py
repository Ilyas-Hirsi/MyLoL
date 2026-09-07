from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.utils.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.champion_recommender import champion_recommender
from app.services.matchup_analyzer import matchup_analyzer
from app.services import personal_stats
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/champions", tags=["champions"])


@router.get("/recommendations")
async def get_champion_recommendations(
    role: Optional[str] = Query(None, description="Filter by role"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get champion recommendations based on difficult matchups"""
    try:
        user = db.query(User).filter(User.puuid == current_user).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ensure user has match data
        from app.models.match import Match
        match_count = db.query(Match).filter(Match.user_puuid == user.puuid).count()
        if match_count == 0:
            return {
                "recommendations": [],
                "based_on_matchups": [],
                "role_filter": role,
                "message": "No match data available. Please refresh your data."
            }
        
        # Get difficult matchups first
        difficult_matchups = matchup_analyzer.analyze_difficult_matchups(db, user.puuid, role, game_mode)
        difficult_champions = [m["champion"] for m in difficult_matchups]
        
        # Get recommendations
        recommendations = champion_recommender.get_champion_recommendations(
            db, user.puuid, difficult_champions, role, game_mode
        )
        
        return {
            "recommendations": recommendations,
            "based_on_matchups": difficult_champions,
            "role_filter": role,
            "game_mode_filter": game_mode
        }
        
    except Exception as e:
        logger.error(f"Champion recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get champion recommendations: {str(e)}")


@router.get("/counters/{champion_name}")
async def get_champion_counters(
    champion_name: str,
    role: Optional[str] = Query(None, description="Filter by role"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Personal counters: which of the user's champions beat this opponent.

    Ranked by the user's own win rate against `champion_name`.
    """
    try:
        user = db.query(User).filter(User.puuid == current_user).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        counters = champion_recommender.get_champion_counters(
            db, user.puuid, champion_name, role, game_mode
        )
        return {
            "champion": champion_name,
            "counters": counters
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Champion counters error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get champion counters: {str(e)}")


@router.get("/stats/{champion_name}")
async def get_champion_stats(
    champion_name: str,
    role: Optional[str] = Query(None, description="Filter by role"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """The user's personal stats for a champion, from their match history.

    `win_rate` and `pick_rate` are personal (the user's own games); there is no
    global meta data here. `strong_against` / `weak_against` are the opponents
    they beat and lose to most while playing this champion.
    """
    try:
        user = db.query(User).filter(User.puuid == current_user).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        normalized_role = personal_stats.normalize_role(role)
        normalized_mode = (game_mode or "").strip() or None

        summary = personal_stats.champion_summary(
            db, user.puuid, champion_name, normalized_role, normalized_mode
        )
        faced = personal_stats.opponents_faced_on_champion(
            db, user.puuid, champion_name, normalized_role, normalized_mode
        )
        favorable = [m for m in faced if m["win_rate"] >= 50]
        unfavorable = [m for m in faced if m["win_rate"] < 50]

        return {
            "champion": champion_name,
            "games": summary["games"],
            "win_rate": summary["win_rate"],
            "pick_rate": summary["pick_rate"],
            "ban_rate": 0.0,  # no personal analogue for ban rate
            "avg_kda": summary["avg_kda"],
            "avg_cs_per_min": summary["avg_cs_per_min"],
            "avg_damage_per_min": summary["avg_damage_per_min"],
            "counters": favorable[:5],
            "strong_against": favorable[:5],
            "weak_against": list(reversed(unfavorable[-5:])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Champion stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get champion stats: {str(e)}")
