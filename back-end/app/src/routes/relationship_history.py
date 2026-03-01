from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.src.schemas import schemas
from app.src.services.services import RelationshipHistoryController
from app.database import get_db

router = APIRouter(prefix="/relationship_history", tags=["RelationshipHistory"])

@router.get("/", response_model=list[schemas.RelationshipHistory])
def read_relationship_history(db: Session = Depends(get_db)):
    return RelationshipHistoryController.get_all(db)

@router.post("/", response_model=schemas.RelationshipHistory)
def create_relationship_history(rh: schemas.RelationshipHistoryCreate, db: Session = Depends(get_db)):
    return RelationshipHistoryController.create(db, rh)