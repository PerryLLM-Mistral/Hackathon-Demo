from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.database import get_db
from app.src.models import models
from app.src.schemas import schemas
from app.src.services.services import CountryController, RelationshipController

router = APIRouter(prefix="/relationships", tags=["Relationships"])

# CREATE RELATIONSHIP BETWEEN COUNTRIES
@router.post("/", response_model=schemas.Relationship)
def create_relationship(rel: schemas.RelationshipCreate, db: Session = Depends(get_db)):
    # Validate that both countries exist using the CountryController
    if not CountryController.get_by_id(db, rel.country_1) or not CountryController.get_by_id(db, rel.country_2):
        raise HTTPException(status_code=404, detail="One or both countries do not exist")

    # Avoid relationship between the same country
    if rel.country_1.upper() == rel.country_2.upper():
        raise HTTPException(status_code=400, detail="A country can not have a relationship with itself")

    # Delegate relationship creation to its controller
    return RelationshipController.create(db, rel)

# GET ALL RELATIONSHIPS
@router.get("/", response_model=List[schemas.Relationship])
def get_relationships(db: Session = Depends(get_db)):
    return RelationshipController.get_all(db)

# GET ALL RELATIONSHIPS FOR A SPECIFIC COUNTRY
@router.get("/{country_id}", response_model=List[schemas.Relationship])
def get_relationships_by_country(country_id: str, db: Session = Depends(get_db)):
    # Verify if the country exists
    if not CountryController.get_by_id(db, country_id):
        raise HTTPException(status_code=404, detail=f"Country '{country_id}' not found")

    # Use the controller to fetch filtered relationships
    return RelationshipController.get_by_country(db, country_id)