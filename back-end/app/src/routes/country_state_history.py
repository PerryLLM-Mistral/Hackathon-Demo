from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.src.schemas import schemas
from app.src.services.services import CountryStateHistoryController
from app.database import get_db

router = APIRouter(prefix="/country_state_history", tags=["CountryStateHistory"])

@router.get("/", response_model=list[schemas.CountryStateHistory])
def read_country_states(db: Session = Depends(get_db)):
    return CountryStateHistoryController.get_all(db)

@router.post("/", response_model=schemas.CountryStateHistory)
def create_country_state(state: schemas.CountryStateHistoryCreate, db: Session = Depends(get_db)):
    return CountryStateHistoryController.create(db, state)