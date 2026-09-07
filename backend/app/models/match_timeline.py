from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class MatchTimeline(Base):
    """Per-minute CS/gold/XP series for a user vs their lane opponent (one row per match)."""
    __tablename__ = "match_timelines"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(50), unique=True, nullable=False, index=True)
    user_puuid = Column(String(100), ForeignKey("users.puuid"), nullable=False, index=True)

    # Denormalised to avoid joining matches.
    champion = Column(String(50), nullable=True)
    opponent_champion = Column(String(50), nullable=True, index=True)
    team_position = Column(String(20), nullable=True)

    # Per-minute cumulative series (JSON arrays, index = minute).
    cs_series = Column(JSON, nullable=True)             # user creep score
    opponent_cs_series = Column(JSON, nullable=True)    # opponent creep score
    gold_diff_series = Column(JSON, nullable=True)      # user gold - opponent
    xp_diff_series = Column(JSON, nullable=True)        # user xp - opponent

    # @10 / @15 checkpoints (user minus opponent).
    cs_diff_at_10 = Column(Integer, nullable=True)
    cs_diff_at_15 = Column(Integer, nullable=True)
    gold_diff_at_10 = Column(Integer, nullable=True)
    gold_diff_at_15 = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    def __repr__(self):
        return (
            f"<MatchTimeline(match_id='{self.match_id}', "
            f"champion='{self.champion}' vs '{self.opponent_champion}')>"
        )
