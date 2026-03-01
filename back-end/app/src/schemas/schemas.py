from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# VALIDATORS FOR COUNTRY MODEL AND ROUTES

class CountryBase(BaseModel):
    name: str = Field(..., min_length=1)
    economy: int = Field(default=0)
    social: int = Field(default=0)
    demography: int = Field(default=0)
    technology: int = Field(default=0)
    military_power: int = Field(default=0)
    n_habitants: int = Field(default=0, ge=0)
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)

class CountryCreate(CountryBase):
    id: str = Field(..., min_length=3, max_length=3, description="Country code must be 3 letters long")

class Country(CountryCreate):
    model_config = ConfigDict(from_attributes=True)



# VALIDATORS FOR RELATIONSHIP MODEL AND ROUTES

class RelationshipBase(BaseModel):
    country_1: str = Field(..., min_length=3, max_length=3)
    country_2: str = Field(..., min_length=3, max_length=3)
    relation: int = Field(default=0, ge=-100, le=100)

class RelationshipCreate(RelationshipBase):
    pass

class Relationship(RelationshipBase):
    id: int

    model_config = ConfigDict(from_attributes=True)



# VALIDATORS FOR TURN MODEL AND ROUTES

class TurnBase(BaseModel):
    run_id: str = Field(..., min_length=1)
    turn_number: int = Field(..., ge=0)
    order: str | None = None

class TurnCreate(TurnBase):
    pass

class Turn(TurnBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# VALIDATORS FOR COUNTRYSTATEHISTORY MODEL AND ROUTES

class CountryStateHistoryBase(BaseModel):
    turn_id: int
    country_id: str = Field(..., min_length=3, max_length=3)
    economy: int = Field(default=0)
    social: int = Field(default=0)
    demography: int = Field(default=0)
    technology: int = Field(default=0)
    military_power: int = Field(default=0)

class CountryStateHistoryCreate(CountryStateHistoryBase):
    pass

class CountryStateHistory(CountryStateHistoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# VALIDATORS FOR RELATTIONSHIPHISTORY MODEL AND ROUTES

class RelationshipHistoryBase(BaseModel):
    country_1: str = Field(..., min_length=3, max_length=3)
    country_2: str = Field(..., min_length=3, max_length=3)
    relation: int = Field(..., ge=-100, le=100)
    pending_alliance_from: Optional[str] = Field(None, min_length=3, max_length=3)

class RelationshipHistoryCreate(RelationshipHistoryBase):
    turn_id: int

class RelationshipHistory(RelationshipHistoryBase):
    id: int
    turn_id: int

    model_config = ConfigDict(from_attributes=True)



# VALIDATORS FOR ACTIONHISTORY MODEL AND ROUTES

class ActionHistoryBase(BaseModel):
    turn_id: int
    country_id: str = Field(..., min_length=3, max_length=3)
    action_type: str
    target_id: Optional[str] = Field(None, min_length=3, max_length=3)
    intensity: Optional[int] = None
    accept: Optional[int] = None  # 1=True, 0=False, None=N/A
    reason: Optional[str] = None

class ActionHistoryCreate(ActionHistoryBase):
    pass

class ActionHistory(ActionHistoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)