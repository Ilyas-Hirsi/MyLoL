"""Personal statistics derived from the user's own match history.

Every function here computes stats from the `matches` table (real Riot
Match-V5 data the app already ingests) - there is no web scraping and no
fabricated data. When a user has no games matching a query, the caller gets
an empty result rather than a made-up one.
"""
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import Integer, func

from app.models.match import Match

_ROLE_MAP = {
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


def normalize_role(role: Optional[str]) -> Optional[str]:
    """Convert a UI role name to Riot's teamPosition format."""
    if not role:
        return None
    key = role.strip().upper()
    return _ROLE_MAP.get(key, key)


def _apply_filters(query, role: Optional[str], game_mode: Optional[str]):
    """Apply optional role / game-mode filters to a Match query.

    `role` must already be normalised to Riot's teamPosition format.
    """
    if role:
        query = query.filter(Match.team_position == role)
    if game_mode:
        query = query.filter(Match.game_mode == game_mode)
    return query


def matchup_grid(
    db: Session,
    user_id: int,
    role: Optional[str] = None,
    game_mode: Optional[str] = None,
) -> Dict[Tuple[str, str], Tuple[int, int]]:
    """Return {(champion, opponent_champion): (games, wins)} for the user.

    A single grouped query the recommender can aggregate in memory instead of
    issuing one query per champion.
    """
    query = db.query(
        Match.champion,
        Match.opponent_champion,
        func.count(Match.id).label("games"),
        func.sum(func.cast(Match.win, Integer)).label("wins"),
    ).filter(
        Match.user_id == user_id,
        Match.champion.isnot(None),
        Match.opponent_champion.isnot(None),
    )
    query = _apply_filters(query, role, game_mode)
    rows = query.group_by(Match.champion, Match.opponent_champion).all()

    grid: Dict[Tuple[str, str], Tuple[int, int]] = {}
    for row in rows:
        grid[(row.champion, row.opponent_champion)] = (row.games, row.wins or 0)
    return grid


def champions_vs_opponent(
    db: Session,
    user_id: int,
    opponent: str,
    role: Optional[str] = None,
    game_mode: Optional[str] = None,
    min_games: int = 1,
) -> List[Dict]:
    """The user's champions ranked by win rate when facing `opponent` in lane.

    This answers "which champion that I play should I pick into X?".
    """
    query = db.query(
        Match.champion,
        func.count(Match.id).label("games"),
        func.sum(func.cast(Match.win, Integer)).label("wins"),
    ).filter(
        Match.user_id == user_id,
        Match.opponent_champion == opponent,
        Match.champion.isnot(None),
    )
    query = _apply_filters(query, role, game_mode)
    rows = query.group_by(Match.champion).having(
        func.count(Match.id) >= min_games
    ).all()

    result = []
    for row in rows:
        games = row.games
        wins = row.wins or 0
        result.append({
            "champion": row.champion,
            "games": games,
            "wins": wins,
            "losses": games - wins,
            "win_rate": round(wins / games * 100, 1),
        })
    # Best win rate first; break ties by the larger sample size.
    result.sort(key=lambda x: (x["win_rate"], x["games"]), reverse=True)
    return result


def opponents_faced_on_champion(
    db: Session,
    user_id: int,
    champion: str,
    role: Optional[str] = None,
    game_mode: Optional[str] = None,
    min_games: int = 1,
) -> List[Dict]:
    """Lane opponents the user has faced while playing `champion`.

    Sorted by the user's win rate (best matchups first).
    """
    query = db.query(
        Match.opponent_champion,
        func.count(Match.id).label("games"),
        func.sum(func.cast(Match.win, Integer)).label("wins"),
    ).filter(
        Match.user_id == user_id,
        Match.champion == champion,
        Match.opponent_champion.isnot(None),
    )
    query = _apply_filters(query, role, game_mode)
    rows = query.group_by(Match.opponent_champion).having(
        func.count(Match.id) >= min_games
    ).all()

    result = []
    for row in rows:
        games = row.games
        wins = row.wins or 0
        result.append({
            "champion": row.opponent_champion,
            "games": games,
            "wins": wins,
            "losses": games - wins,
            "win_rate": round(wins / games * 100, 1),
        })
    result.sort(key=lambda x: (x["win_rate"], x["games"]), reverse=True)
    return result


def champion_summary(
    db: Session,
    user_id: int,
    champion: str,
    role: Optional[str] = None,
    game_mode: Optional[str] = None,
) -> Dict:
    """Aggregate the user's performance while playing `champion`.

    `pick_rate` here is a personal metric: the share of the user's games
    (within the current filters) played on this champion.
    """
    total_query = _apply_filters(
        db.query(func.count(Match.id)).filter(Match.user_id == user_id),
        role,
        game_mode,
    )
    total_games = total_query.scalar() or 0

    query = db.query(
        func.count(Match.id).label("games"),
        func.sum(func.cast(Match.win, Integer)).label("wins"),
        func.avg(Match.kills).label("avg_kills"),
        func.avg(Match.deaths).label("avg_deaths"),
        func.avg(Match.assists).label("avg_assists"),
        func.avg(Match.cs_per_min).label("avg_cs_per_min"),
        func.avg(Match.damage_to_champs_per_min).label("avg_damage_per_min"),
    ).filter(
        Match.user_id == user_id,
        Match.champion == champion,
    )
    query = _apply_filters(query, role, game_mode)
    row = query.one()

    games = row.games or 0
    wins = row.wins or 0
    return {
        "games": games,
        "wins": wins,
        "losses": games - wins,
        "win_rate": round(wins / games * 100, 1) if games else 0.0,
        "pick_rate": round(games / total_games * 100, 1) if total_games else 0.0,
        "avg_kda": {
            "kills": round(row.avg_kills or 0, 1),
            "deaths": round(row.avg_deaths or 0, 1),
            "assists": round(row.avg_assists or 0, 1),
        },
        "avg_cs_per_min": round(row.avg_cs_per_min or 0, 1),
        "avg_damage_per_min": round(row.avg_damage_per_min or 0, 0),
    }
