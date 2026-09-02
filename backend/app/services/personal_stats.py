"""Personal statistics derived from the user's own match history.

Every function here computes stats from the `matches` table (real Riot
Match-V5 data the app already ingests) - there is no web scraping and no
fabricated data. When a user has no games matching a query, the caller gets
an empty result rather than a made-up one.
"""
from math import sqrt
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import Integer, func

from app.models.match import Match
from app.models.match_timeline import MatchTimeline

# z-score for a 95% confidence interval, used by the Wilson score below.
_WILSON_Z = 1.96


def wilson_lower_bound(wins: int, games: int, z: float = _WILSON_Z) -> float:
    """Lower bound of the Wilson score interval for a win rate, as a percentage.

    A raw win rate treats 2/2 (100%) as better than 40/60 (67%), which is
    misleading on tiny samples. The Wilson lower bound discounts a win rate by
    how little data backs it, so a champion needs both a good record *and*
    enough games to rank highly. Returns 0.0 when there are no games.
    """
    if games <= 0:
        return 0.0
    phat = wins / games
    denom = 1 + z * z / games
    centre = phat + z * z / (2 * games)
    margin = z * sqrt((phat * (1 - phat) + z * z / (4 * games)) / games)
    return round(max(0.0, (centre - margin) / denom) * 100, 1)

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
            "confidence": wilson_lower_bound(wins, games),
        })
    # Rank by the confidence-adjusted win rate so a 2-0 record doesn't leapfrog
    # a proven one; fall back to raw win rate, then sample size, for ties.
    result.sort(
        key=lambda x: (x["confidence"], x["win_rate"], x["games"]),
        reverse=True,
    )
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
            "confidence": wilson_lower_bound(wins, games),
        })
    result.sort(
        key=lambda x: (x["confidence"], x["win_rate"], x["games"]),
        reverse=True,
    )
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


def _average_series(series_list: List[List], max_len: int) -> List[float]:
    """Element-wise average of several sequences, per index, up to max_len.

    Each index is averaged only over the games that actually reached that
    minute, so a long game doesn't drag the early-game average around.
    """
    sums: List[float] = []
    counts: List[int] = []
    for series in series_list:
        if not series:
            continue
        for i, value in enumerate(series):
            if i >= max_len:
                break
            if i >= len(sums):
                sums.append(0.0)
                counts.append(0)
            sums[i] += value
            counts[i] += 1
    return [round(sums[i] / counts[i], 1) for i in range(len(sums)) if counts[i]]


def _average_checkpoint(values: List[Optional[int]]) -> Optional[float]:
    """Average a checkpoint metric, ignoring games that ended before it."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 1)


def lane_timeline_vs_opponent(
    db: Session,
    user_id: int,
    opponent: str,
    role: Optional[str] = None,
    min_games: int = 1,
    max_minutes: int = 20,
) -> Dict:
    """Averaged per-minute CS / gold-diff series for the user vs `opponent`.

    Aggregates the stored timelines of every lane game the user played into
    `opponent`, producing chartable series: the user's average CS by minute,
    the opponent's average CS, the CS lead (user minus opponent) and the gold
    lead, plus the classic @10 / @15 laning checkpoints.
    """
    query = db.query(MatchTimeline).filter(
        MatchTimeline.user_id == user_id,
        MatchTimeline.opponent_champion == opponent,
    )
    if role:
        query = query.filter(MatchTimeline.team_position == role)
    rows = query.all()

    empty = {
        "opponent": opponent,
        "games": len(rows),
        "cs_series": [],
        "opponent_cs_series": [],
        "cs_diff_series": [],
        "gold_diff_series": [],
        "avg_cs_diff_at_10": None,
        "avg_cs_diff_at_15": None,
        "avg_gold_diff_at_10": None,
        "avg_gold_diff_at_15": None,
    }
    if len(rows) < min_games:
        return empty

    cs_avg = _average_series([r.cs_series for r in rows], max_minutes)
    opp_cs_avg = _average_series([r.opponent_cs_series for r in rows], max_minutes)
    gold_diff_avg = _average_series([r.gold_diff_series for r in rows], max_minutes)

    # CS lead per minute over the range both averaged series cover.
    paired = min(len(cs_avg), len(opp_cs_avg))
    cs_diff_series = [round(cs_avg[i] - opp_cs_avg[i], 1) for i in range(paired)]

    return {
        "opponent": opponent,
        "games": len(rows),
        "cs_series": cs_avg,
        "opponent_cs_series": opp_cs_avg,
        "cs_diff_series": cs_diff_series,
        "gold_diff_series": gold_diff_avg,
        "avg_cs_diff_at_10": _average_checkpoint([r.cs_diff_at_10 for r in rows]),
        "avg_cs_diff_at_15": _average_checkpoint([r.cs_diff_at_15 for r in rows]),
        "avg_gold_diff_at_10": _average_checkpoint([r.gold_diff_at_10 for r in rows]),
        "avg_gold_diff_at_15": _average_checkpoint([r.gold_diff_at_15 for r in rows]),
    }
