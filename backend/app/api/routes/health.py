from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import engine

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "backend",
    }


@router.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT version(), PostGIS_Version();")
        )

        row = result.fetchone()

        return {
            "database": "connected",
            "postgresql": row[0],
            "postgis": row[1],
        }