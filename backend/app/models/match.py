from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(50), unique=True, nullable=False, index=True)
    user_puuid = Column(String(100), ForeignKey("users.puuid"), nullable=False, index=True)
    
    # Match details
    champion = Column(String(50), nullable=False)
    opponent_champion = Column(String(50), nullable=True)
    team_position = Column(String(20), nullable=False)
    win = Column(Boolean, nullable=False)
    game_duration = Column(Float, nullable=False)  # in minutes
    # Performance stats
    kills = Column(Integer, nullable=False)
    deaths = Column(Integer, nullable=False)
    assists = Column(Integer, nullable=False)
    cs_per_min = Column(Float, nullable=False)
    gold_per_min = Column(Float, nullable=False)
    kill_participation = Column(Float, nullable=False)
    damage_to_champs_per_min = Column(Float, nullable=False)

    # Vision (from Match-V5 participant object)
    vision_score = Column(Integer, nullable=True, default=0)
    wards_placed = Column(Integer, nullable=True, default=0)
    wards_killed = Column(Integer, nullable=True, default=0)
    control_wards_bought = Column(Integer, nullable=True, default=0)

    # Damage breakdown
    damage_taken = Column(Integer, nullable=True, default=0)
    damage_self_mitigated = Column(Integer, nullable=True, default=0)
    damage_to_turrets = Column(Integer, nullable=True, default=0)
    damage_to_objectives = Column(Integer, nullable=True, default=0)
    total_heal = Column(Integer, nullable=True, default=0)

    # Objective participation
    turret_takedowns = Column(Integer, nullable=True, default=0)
    inhibitor_takedowns = Column(Integer, nullable=True, default=0)
    dragon_kills = Column(Integer, nullable=True, default=0)
    baron_kills = Column(Integer, nullable=True, default=0)
    objectives_stolen = Column(Integer, nullable=True, default=0)
    first_blood = Column(Boolean, nullable=True, default=False)
    first_tower = Column(Boolean, nullable=True, default=False)

    # Economy and level
    gold_earned = Column(Integer, nullable=True, default=0)
    total_cs = Column(Integer, nullable=True, default=0)
    champ_level = Column(Integer, nullable=True, default=0)

    # Combat highlights
    largest_killing_spree = Column(Integer, nullable=True, default=0)
    largest_multi_kill = Column(Integer, nullable=True, default=0)
    double_kills = Column(Integer, nullable=True, default=0)
    triple_kills = Column(Integer, nullable=True, default=0)
    quadra_kills = Column(Integer, nullable=True, default=0)
    penta_kills = Column(Integer, nullable=True, default=0)
    time_ccing_others = Column(Integer, nullable=True, default=0)

    # Game mode and queue info
    queue_id = Column(Integer, nullable=True)
    game_mode = Column(String(50), nullable=True)

    # Timestamps
    game_creation = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="matches")
    
    def __repr__(self):
        return f"<Match(match_id='{self.match_id}', champion='{self.champion}', win={self.win})>"
