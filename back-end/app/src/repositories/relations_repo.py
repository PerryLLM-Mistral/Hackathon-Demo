from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.src.models.models import Relation

def get_relation_by_pair(db: Session, a: str, b: str) -> Relation | None:
    return (
        db.query(Relation)
        .filter(
            or_(
                and_(Relation.country_1 == a, Relation.country_2 == b),
                and_(Relation.country_1 == b, Relation.country_2 == a),
            )
        )
        .one_or_none()
    )

def create_or_get_relation(db: Session, a: str, b: str, initial_value: int = 0) -> Relation:
    rel = get_relation_by_pair(db, a, b)
    if rel is not None:
        return rel

    rel = Relation(country_1=a, country_2=b, value=initial_value)
    db.add(rel)
    db.flush()
    return rel

def set_relation_value_by_pair(db: Session, a: str, b: str, new_value: int) -> Relation:
    rel = create_or_get_relation(db, a, b, initial_value=new_value)
    rel.value = new_value
    db.add(rel)
    return rel