from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.src.schemas import schemas
from app.src.services.services import TurnController
from app.database import get_db

router = APIRouter(prefix="/turns", tags=["Turns"])

# GET todos los turns
@router.get("/", response_model=list[schemas.Turn])
def read_turns(db: Session = Depends(get_db)):
    turns = TurnController.get_all(db)
    return turns

# POST un nuevo turn
@router.post("/", response_model=schemas.Turn)
def create_turn(turn: schemas.TurnCreate, db: Session = Depends(get_db)):
    new_turn = TurnController.create(db, turn)
    return new_turn