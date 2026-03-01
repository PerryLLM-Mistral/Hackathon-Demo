import asyncio
import random
from app.database import SessionLocal
from app.src.models.models import Country, Relationship

async def seed():
    db = SessionLocal()

    # Clean existing data
    db.query(Relationship).delete()
    db.query(Country).delete()
    db.commit()

    countries_data = [
        # --- North America & Caribbean ---
        {"id": "USA", "name": "United States", "economy": 95, "social": 60, "demography": 50, "technology": 98, "military_power": 99, "n_habitants": 348483590, "latitude": 37.0902, "longitude": -95.7129, "selected": False},
        {"id": "CAN", "name": "Canada", "economy": 80, "social": 85, "demography": 40, "technology": 85, "military_power": 60, "n_habitants": 38246108, "latitude": 56.1304, "longitude": -106.3468, "selected": False},
        {"id": "MEX", "name": "Mexico", "economy": 70, "social": 55, "demography": 70, "technology": 65, "military_power": 55, "n_habitants": 129000000, "latitude": 23.0, "longitude": -102.0, "selected": False},
        {"id": "GTM", "name": "Guatemala", "economy": 45, "social": 45, "demography": 65, "technology": 40, "military_power": 30, "n_habitants": 18000000, "latitude": 15.5, "longitude": -90.25, "selected": False},
        {"id": "CUB", "name": "Cuba", "economy": 40, "social": 55, "demography": 55, "technology": 45, "military_power": 35, "n_habitants": 11200000, "latitude": 21.5, "longitude": -80.0, "selected": False},
        {"id": "DOM", "name": "Dominican Republic", "economy": 50, "social": 50, "demography": 60, "technology": 45, "military_power": 30, "n_habitants": 11000000, "latitude": 19.0, "longitude": -70.6667, "selected": False},
        {"id": "HTI", "name": "Haiti", "economy": 25, "social": 30, "demography": 60, "technology": 20, "military_power": 15, "n_habitants": 11400000, "latitude": 19.0, "longitude": -72.4167, "selected": False},
        {"id": "JAM", "name": "Jamaica", "economy": 45, "social": 55, "demography": 50, "technology": 40, "military_power": 20, "n_habitants": 3000000, "latitude": 18.25, "longitude": -77.5, "selected": False},
        {"id": "PAN", "name": "Panama", "economy": 55, "social": 55, "demography": 55, "technology": 50, "military_power": 20, "n_habitants": 4400000, "latitude": 9.0, "longitude": -80.0, "selected": False},
        {"id": "CRI", "name": "Costa Rica", "economy": 55, "social": 70, "demography": 45, "technology": 55, "military_power": 10, "n_habitants": 5200000, "latitude": 10.0, "longitude": -84.0, "selected": False},

        # --- South America ---
        {"id": "BRA", "name": "Brazil", "economy": 68, "social": 50, "demography": 75, "technology": 65, "military_power": 60, "n_habitants": 214300000, "latitude": -14.0, "longitude": -51.0, "selected": False},
        {"id": "ARG", "name": "Argentina", "economy": 55, "social": 55, "demography": 55, "technology": 55, "military_power": 40, "n_habitants": 46000000, "latitude": -34.0, "longitude": -64.0, "selected": False},
        {"id": "CHL", "name": "Chile", "economy": 60, "social": 60, "demography": 45, "technology": 60, "military_power": 45, "n_habitants": 19500000, "latitude": -30.0, "longitude": -71.0, "selected": False},
        {"id": "COL", "name": "Colombia", "economy": 55, "social": 50, "demography": 65, "technology": 50, "military_power": 45, "n_habitants": 52000000, "latitude": 4.0, "longitude": -72.0, "selected": False},
        {"id": "PER", "name": "Peru", "economy": 50, "social": 50, "demography": 60, "technology": 45, "military_power": 35, "n_habitants": 34000000, "latitude": -10.0, "longitude": -76.0, "selected": False},
        {"id": "VEN", "name": "Venezuela", "economy": 35, "social": 35, "demography": 60, "technology": 35, "military_power": 35, "n_habitants": 28000000, "latitude": 8.0, "longitude": -66.0, "selected": False},
        {"id": "ECU", "name": "Ecuador", "economy": 45, "social": 50, "demography": 55, "technology": 40, "military_power": 25, "n_habitants": 18000000, "latitude": -2.0, "longitude": -77.5, "selected": False},
        {"id": "BOL", "name": "Bolivia", "economy": 40, "social": 45, "demography": 55, "technology": 35, "military_power": 20, "n_habitants": 12000000, "latitude": -17.0, "longitude": -65.0, "selected": False},
        {"id": "PRY", "name": "Paraguay", "economy": 40, "social": 45, "demography": 50, "technology": 35, "military_power": 20, "n_habitants": 7300000, "latitude": -23.0, "longitude": -58.0, "selected": False},
        {"id": "URY", "name": "Uruguay", "economy": 55, "social": 70, "demography": 40, "technology": 55, "military_power": 20, "n_habitants": 3500000, "latitude": -33.0, "longitude": -56.0, "selected": False},

        # --- Europe ---
        {"id": "ESP", "name": "Spain", "economy": 75, "social": 75, "demography": 45, "technology": 75, "military_power": 55, "n_habitants": 48000000, "latitude": 40.0, "longitude": -4.0, "selected": False},
        {"id": "PRT", "name": "Portugal", "economy": 65, "social": 75, "demography": 45, "technology": 65, "military_power": 35, "n_habitants": 10300000, "latitude": 39.5, "longitude": -8.0, "selected": False},
        {"id": "FRA", "name": "France", "economy": 85, "social": 70, "demography": 50, "technology": 88, "military_power": 85, "n_habitants": 67500000, "latitude": 46.0, "longitude": 2.0, "selected": False},
        {"id": "DEU", "name": "Germany", "economy": 90, "social": 82, "demography": 45, "technology": 92, "military_power": 65, "n_habitants": 83200000, "latitude": 51.0, "longitude": 9.0, "selected": False},
        {"id": "GBR", "name": "United Kingdom", "economy": 84, "social": 72, "demography": 48, "technology": 89, "military_power": 86, "n_habitants": 67300000, "latitude": 54.0, "longitude": -2.0, "selected": False},
        {"id": "ITA", "name": "Italy", "economy": 75, "social": 70, "demography": 40, "technology": 75, "military_power": 60, "n_habitants": 59000000, "latitude": 42.8333, "longitude": 12.8333, "selected": False},
        {"id": "NLD", "name": "Netherlands", "economy": 80, "social": 80, "demography": 45, "technology": 85, "military_power": 45, "n_habitants": 17800000, "latitude": 52.5, "longitude": 5.75, "selected": False},
        {"id": "BEL", "name": "Belgium", "economy": 75, "social": 78, "demography": 45, "technology": 75, "military_power": 40, "n_habitants": 11800000, "latitude": 50.8333, "longitude": 4.0, "selected": False},
        {"id": "CHE", "name": "Switzerland", "economy": 85, "social": 85, "demography": 40, "technology": 85, "military_power": 35, "n_habitants": 9000000, "latitude": 47.0, "longitude": 8.0, "selected": False},
        {"id": "AUT", "name": "Austria", "economy": 75, "social": 80, "demography": 45, "technology": 75, "military_power": 35, "n_habitants": 9100000, "latitude": 47.3333, "longitude": 13.3333, "selected": False},
        {"id": "SWE", "name": "Sweden", "economy": 80, "social": 88, "demography": 45, "technology": 85, "military_power": 50, "n_habitants": 10600000, "latitude": 62.0, "longitude": 15.0, "selected": False},
        {"id": "NOR", "name": "Norway", "economy": 82, "social": 90, "demography": 40, "technology": 82, "military_power": 45, "n_habitants": 5500000, "latitude": 62.0, "longitude": 10.0, "selected": False},
        {"id": "DNK", "name": "Denmark", "economy": 78, "social": 88, "demography": 45, "technology": 80, "military_power": 40, "n_habitants": 5900000, "latitude": 56.0, "longitude": 10.0, "selected": False},
        {"id": "FIN", "name": "Finland", "economy": 75, "social": 85, "demography": 45, "technology": 80, "military_power": 50, "n_habitants": 5600000, "latitude": 64.0, "longitude": 26.0, "selected": False},
        {"id": "POL", "name": "Poland", "economy": 65, "social": 60, "demography": 55, "technology": 65, "military_power": 55, "n_habitants": 38000000, "latitude": 52.0, "longitude": 20.0, "selected": False},
        {"id": "UKR", "name": "Ukraine", "economy": 45, "social": 45, "demography": 50, "technology": 50, "military_power": 60, "n_habitants": 37000000, "latitude": 49.0, "longitude": 32.0, "selected": False},
        {"id": "ROU", "name": "Romania", "economy": 55, "social": 55, "demography": 50, "technology": 55, "military_power": 45, "n_habitants": 19000000, "latitude": 46.0, "longitude": 25.0, "selected": False},
        {"id": "GRC", "name": "Greece", "economy": 55, "social": 60, "demography": 45, "technology": 55, "military_power": 55, "n_habitants": 10400000, "latitude": 39.0, "longitude": 22.0, "selected": False},
        {"id": "IRL", "name": "Ireland", "economy": 80, "social": 80, "demography": 45, "technology": 85, "military_power": 20, "n_habitants": 5200000, "latitude": 53.0, "longitude": -8.0, "selected": False},
        {"id": "CZE", "name": "Czechia", "economy": 65, "social": 65, "demography": 45, "technology": 65, "military_power": 35, "n_habitants": 10900000, "latitude": 49.75, "longitude": 15.5, "selected": False},
        {"id": "HUN", "name": "Hungary", "economy": 55, "social": 55, "demography": 45, "technology": 55, "military_power": 30, "n_habitants": 9600000, "latitude": 47.0, "longitude": 20.0, "selected": False},

        # --- Middle East ---
        {"id": "ISR", "name": "Israel", "economy": 70, "social": 60, "demography": 20, "technology": 94, "military_power": 82, "n_habitants": 9360000, "latitude": 31.0, "longitude": 34.75, "selected": False},
        {"id": "SAU", "name": "Saudi Arabia", "economy": 70, "social": 45, "demography": 55, "technology": 60, "military_power": 75, "n_habitants": 36000000, "latitude": 25.0, "longitude": 45.0, "selected": False},
        {"id": "ARE", "name": "United Arab Emirates", "economy": 75, "social": 55, "demography": 45, "technology": 70, "military_power": 55, "n_habitants": 10000000, "latitude": 24.0, "longitude": 54.0, "selected": False},
        {"id": "IRN", "name": "Iran", "economy": 55, "social": 45, "demography": 65, "technology": 55, "military_power": 70, "n_habitants": 88000000, "latitude": 32.0, "longitude": 53.0, "selected": False},
        {"id": "TUR", "name": "Turkey", "economy": 65, "social": 55, "demography": 60, "technology": 60, "military_power": 75, "n_habitants": 85000000, "latitude": 39.0, "longitude": 35.0, "selected": False},
        {"id": "EGY", "name": "Egypt", "economy": 50, "social": 45, "demography": 80, "technology": 45, "military_power": 65, "n_habitants": 110000000, "latitude": 27.0, "longitude": 30.0, "selected": False},

        # --- Asia & Oceania ---
        {"id": "CHN", "name": "China", "economy": 92, "social": 55, "demography": 95, "technology": 90, "military_power": 92, "n_habitants": 1412914089, "latitude": 35.0, "longitude": 105.0, "selected": False},
        {"id": "RUS", "name": "Russia", "economy": 65, "social": 45, "demography": 55, "technology": 78, "military_power": 95, "n_habitants": 143453337, "latitude": 60.0, "longitude": 100.0, "selected": False},
        {"id": "IND", "name": "India", "economy": 75, "social": 50, "demography": 98, "technology": 82, "military_power": 88, "n_habitants": 1408000000, "latitude": 20.0, "longitude": 77.0, "selected": False},
        {"id": "JPN", "name": "Japan", "economy": 88, "social": 80, "demography": 35, "technology": 95, "military_power": 70, "n_habitants": 125700000, "latitude": 36.0, "longitude": 138.0, "selected": False},
        {"id": "KOR", "name": "Korea, Republic of", "economy": 82, "social": 75, "demography": 30, "technology": 96, "military_power": 80, "n_habitants": 51740000, "latitude": 37.0, "longitude": 127.5, "selected": False},
        {"id": "PRK", "name": "Korea, Democratic People's Republic of", "economy": 20, "social": 20, "demography": 55, "technology": 20, "military_power": 70, "n_habitants": 26000000, "latitude": 40.0, "longitude": 127.0, "selected": False},
        {"id": "IDN", "name": "Indonesia", "economy": 55, "social": 50, "demography": 80, "technology": 50, "military_power": 55, "n_habitants": 280000000, "latitude": -5.0, "longitude": 120.0, "selected": False},
        {"id": "PAK", "name": "Pakistan", "economy": 45, "social": 40, "demography": 75, "technology": 40, "military_power": 65, "n_habitants": 240000000, "latitude": 30.0, "longitude": 70.0, "selected": False},
        {"id": "BGD", "name": "Bangladesh", "economy": 40, "social": 45, "demography": 80, "technology": 35, "military_power": 35, "n_habitants": 170000000, "latitude": 24.0, "longitude": 90.0, "selected": False},
        {"id": "VNM", "name": "Viet Nam", "economy": 55, "social": 55, "demography": 65, "technology": 50, "military_power": 55, "n_habitants": 100000000, "latitude": 16.0, "longitude": 106.0, "selected": False},
        {"id": "THA", "name": "Thailand", "economy": 55, "social": 55, "demography": 55, "technology": 50, "military_power": 55, "n_habitants": 71000000, "latitude": 15.0, "longitude": 101.0, "selected": False},
        {"id": "PHL", "name": "Philippines", "economy": 50, "social": 50, "demography": 70, "technology": 45, "military_power": 40, "n_habitants": 115000000, "latitude": 13.0, "longitude": 122.0, "selected": False},
        {"id": "AUS", "name": "Australia", "economy": 78, "social": 88, "demography": 30, "technology": 84, "military_power": 65, "n_habitants": 25700000, "latitude": -25.0, "longitude": 133.0, "selected": False},
        {"id": "NZL", "name": "New Zealand", "economy": 70, "social": 85, "demography": 35, "technology": 75, "military_power": 30, "n_habitants": 5200000, "latitude": -41.0, "longitude": 174.0, "selected": False},

        # --- Africa ---
        {"id": "ZAF", "name": "South Africa", "economy": 55, "social": 40, "demography": 60, "technology": 60, "military_power": 55, "n_habitants": 60000000, "latitude": -29.0, "longitude": 24.0, "selected": False},
        {"id": "NGA", "name": "Nigeria", "economy": 50, "social": 35, "demography": 90, "technology": 40, "military_power": 55, "n_habitants": 230000000, "latitude": 10.0, "longitude": 8.0, "selected": False},
        {"id": "ETH", "name": "Ethiopia", "economy": 35, "social": 35, "demography": 85, "technology": 25, "military_power": 45, "n_habitants": 125000000, "latitude": 9.0, "longitude": 40.0, "selected": False},
        {"id": "KEN", "name": "Kenya", "economy": 40, "social": 40, "demography": 75, "technology": 35, "military_power": 35, "n_habitants": 55000000, "latitude": 1.0, "longitude": 38.0, "selected": False},
        {"id": "TZA", "name": "Tanzania, United Republic of", "economy": 35, "social": 40, "demography": 75, "technology": 25, "military_power": 30, "n_habitants": 65000000, "latitude": -6.0, "longitude": 35.0, "selected": False},
        {"id": "DZA", "name": "Algeria", "economy": 45, "social": 45, "demography": 60, "technology": 35, "military_power": 55, "n_habitants": 45000000, "latitude": 28.0, "longitude": 3.0, "selected": False},
        {"id": "MAR", "name": "Morocco", "economy": 45, "social": 45, "demography": 55, "technology": 40, "military_power": 45, "n_habitants": 37000000, "latitude": 32.0, "longitude": -6.0, "selected": False},
        {"id": "TUN", "name": "Tunisia", "economy": 40, "social": 45, "demography": 50, "technology": 40, "military_power": 30, "n_habitants": 12000000, "latitude": 34.0, "longitude": 9.0, "selected": False},
        {"id": "GHA", "name": "Ghana", "economy": 40, "social": 40, "demography": 70, "technology": 35, "military_power": 25, "n_habitants": 34000000, "latitude": 8.0, "longitude": -2.0, "selected": False},
        {"id": "CIV", "name": "Côte d'Ivoire", "economy": 40, "social": 35, "demography": 70, "technology": 30, "military_power": 25, "n_habitants": 29000000, "latitude": 8.0, "longitude": -5.0, "selected": False}
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

    # Load existing IDs
    country_ids = [c[0] for c in db.query(Country.id).all()]

    REL_MIN, REL_MAX = -100, 100
    K_PER_COUNTRY = 8

    # In case there are not enough countries
    if len(country_ids) < 2:
        db.close()
        raise RuntimeError("At least 2 countries needed to create relationships.")

    # Generate unique relationships
    for c1 in country_ids:
        candidates = [c for c in country_ids if c != c1]
        picks = random.sample(candidates, k=min(K_PER_COUNTRY, len(candidates)))

        for c2 in picks:
            a, b = sorted([c1, c2])

            rel = db.query(Relationship).filter(
                (Relationship.country_1 == a) & (Relationship.country_2 == b)
            ).first()

            if not rel:
                db.add(Relationship(
                    country_1=a,
                    country_2=b,
                    relation=random.randint(REL_MIN, REL_MAX)
                ))
            else:
                rel.relation = random.randint(REL_MIN, REL_MAX)

        db.commit()
        db.close()

if __name__ == "__main__":
    asyncio.run(seed())