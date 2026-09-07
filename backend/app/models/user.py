from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class User(Base):
    __tablename__ = "users"
    
    # Riot assigns the PUUID and it survives Riot ID and tag changes, so it is
    # the identity. riot_id and tag are display names and carry no index.
    puuid = Column(String(100), primary_key=True)
    riot_id = Column(String(50), nullable=False)
    tag = Column(String(10), nullable=False)
    hashed_password = Column(String(255), nullable=True, default='', server_default='')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    matches = relationship("Match", back_populates="user")
    champion_mastery = relationship("ChampionMastery", back_populates="user")
    
    def __repr__(self):
        return f"<User(riot_id='{self.riot_id}#{self.tag}', puuid='{self.puuid[:8]}…')>"
