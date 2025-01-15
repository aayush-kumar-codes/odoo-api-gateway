from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import Base, engine

app = FastAPI(
    title="Odoo API Gateway",
    description="FastAPI based API Gateway for Odoo",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Welcome to the E-commerce API Gateway"} 