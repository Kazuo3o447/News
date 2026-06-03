"""
IT News Hub — FastAPI Backend
Entry point for Azure App Service
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, news
from config.settings import settings
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Scheduler + initialer Feed-Fetch
    start_scheduler()
    yield
    # Shutdown: sauber beenden
    stop_scheduler()


app = FastAPI(
    title="IT News Hub API",
    version="0.1.0",
    description="RSS-Aggregator mit Groq KI-Klassifizierung",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(news.router,   prefix="/api")
