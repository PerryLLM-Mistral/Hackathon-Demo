from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.src.models import models
from app.src.schemas import schemas

router = APIRouter(prefix="/countries", tags=["Countries"])

# CREATE COUNTRY
@router.post("/", response_model=schemas.Country)
def create_country(country: schemas.CountryCreate, db: Session = Depends(get_db)):
    # Check if ID already exists
    db_country = db.query(models.Country).filter(models.Country.id == country.id.upper()).first()
    if db_country:
        raise HTTPException(status_code=400, detail="Country ID already registered")
    
    # Create and save object
    new_country = models.Country(**country.model_dump())
    db.add(new_country)
    db.commit()
    db.refresh(new_country)

    return new_country

# GET ALL COUNTRIES
@router.get("/", response_model=List[schemas.Country])
def get_countries(db: Session = Depends(get_db)):
    return db.query(models.Country).all()

# GET COUNTRY BY ID
@router.get("/{country_id}", response_model=schemas.Country)
def get_country_by_id(country_id: str, db: Session = Depends(get_db)):
    # Check if that country by ID exists
    db_country = db.query(models.Country).filter(models.Country.id == country_id.upper()).first()
    if not db_country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return db_country