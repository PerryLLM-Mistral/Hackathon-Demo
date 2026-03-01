from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.src.models import models
from app.src.schemas import schemas
from app.multi_llm.schemas import Action

# CONTROLLER FOR COUNTRY MODEL

class CountryController:

    @staticmethod
    def get_all(db: Session):
        # Retrieve all countries from the Country table
        return db.query(models.Country).all()

    @staticmethod
    def get_by_id(db: Session, country_id: str):
        # Search for a country using its unique ID
        return db.query(models.Country).filter(models.Country.id == country_id.upper()).first()

    @staticmethod
    def create(db: Session, country_data: schemas.CountryCreate):
        # Convert Pydantic schema to SQLAlchemy model
        new_country = models.Country(**country_data.model_dump())

        # Add the new object to the database
        db.add(new_country)

        # Save changes
        db.commit()

        # Refresh the object
        db.refresh(new_country)

        return new_country
    
    @staticmethod
    def get_selected(db: Session):
        # Retrieve only the countries that have the 'selected' flag set to True
        return db.query(models.Country).filter(models.Country.selected == True).all()



# CONTROLLER FOR RELATIONSHIP MODEL

class RelationshipController:

    @staticmethod
    def get_all(db: Session):
        # Fetch every relationship stored in the database
        return db.query(models.Relationship).all()

    @staticmethod
    def get_by_country(db: Session, country_id: str):
        # Find relationships where the given country is either the initiator or the receiver
        return db.query(models.Relationship).filter(
            or_(
                models.Relationship.country_1 == country_id.upper(),
                models.Relationship.country_2 == country_id.upper()
            )
        ).all()

    @staticmethod
    def create(db: Session, rel_data: schemas.RelationshipCreate):
        # Create a relationship instance
        new_rel = models.Relationship(**rel_data.model_dump())
        
        # Add the new relationship to the database
        db.add(new_rel)
        
        # Save changes
        db.commit()
        
        # Refresh the object
        db.refresh(new_rel)
        
        return new_rel


# CONTROLLER FOR TURN MODEL

class TurnController:

    @staticmethod
    def get_all(db: Session):
        return db.query(models.Turn).all()

    @staticmethod
    def get_by_id(db: Session, turn_id: int):
        return db.query(models.Turn).filter(models.Turn.id == turn_id).first()

    @staticmethod
    def create(db: Session, turn_data: schemas.TurnCreate):
        new_turn = models.Turn(**turn_data.model_dump())
        db.add(new_turn)
        db.commit()
        db.refresh(new_turn)
        return new_turn
    

# CONTROLLER FOR COUNTRYSTATEHISTORY MODEL

class CountryStateHistoryController:

    @staticmethod
    def get_all(db: Session):
        return db.query(models.CountryStateHistory).all()

    @staticmethod
    def get_by_id(db: Session, state_id: int):
        return db.query(models.CountryStateHistory).filter(models.CountryStateHistory.id == state_id).first()

    @staticmethod
    def create(db: Session, state_data: schemas.CountryStateHistoryCreate):
        new_state = models.CountryStateHistory(**state_data.model_dump())
        db.add(new_state)
        db.commit()
        db.refresh(new_state)
        return new_state


# CONTROLLER FOR RELATIONSHIPHISTORY MODEL

class RelationshipHistoryController:

    @staticmethod
    def get_all(db: Session):
        return db.query(models.RelationshipHistory).all()

    @staticmethod
    def create(db: Session, rh_data: schemas.RelationshipHistoryCreate):
        new_rh = models.RelationshipHistory(**rh_data.model_dump())
        db.add(new_rh)
        db.commit()
        db.refresh(new_rh)
        return new_rh
    

# CONTROLLER FOR ACTIONHISTORY MODEL

class ActionHistoryController:

    @staticmethod
    def get_all(db: Session):
        return db.query(models.ActionHistory).all()

    @staticmethod
    def create(db: Session, ah_data: schemas.ActionHistoryCreate):
        new_ah = models.ActionHistory(**ah_data.model_dump())
        db.add(new_ah)
        db.commit()
        db.refresh(new_ah)
        return new_ah