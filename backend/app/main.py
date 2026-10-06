from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.resources import router as resources_router
from app.api.routes.ai import router as ai_router
from app.db.database import Base, engine
from app.db import models


app = FastAPI(
    title="Emergency Intelligence & Response API",
    description="Backend API for the Emergency Intelligence & Response system.",
    version="0.1.0",
)


Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    incidents_router,
    prefix="/api",
)

app.include_router(
    resources_router,
    prefix="/api",
)

app.include_router(
    ai_router,
    prefix="/api",
)