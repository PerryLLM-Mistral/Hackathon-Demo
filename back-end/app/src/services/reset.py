from sqlalchemy.orm import Session
from app.src.models.models import Country, Relationship

def reset_stats(db: Session):
    """
    Performs a soft reset: clears all relations and resets game-related 
    statistics to zero while preserving identity and geographical data.
    """
    try:
        # Clear all existing relations
        db.query(Relationship).delete()

        # Retrieve all countries currently in the database
        countries = db.query(Country).all()

        for country in countries:
            # Reset game-specific metrics to zero
            # id, name, latitude and longitude remain untouched
            country.economy = 0
            country.social = 0
            country.demography = 0
            country.technology = 0
            country.military_power = 0
            country.n_habitants = 0 
            
        # Commit changes
        db.commit()
        return {
            "status": "success", 
            "message": "Global stats reset to zero. Identity and coordinates preserved."
        }
    
    except Exception as e:
        # Revert changes
        db.rollback()
        print(f"DEBUG [Reset Error]: {e}")
        return {"status": "error", "message": str(e)}