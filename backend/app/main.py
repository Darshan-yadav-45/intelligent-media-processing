"""
FastAPI application entrypoint.
Run locally with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import get_settings
from app.logging_config import configure_logging
from app.database import init_db
from app.rate_limit import limiter
from app.api import auth, images, analytics, health

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Intelligent Media Processing Pipeline",
    description="Backend + AI Engineering assignment: async image analysis pipeline",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(images.router)
app.include_router(analytics.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"service": "Intelligent Media Processing Pipeline", "docs": "/docs"}
