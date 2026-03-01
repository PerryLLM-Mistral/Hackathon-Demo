from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.src.services import reset
from app.src.routes.simulation import sim_engine, RUN_ID

router = APIRouter(prefix="/reset", tags=["Reset Database"])

@router.post("/reset")
async def handle_reset(db: Session = Depends(get_db)):
    # Call the controller logic
    result = reset.reset_selected(db)
    
    # If the controller returned an error status, raise an exception
    if result["status"] == "error":
        raise HTTPException(
            status_code=500, 
            detail=f"Database operation failed: {result['message']}"
        )
    
    sim_engine.force_reload(db, RUN_ID)
        
    return result