"""
News API-Endpunkte
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from api.models.article import Article
from config.feeds import FEEDS
from services import cosmos_service
from services.scheduler import run_pipeline

router = APIRouter(tags=["news"])


@router.get("/news", response_model=dict)
async def get_news(
    category: Literal["KRITISCH", "NORMAL", "DUMP"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
):
    """Gibt paginierte Artikel zurück, optional gefiltert nach Kategorie."""
    articles, total = cosmos_service.get_articles(
        category=category, page=page, page_size=page_size
    )
    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
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
async def trigger_refresh(background_tasks: BackgroundTasks):
    """
    Löst manuell einen Feed-Refresh aus (läuft im Hintergrund).
    Gibt sofort 202 Accepted zurück.
    """
    background_tasks.add_task(run_pipeline)
    return {"message": "Feed-Refresh gestartet"}


@router.get("/feeds")
async def get_feeds():
    """Gibt die Liste der konfigurierten RSS-Feeds zurück."""
    return {"total": len(FEEDS), "feeds": FEEDS}
