from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.src.models import models
from app.src.schemas import schemas


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