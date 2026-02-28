from pydantic import BaseModel, Field, ConfigDict

# VALIDATORS FOR COUNTRY MODEL AND ROUTES

class CountryBase(BaseModel):
    name: str = Field(..., min_length=1)
    economy: int = Field(default=0)
    social: int = Field(default=0)
    demography: int = Field(default=0)
    technology: int = Field(default=0)
    military_power: int = Field(default=0)
    n_habitants: int = Field(default=0, ge=0)
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)

class CountryCreate(CountryBase):
    id: str = Field(..., min_length=3, max_length=3, description="Country code must be 3 letters long")

class Country(CountryCreate):
    model_config = ConfigDict(from_attributes=True)



# VALIDATORS FOR RELATIONSHIP MODEL AND ROUTES

class RelationshipBase(BaseModel):
    country_1: str = Field(..., min_length=3, max_length=3)
    country_2: str = Field(..., min_length=3, max_length=3)
    relation: int = Field(default=0, ge=-100, le=100)

class RelationshipCreate(RelationshipBase):
    pass

class Relationship(RelationshipBase):
    id: int

    model_config = ConfigDict(from_attributes=True)