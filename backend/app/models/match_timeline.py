from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class MatchTimeline(Base):
    """Per-minute laning-phase series derived from the Match-V5 timeline.

    One row per (user, match). The series are cumulative values indexed by
    minute (index 0 = game start), so the frontend can plot the user's CS,
    gold and XP against their lane opponent's over the course of the game.
    """
    __tablename__ = "match_timelines"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Denormalised so aggregation queries don't need to join the matches table.
    champion = Column(String(50), nullable=True)
    opponent_champion = Column(String(50), nullable=True, index=True)
    team_position = Column(String(20), nullable=True)

    # Per-minute cumulative series (JSON arrays, index = minute).
    cs_series = Column(JSON, nullable=True)             # user creep score
    opponent_cs_series = Column(JSON, nullable=True)    # lane opponent creep score
    gold_diff_series = Column(JSON, nullable=True)      # user totalGold - opponent
    xp_diff_series = Column(JSON, nullable=True)        # user xp - opponent

    # Laning-phase checkpoints (user minus opponent), for quick aggregation.
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
