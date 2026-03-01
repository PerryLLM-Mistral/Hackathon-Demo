from sqlalchemy.orm import Session
from app.src.models.models import Country, Relation
from app.multi_llm.schemas.world import WorldState, CountryState, RelationState

AGENT_IDS = ["USA", "CHN", "RUS"]

def build_world_state_for_agents(db: Session, turn: int) -> WorldState:
    # Load only the 3 countries used by the fixed agents
    countries = db.query(Country).filter(Country.id.in_(AGENT_IDS)).all()

    # Load only relations among these 3 countries (any stored order)
    relations = db.query(Relation).filter(
        Relation.country_1.in_(AGENT_IDS),
        Relation.country_2.in_(AGENT_IDS),
    ).all()

    return WorldState(
        turn=turn,
        countries=[
            CountryState(
                id=c.id,
                name=c.name,
                economy=c.economy,
                social=c.social,
                demography=c.demography,
                technology=c.technology,
                military_power=c.military_power,
                n_habitants=c.n_habitants,
            )
            for c in countries
        ],
        relations=[
            RelationState(
                id=r.id,
                country_1=r.country_1,
                country_2=r.country_2,
                value=r.value,
            )
            for r in relations
        ],
    )