import asyncio
from app.database import SessionLocal
from app.src.models.models import Country, Relationship

async def seed():
    db = SessionLocal()

    # Limpiar datos existentes
    db.query(Relationship).delete()
    db.query(Country).delete()
    db.commit()
    
    # Datos de los países
    countries_data = [
        {
            "id": "USA", 
            "name": "United States",
            "economy": 80, 
            "social": 60, 
            "demography": 50,
            "technology": 90, 
            "military_power": 85,
            "n_habitants": 348483590, 
            "latitude": 37.09024, 
            "longitude": -95.712891
        },
        {
            "id": "CHI", 
            "name": "China",
            "economy": 85, 
            "social": 55, 
            "demography": 60,
            "technology": 80, 
            "military_power": 75,
            "n_habitants": 1412914089, 
            "latitude": 35.86166, 
            "longitude": 104.195397
        },
        {
            "id": "RUS", 
            "name": "Russia",
            "economy": 70, 
            "social": 50, 
            "demography": 55,
            "technology": 75, 
            "military_power": 80,
            "n_habitants": 143453337, 
            "latitude": 61.52401, 
            "longitude": 105.318756
        }
    ]

    for data in countries_data:
        country = db.query(Country).filter(Country.id == data["id"]).first()
        if not country:
            db.add(Country(**data))
            print(f"Country created: {data['id']}")
        else:
            for key, value in data.items():
                setattr(country, key, value)
            print(f"{data['id']} updated with stats.")

    db.commit()

    pairs = [("USA", "CHI"), ("USA", "RUS"), ("CHI", "RUS")]

    for c1, c2 in pairs:
        rel = db.query(Relationship).filter(
            ((Relationship.country_1 == c1) & (Relationship.country_2 == c2)) |
            ((Relationship.country_1 == c2) & (Relationship.country_2 == c1))
        ).first()

        if not rel:
            new_rel = Relationship(
                country_1=c1,
                country_2=c2,
                relation=0  # neutral
            )
            db.add(new_rel)
            print(f"Relationship established: {c1} <-> {c2}")

    db.commit()
    db.close()

if __name__ == "__main__":
    asyncio.run(seed())