# multi-llm/app/schemas/world.py
from pydantic import BaseModel
from typing import List, Optional

class CountryState(BaseModel):
    id: str
    name: str
    power: float = 1.0

class RelationState(BaseModel):
    a: str
    b: str
    score: int  # -100..100
    relation: str  # "WAR"|"ALLY"|"NEUTRAL"

class Event(BaseModel):
    turn: int
    text: str

class WorldState(BaseModel):
    turn: int
    countries: List[CountryState]
    relations: List[RelationState]
    recent_events: List[Event] = []