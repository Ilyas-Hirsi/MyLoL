from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models.user import User
from app.models.match import Match
from app.models.match_timeline import MatchTimeline
from app.models.champion_mastery import ChampionMastery
from app.utils.auth import get_current_user
from app.services.riot_api import riot_api
from app.services.cache_service import cache
from config.settings import settings
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from app.services.champion_data import champion_data
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

class UserProfile(BaseModel):
    id: int
    riot_id: str
    tag: str
    puuid: str
    created_at: str
    last_updated: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile"""
    try:
        user = db.query(User).filter(User.id == int(current_user)).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserProfile(
            id=user.id,
            riot_id=user.riot_id,
            tag=user.tag,
            puuid=user.puuid,
            created_at=user.created_at.isoformat(),
            last_updated=user.last_updated.isoformat() if user.last_updated else None
        )
    except Exception as e:
        logger.error(f"Profile error: {e}")
        raise HTTPException(status_code=500, detail=f"Profile fetch failed: {str(e)}")

@router.get("/match-history")
async def get_match_history(
    current_user: str = Depends(get_current_user), 
    db: Session = Depends(get_db),
    game_mode: Optional[str] = None,
    limit: int = 200
):
    """Get user's match history from Riot API and database with caching"""
    logger.debug(f"Match history endpoint called for user {current_user}")
    
    try:
        user = db.query(User).filter(User.id == int(current_user)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Try to get from cache first (1 hour TTL)
        cache_key = f"match_history:{user.id}:{game_mode or 'all'}:{limit}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning {len(cached_data)} matches from cache")
            return cached_data
        
        # Query matches from database first
        query = db.query(Match).filter(Match.user_id == user.id)
        
        if game_mode:
            query = query.filter(Match.game_mode == game_mode)
        
        matches = query.order_by(Match.game_creation.desc()).limit(limit).all()
        
        # Format existing matches for response
        formatted_matches = []
        for match in matches:
            formatted_matches.append({
                "match_id": match.match_id,
                "champion": match.champion,
                "opponent_champion": match.opponent_champion,
                "team_position": match.team_position,
                "win": match.win,
                "game_duration": match.game_duration,
                "kda": {
                    "kills": match.kills,
                    "deaths": match.deaths,
                    "assists": match.assists
                },
                "cs_per_min": match.cs_per_min,
                "gold_per_min": match.gold_per_min,
                "kill_participation": match.kill_participation,
                "damage_to_champs_per_min": match.damage_to_champs_per_min,
                "game_creation": match.game_creation.isoformat() if match.game_creation else None,
                "queue_id": match.queue_id,
                "game_mode": match.game_mode
            })
        
        # Check if we have recent GAME data (played within last 24 hours)
        # Use game_creation (when game was played), not created_at (when added to DB)
        recent_match = db.query(Match).filter(
            Match.user_id == user.id,
            Match.game_creation >= datetime.utcnow() - timedelta(hours=24)
        ).first()
        
        logger.debug(f"Found {len(formatted_matches)} matches in database. Recent match? {recent_match is not None}")
        
        # Only fetch new data if we don't have recent data
        if not recent_match:
            # Check if we have any matches at all
            has_any_matches = db.query(Match).filter(Match.user_id == user.id).first()
            
            if has_any_matches:
                # Fetch only new matches from Riot API (will stop at first existing match)
                logger.debug(f"Fetching new matches from Riot API for user {user.puuid}")
            else:
                # First time fetching - get fresh data
                logger.debug(f"First time fetch - getting fresh match data from Riot API for user {user.puuid}")
            
            # Fetch new matches and add them to the database
            await _fetch_and_store_matches(db, user)
            
            # Re-query to get the updated data including new matches
            query = db.query(Match).filter(Match.user_id == user.id)
            if game_mode:
                query = query.filter(Match.game_mode == game_mode)
            updated_matches = query.order_by(Match.game_creation.desc()).limit(limit).all()
            
            # Format updated matches
            formatted_matches = []
            for match in updated_matches:
                formatted_matches.append({
                    "match_id": match.match_id,
                    "champion": match.champion,
                    "opponent_champion": match.opponent_champion,
                    "team_position": match.team_position,
                    "win": match.win,
                    "game_duration": match.game_duration,
                    "kda": {
                        "kills": match.kills,
                        "deaths": match.deaths,
                        "assists": match.assists
                    },
                    "cs_per_min": match.cs_per_min,
                    "gold_per_min": match.gold_per_min,
                    "kill_participation": match.kill_participation,
                    "damage_to_champs_per_min": match.damage_to_champs_per_min,
                    "game_creation": match.game_creation.isoformat() if match.game_creation else None,
                    "queue_id": match.queue_id,
                    "game_mode": match.game_mode
                })
        
        # Cache the result for 1 hour
        cache.set(cache_key, formatted_matches, ttl=3600)
        
        logger.debug(f"Returning {len(formatted_matches)} matches from database")
        return formatted_matches
        
    except Exception as e:
        logger.error(f"Match history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch match history: {str(e)}")

@router.get("/champion-mastery")
async def get_champion_mastery(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's champion mastery data from Riot API and database with caching"""
    logger.debug(f"Champion mastery endpoint called for user {current_user}")
    
    try:
        user = db.query(User).filter(User.id == int(current_user)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Try to get from cache first (2 hour TTL)
        cache_key = f"champion_mastery:{user.id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning {len(cached_data)} masteries from cache")
            return cached_data
        
        # Query mastery from database first
        mastery = db.query(ChampionMastery).filter(
            ChampionMastery.user_id == user.id
        ).order_by(ChampionMastery.champion_points.desc()).all()
        
        # Check if we have recent mastery data (updated within last 48 hours)
        recent_mastery = db.query(ChampionMastery).filter(
            ChampionMastery.user_id == user.id,
            ChampionMastery.last_updated >= datetime.utcnow() - timedelta(hours=48)
        ).first()
        
        logger.debug(f"Found {len(mastery)} masteries in database. Recent mastery? {recent_mastery is not None}")
        
        if not recent_mastery:
            # Fetch fresh data from Riot API
            logger.debug(f"Fetching fresh mastery data from Riot API for user {user.puuid}")
            await _fetch_and_store_mastery(db, user)
            
            # Re-query to get the updated mastery data
            mastery = db.query(ChampionMastery).filter(
                ChampionMastery.user_id == user.id
            ).order_by(ChampionMastery.champion_points.desc()).all()
        
        # Format mastery for API response
        formatted_mastery = []
        for champ in mastery:
            formatted_mastery.append({
                "champion_id": champ.champion_id,
                "champion_name": champ.champion_name,
                "champion_level": champ.champion_level,
                "champion_points": champ.champion_points,
                "last_played": champ.last_played.isoformat() if champ.last_played else None
            })
        
        # Cache the result for 2 hours
        cache.set(cache_key, formatted_mastery, ttl=7200)
        
        logger.debug(f"Returning {len(formatted_mastery)} champion masteries from database")
        return formatted_mastery
        
    except Exception as e:
        logger.error(f"Champion mastery error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch champion mastery: {str(e)}")

@router.post("/refresh-data")
async def refresh_user_data(
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Force refresh user data from Riot API"""
    logger.debug(f"Refresh data endpoint called for user {current_user}")
    
    try:
        user = db.query(User).filter(User.id == int(current_user)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Clear cache for this user
        cache.clear_user_cache(user.puuid)
        
        # Clear specific cache keys
        cache.delete(f"match_history:{user.id}:all:200")
        cache.delete(f"match_history:{user.id}:all:100")
        cache.delete(f"champion_mastery:{user.id}")
        
        # Add background tasks to fetch fresh data
        background_tasks.add_task(_fetch_and_store_matches, db, user)
        background_tasks.add_task(_fetch_and_store_mastery, db, user)
        
        # Update last_updated timestamp
        user.last_updated = datetime.utcnow()
        db.commit()
        
        return {
            "message": "User data refresh initiated", 
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Refresh data error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh user data: {str(e)}")

# Helper functions for fetching and storing data
async def _fetch_and_store_matches(db: Session, user: User):
    """Page through history up to MATCH_HISTORY_MAX, stopping at already-stored matches."""
    try:
        batch_size = 100
        max_matches = settings.MATCH_HISTORY_MAX
        matches_added = 0

        existing_match_ids = set(
            row[0] for row in db.query(Match.match_id)
            .filter(Match.user_id == user.id)
            .all()
        )

        # Collect unseen match ids, stopping at known history.
        new_match_ids = []
        found_existing = False
        for start in range(0, max_matches, batch_size):
            count = min(batch_size, max_matches - start)
            batch = riot_api.get_match_history(user.puuid, count=count, start=start)
            if not batch:
                break
            for match_id in batch:
                if match_id in existing_match_ids:
                    found_existing = True
                    break
                new_match_ids.append(match_id)
            if found_existing or len(batch) < count:
                break

        logger.debug(f"Fetching details for {len(new_match_ids)} new matches (max {max_matches})...")

        for match_id in new_match_ids:
            match_data = riot_api.get_match_details(match_id)
            if not match_data:
                continue

            player_data = next(
                (p for p in match_data["info"]["participants"] if p["puuid"] == user.puuid),
                None
            )
            if not player_data:
                continue

            # Full participant so we can reuse its participantId for the timeline.
            opponent = _get_lane_opponent_participant(match_data, player_data)
            opponent_champion = opponent["championName"] if opponent else None

            queue_id = match_data["info"]["queueId"]
            game_mode = _get_game_mode(queue_id)
            duration_min = match_data["info"]["gameDuration"] / 60

            team_kills = sum(p["kills"] for p in match_data["info"]["participants"] if p["teamId"] == player_data["teamId"])
            kill_participation = (player_data["kills"] + player_data["assists"]) / max(1, team_kills)

            # Create match record
            match_record = Match(
                match_id=match_id,
                user_id=user.id,
                champion=player_data["championName"],
                opponent_champion=opponent_champion,
                team_position=_normalize_team_position(player_data.get("teamPosition", "UNKNOWN")),
                win=player_data["win"],
                game_duration=duration_min,
                kills=player_data["kills"],
                deaths=player_data["deaths"],
                assists=player_data["assists"],
                cs_per_min=(player_data["totalMinionsKilled"] + player_data["neutralMinionsKilled"]) / duration_min,
                gold_per_min=player_data["goldEarned"] / duration_min,
                kill_participation=kill_participation,
                damage_to_champs_per_min=player_data["totalDamageDealtToChampions"] / duration_min,
                # Vision
                vision_score=player_data.get("visionScore", 0),
                wards_placed=player_data.get("wardsPlaced", 0),
                wards_killed=player_data.get("wardsKilled", 0),
                control_wards_bought=player_data.get("visionWardsBoughtInGame", 0),
                # Damage breakdown
                damage_taken=player_data.get("totalDamageTaken", 0),
                damage_self_mitigated=player_data.get("damageSelfMitigated", 0),
                damage_to_turrets=player_data.get("damageDealtToTurrets", 0),
                damage_to_objectives=player_data.get("damageDealtToObjectives", 0),
                total_heal=player_data.get("totalHeal", 0),
                # Objective participation
                turret_takedowns=player_data.get("turretTakedowns", 0),
                inhibitor_takedowns=player_data.get("inhibitorTakedowns", 0),
                dragon_kills=player_data.get("dragonKills", 0),
                baron_kills=player_data.get("baronKills", 0),
                objectives_stolen=player_data.get("objectivesStolen", 0),
                first_blood=player_data.get("firstBloodKill", False),
                first_tower=player_data.get("firstTowerKill", False),
                # Economy and level
                gold_earned=player_data.get("goldEarned", 0),
                total_cs=player_data.get("totalMinionsKilled", 0) + player_data.get("neutralMinionsKilled", 0),
                champ_level=player_data.get("champLevel", 0),
                # Combat highlights
                largest_killing_spree=player_data.get("largestKillingSpree", 0),
                largest_multi_kill=player_data.get("largestMultiKill", 0),
                double_kills=player_data.get("doubleKills", 0),
                triple_kills=player_data.get("tripleKills", 0),
                quadra_kills=player_data.get("quadraKills", 0),
                penta_kills=player_data.get("pentaKills", 0),
                time_ccing_others=player_data.get("timeCCingOthers", 0),
                game_creation=datetime.fromtimestamp(match_data["info"]["gameCreation"] / 1000),
                queue_id=queue_id,
                game_mode=game_mode
            )

            db.add(match_record)
            matches_added += 1

            # Timeline only applies to lane games with an identified opponent.
            if settings.FETCH_MATCH_TIMELINE and opponent is not None:
                _fetch_and_store_timeline(db, user, match_id, player_data, opponent)

        db.commit()
        logger.debug(f"Successfully stored {matches_added} new matches for user {user.puuid}")

    except Exception as e:
        logger.error(f"Failed to fetch and store matches: {e}")
        db.rollback()


def _fetch_and_store_timeline(db: Session, user: User, match_id: str, player_data: dict, opponent: dict):
    """Fetch the match timeline and store per-minute series vs the lane opponent."""
    try:
        timeline = riot_api.get_match_timeline(match_id)
        if not timeline:
            return
        metrics = _compute_timeline_metrics(timeline, player_data, opponent)
        if not metrics:
            return
        db.add(MatchTimeline(
            match_id=match_id,
            user_id=user.id,
            champion=player_data["championName"],
            opponent_champion=opponent["championName"],
            team_position=_normalize_team_position(player_data.get("teamPosition", "UNKNOWN")),
            **metrics,
        ))
    except Exception as e:
        logger.error(f"Failed to store timeline for {match_id}: {e}")


def _compute_timeline_metrics(timeline: dict, player_data: dict, opponent: dict) -> Optional[dict]:
    """Build per-minute CS/gold/XP series (index = minute) for the user vs the opponent."""
    frames = timeline.get("info", {}).get("frames", [])
    if not frames:
        return None

    player_pid = str(player_data["participantId"])
    opp_pid = str(opponent["participantId"])

    cs_series, opp_cs_series, gold_diff_series, xp_diff_series = [], [], [], []
    for frame in frames:
        pf = frame.get("participantFrames", {})
        me = pf.get(player_pid)
        opp = pf.get(opp_pid)
        if not me or not opp:
            continue
        cs_series.append(me.get("minionsKilled", 0) + me.get("jungleMinionsKilled", 0))
        opp_cs_series.append(opp.get("minionsKilled", 0) + opp.get("jungleMinionsKilled", 0))
        gold_diff_series.append(me.get("totalGold", 0) - opp.get("totalGold", 0))
        xp_diff_series.append(me.get("xp", 0) - opp.get("xp", 0))

    if not cs_series:
        return None

    def cs_diff_at(minute: int) -> Optional[int]:
        if len(cs_series) > minute:
            return cs_series[minute] - opp_cs_series[minute]
        return None

    def gold_diff_at(minute: int) -> Optional[int]:
        if len(gold_diff_series) > minute:
            return gold_diff_series[minute]
        return None

    return {
        "cs_series": cs_series,
        "opponent_cs_series": opp_cs_series,
        "gold_diff_series": gold_diff_series,
        "xp_diff_series": xp_diff_series,
        "cs_diff_at_10": cs_diff_at(10),
        "cs_diff_at_15": cs_diff_at(15),
        "gold_diff_at_10": gold_diff_at(10),
        "gold_diff_at_15": gold_diff_at(15),
    }

async def _fetch_and_store_mastery(db: Session, user: User):
    """Fetch champion mastery data from Riot API and store in database"""
    try:
        # Get mastery data from Riot API
        mastery_data = riot_api.get_champion_mastery(user.puuid)
        logger.debug(f"Found {len(mastery_data)} champion masteries")
        
        for champ_data in mastery_data:
            # Check if mastery already exists
            existing_mastery = db.query(ChampionMastery).filter(
                ChampionMastery.user_id == user.id,
                ChampionMastery.champion_id == champ_data["championId"]
            ).first()
            
            if existing_mastery:
                # Update existing mastery
                existing_mastery.champion_level = champ_data["championLevel"]
                existing_mastery.champion_points = champ_data["championPoints"]
                existing_mastery.last_played = datetime.fromtimestamp(champ_data["lastPlayTime"] / 1000) if champ_data["lastPlayTime"] else None
            else:
                # Create new mastery record
                mastery_record = ChampionMastery(
                    user_id=user.id,
                    champion_id=champ_data["championId"],
                    champion_name=_get_champion_name_by_id(champ_data["championId"]),
                    champion_level=champ_data["championLevel"],
                    champion_points=champ_data["championPoints"],
                    last_played=datetime.fromtimestamp(champ_data["lastPlayTime"] / 1000) if champ_data["lastPlayTime"] else None
                )
                db.add(mastery_record)
        
        db.commit()
        logger.debug(f"Successfully stored mastery data for user {user.puuid}")
        
    except Exception as e:
        logger.error(f"Failed to fetch and store mastery: {e}")
        db.rollback()

_LANE_POSITIONS = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}


def _get_lane_opponent_participant(match_data: dict, player_data: dict) -> Optional[dict]:
    """Opposing participant in the same lane, or None (e.g. ARAM/Arena/unknown position)."""
    player_lane = (player_data.get("teamPosition") or "").strip().upper()
    if player_lane not in _LANE_POSITIONS:
        return None
    player_team = player_data["teamId"]
    for participant in match_data["info"]["participants"]:
        if (participant["teamId"] != player_team and
                participant.get("teamPosition") == player_data.get("teamPosition")):
            return participant
    return None

def _get_game_mode(queue_id: int) -> str:
    """Convert queue ID to game mode name"""
    queue_map = {
        420: "Ranked Solo/Duo",
        440: "Ranked Flex",
        450: "ARAM",
        700: "Clash",
        900: "URF",
        1020: "One for All",
        1300: "Nexus Blitz",
        1400: "Ultimate Spellbook",
        1700: "Arena",
        1900: "URF",
        2000: "Tutorial",
        2010: "Tutorial",
        2020: "Tutorial"
    }
    return queue_map.get(queue_id, f"Queue {queue_id}")

def _get_champion_name_by_id(champion_id: int) -> str:
    """Get champion name by ID using Data Dragon mapping"""
    return champion_data.get_champion_name_by_id(champion_id)

def _normalize_team_position(pos: str) -> str:
    if not pos:
        return "UNKNOWN"
    mapping = {
        'MID': 'MIDDLE',
        'ADC': 'BOTTOM',
        'BOT': 'BOTTOM',
        'SUPPORT': 'UTILITY',
    }
    up = pos.strip().upper()
    return mapping.get(up, up)