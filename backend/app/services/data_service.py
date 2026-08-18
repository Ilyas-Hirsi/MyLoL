from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.user import User
from app.models.match import Match
from app.models.champion_mastery import ChampionMastery
from app.services.riot_api import riot_api
from app.services.cache_service import cache
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.cache_ttl = settings.CACHE_MATCH_HISTORY_TTL
    
    def get_or_fetch_user_data(self, db: Session, user_id: int, force_refresh: bool = False) -> Dict:
        """Get user data from database, fetch from Riot API if needed"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        cache_key = f"user:{user.puuid}:data"
        
        def _fetch_data():
            # Check if we need to fetch new data
            if not force_refresh and self._has_recent_data(db, user_id):
                return self._get_cached_data(db, user_id)
            
            # Fetch from Riot API
            return self._fetch_from_riot_api(db, user)
        
        return cache.get_or_set(cache_key, _fetch_data, self.cache_ttl)
    
    def _has_recent_data(self, db: Session, user_id: int) -> bool:
        """Check if user has recent match data (within last hour)"""
        recent_time = datetime.utcnow() - timedelta(hours=1)
        recent_match = db.query(Match).filter(
            Match.user_id == user_id,
            Match.created_at >= recent_time
        ).first()
        return recent_match is not None
    
    def _get_cached_data(self, db: Session, user_id: int) -> Dict:
        """Get data from database"""
        matches = db.query(Match).filter(Match.user_id == user_id).order_by(Match.game_creation.desc()).limit(200).all()
        mastery = db.query(ChampionMastery).filter(ChampionMastery.user_id == user_id).all()
        
        return {
            "matches": [self._format_match(match) for match in matches],
            "mastery": [self._format_mastery(m) for m in mastery]
        }
    
    def _fetch_from_riot_api(self, db: Session, user: User) -> Dict:
        """Fetch fresh data from Riot API and store in database"""
        # Get match history

        match_ids = []
        for i in range(2):
            match_ids.append(riot_api.get_match_history(user.puuid, count=100))
        
        # Process matches
        matches = []
        for match_id in match_ids:
            # Check if match already exists
            existing_match = db.query(Match).filter(Match.match_id == match_id).first()
            if existing_match:
                matches.append(self._format_match(existing_match))
                continue
            
            # Fetch new match data
            match_data = riot_api.get_match_details(match_id)
            if match_data:
                match_obj = self._process_match_data(db, user, match_id, match_data)
                if match_obj:
                    matches.append(self._format_match(match_obj))
        
        # Get champion mastery
        mastery_data = riot_api.get_champion_mastery(user.puuid)
        mastery = []
        for champ_data in mastery_data:
            mastery_obj = self._process_mastery_data(db, user, champ_data)
            if mastery_obj:
                mastery.append(self._format_mastery(mastery_obj))
        
        return {"matches": matches, "mastery": mastery}
    
    def _process_match_data(self, db: Session, user: User, match_id: str, match_data: Dict) -> Optional[Match]:
        """Process and store match data"""
        try:
            player_data = next(
                (p for p in match_data["info"]["participants"] if p["puuid"] == user.puuid),
                None
            )
            if not player_data:
                return None
            
            # Extract game mode info
            queue_id = match_data["info"]["queueId"]
            game_mode = self._get_game_mode(queue_id)
            
            # Create match object
            match_obj = Match(
                match_id=match_id,
                user_id=user.id,
                champion=player_data["championName"],
                opponent_champion=self._get_opponent_champion(match_data, player_data),
                team_position=player_data.get("teamPosition", "UNKNOWN"),
                win=player_data["win"],
                game_duration=match_data["info"]["gameDuration"] / 60,
                kills=player_data["kills"],
                deaths=player_data["deaths"],
                assists=player_data["assists"],
                cs_per_min=(player_data["totalMinionsKilled"] + player_data["neutralMinionsKilled"]) / (match_data["info"]["gameDuration"] / 60),
                gold_per_min=player_data["goldEarned"] / (match_data["info"]["gameDuration"] / 60),
                kill_participation=self._calculate_kill_participation(player_data, match_data),
                damage_to_champs_per_min=player_data["totalDamageDealtToChampions"] / (match_data["info"]["gameDuration"] / 60),
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
            
            db.add(match_obj)
            db.commit()
            db.refresh(match_obj)
            return match_obj
            
        except Exception as e:
            logger.error(f"Error processing match {match_id}: {e}")
            return None
    
    def _get_game_mode(self, queue_id: int) -> str:
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
    
    def get_filtered_matches(self, db: Session, user_id: int, game_mode: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get matches filtered by game mode"""
        query = db.query(Match).filter(Match.user_id == user_id)
        
        if game_mode:
            query = query.filter(Match.game_mode == game_mode)
        
        matches = query.order_by(Match.game_creation.desc()).limit(limit).all()
        return [self._format_match(match) for match in matches]
    
    def _format_match(self, match: Match) -> Dict:
        """Format match for API response"""
        return {
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
            "vision": {
                "vision_score": match.vision_score,
                "wards_placed": match.wards_placed,
                "wards_killed": match.wards_killed,
                "control_wards_bought": match.control_wards_bought,
            },
            "damage": {
                "taken": match.damage_taken,
                "self_mitigated": match.damage_self_mitigated,
                "to_turrets": match.damage_to_turrets,
                "to_objectives": match.damage_to_objectives,
                "total_heal": match.total_heal,
            },
            "objectives": {
                "turret_takedowns": match.turret_takedowns,
                "inhibitor_takedowns": match.inhibitor_takedowns,
                "dragon_kills": match.dragon_kills,
                "baron_kills": match.baron_kills,
                "objectives_stolen": match.objectives_stolen,
                "first_blood": match.first_blood,
                "first_tower": match.first_tower,
            },
            "economy": {
                "gold_earned": match.gold_earned,
                "total_cs": match.total_cs,
                "champ_level": match.champ_level,
            },
            "highlights": {
                "largest_killing_spree": match.largest_killing_spree,
                "largest_multi_kill": match.largest_multi_kill,
                "double_kills": match.double_kills,
                "triple_kills": match.triple_kills,
                "quadra_kills": match.quadra_kills,
                "penta_kills": match.penta_kills,
                "time_ccing_others": match.time_ccing_others,
            },
            "game_creation": match.game_creation.isoformat() if match.game_creation else None,
            "queue_id": getattr(match, 'queue_id', None),
            "game_mode": getattr(match, 'game_mode', 'Unknown')
        }
    
    def _format_mastery(self, mastery: ChampionMastery) -> Dict:
        """Format mastery for API response"""
        return {
            "champion_id": mastery.champion_id,
            "champion_name": mastery.champion_name,
            "champion_level": mastery.champion_level,
            "champion_points": mastery.champion_points,
            "last_played": mastery.last_played.isoformat() if mastery.last_played else None
        }

# Global instance
data_service = DataService()