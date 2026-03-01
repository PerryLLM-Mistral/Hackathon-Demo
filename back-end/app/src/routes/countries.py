from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.src.models import models
from app.src.schemas import schemas
from app.src.services.services import CountryController

router = APIRouter(prefix="/countries", tags=["Countries"])

# CREATE COUNTRY
@router.post("/", response_model=schemas.Country)
def create_country(country: schemas.CountryCreate, db: Session = Depends(get_db)):
    # Check if country already exists
    if CountryController.get_by_id(db, country.id):
        raise HTTPException(status_code=400, detail="Country ID already registered")
    
    # Delegate creation logic to the controller
    return CountryController.create(db, country)


# GET ALL COUNTRIES
@router.get("/", response_model=List[schemas.Country])
def get_countries(db: Session = Depends(get_db)):
    return CountryController.get_all(db)


# GET ALL SELECTED COUNTRIES
@router.get("/selected", response_model=List[schemas.Country])
def get_selected_countries(db: Session = Depends(get_db)):
    # Get the list of countries currently selected by the user
    return CountryController.get_selected(db)


# SELECT MULTIPLE COUNTRIES AT ONCE
@router.patch("/select-multiple")
def select_multiple_countries(country_ids: List[str] = Body(...), db: Session = Depends(get_db)):
    try:
        # Call controller method to change 'selected' flag to True
        success = CountryController.select_countries(db, country_ids)
        if not success:
            raise HTTPException(status_code=400, detail="Error updating selection")
        
        return {"status": "success", "message": f"{len(country_ids)} selected countries", "data": success}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# GET COUNTRY BY ID
@router.get("/{country_id}", response_model=schemas.Country)
def get_country_by_id(country_id: str, db: Session = Depends(get_db)):
    # Use the controller to find the specific country
    db_country = CountryController.get_by_id(db, country_id)
    if not db_country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return db_country