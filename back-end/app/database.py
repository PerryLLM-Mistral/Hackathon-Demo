import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get the DATABASE_URL from env
SQLALCHEMY_DATABASE_URL = os.environ.get("POSTGRES_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("POSTGRES_URL is not set in env variables")

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the database models
Base = declarative_base()

# Dependency to get the DB session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()