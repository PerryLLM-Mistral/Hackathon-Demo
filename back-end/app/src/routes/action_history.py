from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.src.schemas import schemas
from app.src.services.services import ActionHistoryController
from app.database import get_db

router = APIRouter(prefix="/action_history", tags=["ActionHistory"])

# GET todos los registros
@router.get("/", response_model=list[schemas.ActionHistory])
def read_action_history(db: Session = Depends(get_db)):
    return ActionHistoryController.get_all(db)

# POST un nuevo registro
@router.post("/", response_model=schemas.ActionHistory)
def create_action_history(ah: schemas.ActionHistoryCreate, db: Session = Depends(get_db)):
    return ActionHistoryController.create(db, ah)