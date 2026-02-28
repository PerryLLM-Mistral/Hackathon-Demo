# app/main.py
from fastapi import FastAPI
from app.src.routes.countries import router as countries_router
from app.src.routes.relationships import router as relationships_router

app = FastAPI()

app.include_router(countries_router)
app.include_router(relationships_router)