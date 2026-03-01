from sqlalchemy import Column, Integer, Float, String, ForeignKey, CheckConstraint
from app.database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(String(3), primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    economy = Column(Integer, default=0, nullable=False)
    social = Column(Integer, default=0, nullable=False)
    demography = Column(Integer, default=0, nullable=False)
    technology = Column(Integer, default=0, nullable=False)
    military_power = Column(Integer, default=0, nullable=False)
    n_habitants = Column(Integer, default=0, nullable=False)
    latitude = Column(Float, default=0.0, nullable=False)
    longitude = Column(Float, default=0.0, nullable=False)

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    country_1 = Column(String(3), ForeignKey("countries.id"), nullable=False)
    country_2 = Column(String(3), ForeignKey("countries.id"), nullable=False)
    relation = Column(Integer, CheckConstraint('relation >= -100 AND relation <= 100', name='check_relation_range'), nullable=False, default=0)

class Turn(Base):
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(32), index=True, nullable=False)
    turn_number = Column(Integer, nullable=False)
    order = Column(String, nullable=True) 

class CountryStateHistory(Base):
    __tablename__ = "country_state_history"

    id = Column(Integer, primary_key=True, index=True)
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False)
    country_id = Column(String(3), ForeignKey("countries.id"), nullable=False)
    economy = Column(Integer, default=0, nullable=False)
    social = Column(Integer, default=0, nullable=False)
    demography = Column(Integer, default=0, nullable=False)
    technology = Column(Integer, default=0, nullable=False)
    military_power = Column(Integer, default=0, nullable=False)

class RelationshipHistory(Base):
    __tablename__ = "relationship_history"

    id = Column(Integer, primary_key=True, index=True)
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False)
    country_1 = Column(String(3), ForeignKey("countries.id"), nullable=False)
    country_2 = Column(String(3), ForeignKey("countries.id"), nullable=False)
    relation = Column(Integer, CheckConstraint('relation >= -100 AND relation <= 100'), nullable=False, default=0)
    pending_alliance_from = Column(String(3), ForeignKey("countries.id"), nullable=True)

class ActionHistory(Base):
    __tablename__ = "action_history"

    id = Column(Integer, primary_key=True, index=True)
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False)
    country_id = Column(String(3), ForeignKey("countries.id"), nullable=False)
    action_type = Column(String, nullable=False)
    target_id = Column(String(3), ForeignKey("countries.id"), nullable=True)
    intensity = Column(Integer, nullable=True)
    accept = Column(Integer, nullable=True)  # 1 = True, 0 = False, NULL = N/A
    reason = Column(String, nullable=True)