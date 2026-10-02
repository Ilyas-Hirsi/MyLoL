from typing import List, Dict, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.champion_mastery import ChampionMastery
from app.services.cache_service import cache
from app.services import personal_stats
from config.settings import settings


class ChampionRecommender:
    def __init__(self):
        self.cache_ttl = settings.CACHE_MATCHUP_DATA_TTL

    def get_champion_recommendations(
        self,
        db: Session,
        user_puuid: str,
        difficult_matchups: List[str],
        role: str = None,
        game_mode: str | None = None,
    ) -> List[Dict]:
        """Recommend champions from the user's own pool for their hard matchups.

        For each champion the user plays, we look at their real win rate (from
        match history) against the opponents they currently struggle with, and
        surface the champions that actually perform best. No web scraping and no
        simulated numbers - everything comes from the user's games.
        """
        normalized_role = self._normalize_role(role)
        normalized_mode = (game_mode or "").strip() or None
        cache_key = (
            f"user:{user_puuid}:recommendations:{normalized_role or 'all'}:"
            f"{normalized_mode or 'all'}:{hash(tuple(sorted(difficult_matchups)))}"
        )

        def _get_recommendations():
            # Mastery gives us the champion pool plus points/level for display.
            mastery_data = db.query(ChampionMastery).filter(
                ChampionMastery.user_puuid == user_puuid
            ).all()
            mastery_by_name = {m.champion_name: m for m in mastery_data}

            # One grouped query: (champion, opponent) -> (games, wins).
            grid = personal_stats.matchup_grid(
                db, user_puuid, normalized_role, normalized_mode
            )
            if not grid:
                return []

            difficult_set = set(difficult_matchups)

            # Aggregate per champion: overall record and record vs hard matchups.
            overall = defaultdict(lambda: [0, 0])          # champ -> [games, wins]
            vs_difficult = defaultdict(lambda: [0, 0])     # champ -> [games, wins]
            beaten = defaultdict(list)                      # champ -> [opponents]
            for (champ, opp), (games, wins) in grid.items():
                overall[champ][0] += games
                overall[champ][1] += wins
                if opp in difficult_set:
                    vs_difficult[champ][0] += games
                    vs_difficult[champ][1] += wins
                    if wins / games >= 0.5:
                        beaten[champ].append(opp)

            recommendations = []
            for champ, (games, wins) in overall.items():
                if games < 3:  # need a real sample to say anything useful
                    continue

                d_games, d_wins = vs_difficult[champ]
                has_direct = d_games > 0
                if has_direct:
                    counter_win_rate = round(d_wins / d_games * 100, 1)
                    reason = (
                        f"You win {counter_win_rate}% on {champ} across "
                        f"{d_games} game{'s' if d_games != 1 else ''} vs your "
                        f"difficult matchups"
                    )
                else:
                    counter_win_rate = round(wins / games * 100, 1)
                    reason = (
                        f"Your overall win rate on {champ} is "
                        f"{counter_win_rate}% ({games} games)"
                    )

                mastery = mastery_by_name.get(champ)
                recommendations.append({
                    "champion": champ,
                    "mastery_points": mastery.champion_points if mastery else 0,
                    "mastery_level": mastery.champion_level if mastery else 0,
                    "counter_win_rate": counter_win_rate,
                    "games_vs_opponents": d_games,
                    "counters": sorted(beaten[champ])[:5],
                    "reason": reason,
                    # Internal sort hint: prefer direct evidence at equal win rate.
                    "_has_direct": has_direct,
                })

            # Only recommend champions the user actually wins on. If none clear
            # 50% (e.g. a rough stretch), fall back to their best available so
            # the list is never empty.
            winners = [r for r in recommendations if r["counter_win_rate"] >= 50]
            pool = winners if winners else recommendations

            # Best win rate first; direct head-to-head data breaks ties.
            pool.sort(
                key=lambda x: (x["counter_win_rate"], x["_has_direct"]),
                reverse=True,
            )
            for rec in pool:
                rec.pop("_has_direct", None)
            return pool[:5]

        return cache.get_or_set(cache_key, _get_recommendations, self.cache_ttl)

    def get_champion_counters(
        self,
        db: Session,
        user_puuid: str,
        champion: str,
        role: str | None = None,
        game_mode: str | None = None,
    ) -> List[Dict]:
        """Personal counters: which of the user's champions beat `champion`.

        Derived from the user's match history, so it reflects what has actually
        worked for them rather than a global meta average.
        """
        normalized_role = self._normalize_role(role)
        normalized_mode = (game_mode or "").strip() or None
        cache_key = (
            f"user:{user_puuid}:counters:{champion}:"
            f"{normalized_role or 'all'}:{normalized_mode or 'all'}"
        )

        def _get_counters():
            return personal_stats.champions_vs_opponent(
                db, user_puuid, champion, normalized_role, normalized_mode
            )

        return cache.get_or_set(cache_key, _get_counters, self.cache_ttl)

    def _normalize_role(self, role: Optional[str]) -> Optional[str]:
        """Convert UI role names to Riot's teamPosition format."""
        if not role:
            return None
        role_mapping = {
            "TOP": "TOP",
            "JUNGLE": "JUNGLE",
            "MID": "MIDDLE",
            "MIDDLE": "MIDDLE",
            "ADC": "BOTTOM",
            "BOT": "BOTTOM",
            "BOTTOM": "BOTTOM",
            "SUPPORT": "UTILITY",
            "UTILITY": "UTILITY",
        }
        return role_mapping.get(role.strip().upper(), role.strip().upper())


# Global instance
champion_recommender = ChampionRecommender()
