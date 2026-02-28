from sqlalchemy import Column, Integer, Float, String, ForeignKey, CheckConstraint
from app.database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(String(3), primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    economy = Column(Integer, default=0, nullable=False)
    social_status = Column(Integer, default=0, nullable=False)
    demography = Column(Integer, default=0, nullable=False)
    technology = Column(Integer, default=0, nullable=False)
    military_power = Column(Integer, default=0, nullable=False)
    num_habitants = Column(Integer, default=0, nullable=False)
    latitude = Column(Float, default=0.0, nullable=False)
    longitude = Column(Float, default=0.0, nullable=False)

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    country_1 = Column(String(3), ForeignKey("countries.id"), nullable=False)
    country_2 = Column(String(3), ForeignKey("countries.id"), nullable=False)
    relation = Column(Integer, CheckConstraint('relation >= -100 AND relation <= 100', name='check_relation_range'), nullable=False, default=0)