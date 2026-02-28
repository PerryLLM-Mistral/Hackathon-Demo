from typing import List, Literal
from pydantic import BaseModel, Field

RelationLabel = Literal["WAR", "NEUTRAL", "ALLY"]


def relation_label(relation: int) -> RelationLabel:
    """
    Converts numeric relation into a qualitative label.
    Derived value (not stored in DB).
    """
    if relation <= -60:
        return "WAR"
    if relation >= 60:
        return "ALLY"
    return "NEUTRAL"


class CountryState(BaseModel):
    """
    Snapshot of a country (mirrors DB columns in src/models/Country).
    """
    id: str
    name: str

    economy: int = Field(ge=0, le=100)
    social: int = Field(ge=0, le=100)
    demography: int = Field(ge=0, le=100)
    technology: int = Field(ge=0, le=100)
    military_power: int = Field(ge=0, le=100)
    n_habitants: int = Field(ge=0)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class RelationState(BaseModel):
    id: int
    country_1: str
    country_2: str
    relation: int = Field(ge=-100, le=100)

    pending_alliance_from: str | None = None

class WorldState(BaseModel):
    """
    World snapshot passed to agents.
    Built from the 2 DB tables: countries + relationships.
    """
    turn: int
    countries: List[CountryState]
    relations: List[RelationState]