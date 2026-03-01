from sqlalchemy.orm import Session
from app.src.models.models import Country

def reset_selected(db: Session):
    """
    Sets the 'selected' column to False for all countries in the database.
    """
    try:
        # Perform an update for the 'selected' flag
        num_updated = db.query(Country).update({Country.selected: False})
        
        # Save changes
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Selection cleared for {num_updated} countries."
        }
    
    except Exception as e:
        # Undo changes if something goes wrong
        db.rollback()
        return {
            "status": "error", 
            "message": str(e)
        }