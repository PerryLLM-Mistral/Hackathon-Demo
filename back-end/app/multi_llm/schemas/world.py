from typing import List, Literal
from pydantic import BaseModel, Field


RelationLabel = Literal["WAR", "NEUTRAL", "ALLY"]


def relation_label(value: int) -> RelationLabel:
    """
    Converts numeric relation value into a qualitative label.
    This label is derived, not stored in the database.
    """
    if value <= -90:
        return "WAR"
    if value >= 60:
        return "ALLY"
    return "NEUTRAL"


class CountryState(BaseModel):
    """
    Snapshot of a country (from DB).
    """

    id: str  # USA, CHI, RUS
    name: str

    economy: int = Field(ge=0, le=100)
    social: int = Field(ge=0, le=100)
    demography: int = Field(ge=0, le=100)
    technology: int = Field(ge=0, le=100)
    military_power: int = Field(ge=0, le=100)
    n_habitants: int = Field(ge=0)


class RelationState(BaseModel):
    """
    Snapshot of a relation between two countries.
    """

    id: int
    country_1: str
    country_2: str
    value: int = Field(ge=-100, le=100)
    def label(self) -> RelationLabel:
        """
        Returns derived qualitative label for LLM context or UI.
        """
        return relation_label(self.value)


class WorldState(BaseModel):
    """
    Snapshot of the world passed to agents.

    Built from:
        - countries table
        - relations table

    'turn' is not stored in DB. It lives in memory.
    """

    turn: int
    countries: List[CountryState]
    relations: List[RelationState]