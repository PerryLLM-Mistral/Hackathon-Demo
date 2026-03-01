import asyncio
import random
from app.database import SessionLocal
from app.src.models.models import Country, Relationship, Turn, ActionHistory, CountryStateHistory, RelationshipHistory
from app.scripts.data import COUNTRIES_DATA


def clear_all_tables(db):
    db.query(ActionHistory).delete()
    db.query(RelationshipHistory).delete()
    db.query(CountryStateHistory).delete()
    db.query(Turn).delete()
    db.query(Relationship).delete()
    db.query(Country).delete()
    db.commit()


def populate_world(db):
    """Insert countries with default values and add random relationships."""

    # Add countries with default values
    unique_countries = {c['id']: c for c in COUNTRIES_DATA}.values()
        
    for data in unique_countries:
        db.add(Country(**data))

    db.commit()

    # Load existing IDs
    country_ids = [c[0] for c in db.query(Country.id).all()]

    REL_MIN, REL_MAX = -100, 100
    K_PER_COUNTRY = 8

    # In case there are not enough countries
    if len(country_ids) < 2:
        db.close()
        raise RuntimeError("At least 2 countries needed to create relationships.")

    # Generate unique relationships
    for c1 in country_ids:
        candidates = [c for c in country_ids if c != c1]
        picks = random.sample(candidates, k=min(K_PER_COUNTRY, len(candidates)))

        for c2 in picks:
            a, b = sorted([c1, c2])

            rel = db.query(Relationship).filter(
                (Relationship.country_1 == a) & (Relationship.country_2 == b)
            ).first()

            if not rel:
                db.add(Relationship(
                    country_1=a,
                    country_2=b,
                    relation=random.randint(REL_MIN, REL_MAX)
                ))
            else:
                rel.relation = random.randint(REL_MIN, REL_MAX)

    db.commit()


async def seed():
    db = SessionLocal()

    try:
        # Clean existing data
        clear_all_tables(db)
        
        # Add countries and relationships
        populate_world(db)

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
    finally:
        db.close()