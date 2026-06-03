"""
News API-Endpunkte
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query

from api.models.article import Article
from config.feeds import FEEDS
from config.settings import settings
from services import cosmos_service, feed_health
from services.scheduler import run_pipeline, reclassify_stale
from services.topics import PLATFORMS, TOPICS

router = APIRouter(tags=["news"])

_VALID_CATEGORIES = {"KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC", "PENDING"}
_VALID_PLATFORMS  = {"windows", "apple", "android", "cross"}


@router.get("/news", response_model=dict)
async def get_news(
    category: Literal["KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC", "PENDING"] | None = Query(default=None),
    platform: Literal["windows", "apple", "android", "cross"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    collapse: bool = Query(default=True, description="Pro cluster_id nur den Repräsentanten zurückgeben"),
):
    """Gibt paginierte Artikel zurück, optional gefiltert nach Kategorie und/oder Plattform."""
    if category is not None and category not in _VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Ungültige Kategorie")
    if platform is not None and platform not in _VALID_PLATFORMS:
        raise HTTPException(status_code=422, detail="Ungültige Plattform")

    articles, total = cosmos_service.get_articles(
        category=category, platform=platform, page=page, page_size=page_size, collapse=collapse
    )
    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "collapse":  collapse,
        "items":     [a.model_dump() for a in articles],
    }


@router.get("/news/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """Gibt einen einzelnen Artikel nach ID zurück."""
    article = cosmos_service.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return article


@router.post("/refresh", status_code=202)
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    x_refresh_secret: str | None = Header(default=None),
):
    """Löst manuell einen Feed-Refresh aus (läuft im Hintergrund)."""
    if settings.REFRESH_SECRET and x_refresh_secret != settings.REFRESH_SECRET:
        raise HTTPException(status_code=401, detail="Ungültiges oder fehlendes X-Refresh-Secret")
    background_tasks.add_task(run_pipeline)
    return {"message": "Feed-Refresh gestartet"}


@router.post("/reclassify", status_code=202)
async def trigger_reclassify(
    background_tasks: BackgroundTasks,
    stale: bool = Query(default=False, description="Artikel mit veralteter prompt_version neu klassifizieren"),
    x_refresh_secret: str | None = Header(default=None),
):
    """
    Reklassifiziert PENDING-Artikel oder (stale=true) alle Artikel mit veralteter prompt_version.
    Muss mit X-Refresh-Secret abgesichert sein, wenn REFRESH_SECRET konfiguriert ist.
    """
    if settings.REFRESH_SECRET and x_refresh_secret != settings.REFRESH_SECRET:
        raise HTTPException(status_code=401, detail="Ungültiges oder fehlendes X-Refresh-Secret")
    if stale:
        background_tasks.add_task(reclassify_stale)
        return {"message": "Stale-Reklassifizierung gestartet", "prompt_version": settings.PROMPT_VERSION}
    from services.scheduler import reclassify_pending
    background_tasks.add_task(reclassify_pending)
    return {"message": "PENDING-Reklassifizierung gestartet"}


@router.get("/feeds")
async def get_feeds():
    """Gibt die Liste der konfigurierten RSS-Feeds zurück."""
    return {"total": len(FEEDS), "feeds": FEEDS}


@router.get("/feeds/health")
async def get_feeds_health():
    """Gibt den Gesundheitszustand aller bekannten Feed-Quellen zurück."""
    return {"health": feed_health.get_health()}


@router.get("/topics")
async def get_topics():
    """Gibt alle konfigurierten Topics (key + label, keine Keywords) zurück."""
    return {"topics": [{"key": t["key"], "label": t["label"]} for t in TOPICS]}


@router.get("/platforms")
async def get_platforms():
    """Gibt alle Plattform-Werte (key + label) zurück."""
    return {"platforms": PLATFORMS}
