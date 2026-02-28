from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.database import get_db
from app.src.models import models
from app.src.schemas import schemas

router = APIRouter(prefix="/relationships", tags=["Relationships"])

# CREATE RELATIONSHIP BETWEEN COUNTRIES
@router.post("/", response_model=schemas.Relationship)
def create_relationship(rel: schemas.RelationshipCreate, db: Session = Depends(get_db)):
    # Check that both countries exist
    country_1 = db.query(models.Country).filter(models.Country.id == rel.country_1.upper()).first()
    country_2 = db.query(models.Country).filter(models.Country.id == rel.country_2.upper()).first()
    
    if not country_1 or not country_2:
        raise HTTPException(status_code=404, detail="One or both countries do not exist")

    # Avoid relationship between the same country
    if rel.country_1 == rel.country_2:
        raise HTTPException(status_code=400, detail="A country can not have a relationship with itself")

    # Create and save object
    new_rel = models.Relationship(**rel.model_dump())
    db.add(new_rel)
    db.commit()
    db.refresh(new_rel)
    
    return new_rel

# GET ALL RELATIONSHIPS
@router.get("/", response_model=List[schemas.Relationship])
def get_relationships(db: Session = Depends(get_db)):
    return db.query(models.Relationship).all()

# GET ALL RELATIONSHIPS FOR A SPECIFIC COUNTRY
@router.get("/{country_id}", response_model=List[schemas.Relationship])
def get_relationships_by_country(country_id: str, db: Session = Depends(get_db)):
    # Search for relationships where the ID matches either column
    relationships = db.query(models.Relationship).filter(
        or_(
            models.Relationship.country_1 == country_id.upper(),
            models.Relationship.country_2 == country_id.upper()
        )
    ).all()

    # Check if the country exists
    country_exists = db.query(models.Country).filter(models.Country.id == country_id.upper()).first()
    if not country_exists:
        raise HTTPException(status_code=404, detail=f"Country '{country_id}' not found")

    return relationships 