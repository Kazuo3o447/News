"""
News API-Endpunkte
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request

from api.models.article import Article
from config.feeds import FEEDS
from config.settings import settings
from services import cosmos_service, feed_health
from services.identity import current_user
from services.scheduler import run_pipeline, reclassify_stale
from services.topics import PLATFORMS, TOPICS

router = APIRouter(tags=["news"])

_VALID_CATEGORIES = {"KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC", "PENDING"}
_VALID_PLATFORMS  = {"windows", "apple", "android", "cross"}
_VALID_VIEWS      = {"all", "unread", "critical"}


def _is_priority(article: Article) -> bool:
    """B3: Abgeleitetes Flag — True für Windows/Microsoft und cross-Security."""
    if article.platform == "windows":
        return True
    if "microsoft" in (article.topics or []):
        return True
    return False


@router.get("/news", response_model=dict)
async def get_news(
    request: Request,
    # legacy filter (kept for backwards compat)
    category: Literal["KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC", "PENDING"] | None = Query(default=None),
    # B1 new params
    view:      str | None = Query(default="all",  description="all | unread | critical"),
    platform:  Literal["windows", "apple", "android", "cross"] | None = Query(default=None),
    q:         str | None = Query(default=None,   description="Freitext in Titel/Summary/Quelle"),
    topic:     str | None = Query(default=None,   description="Topic-Key"),
    source:    str | None = Query(default=None,   description="Quellenname"),
    since:     str | None = Query(default=None,   description="ISO-8601: nur Artikel neuer als"),
    page:      int        = Query(default=1, ge=1),
    page_size: int        = Query(default=30, ge=1, le=60),
    collapse:  bool       = Query(default=True,   description="Pro cluster_id nur Repräsentant"),
):
    """
    Gibt paginierte, server-seitig gefilterte und sortierte Artikel zurück.
    Sortierung: KRITISCH zuerst (höchster CVSS), dann published_at DESC.
    """
    if view and view not in _VALID_VIEWS:
        raise HTTPException(status_code=422, detail=f"Ungültiger view-Wert: {view!r}")
    if category is not None and category not in _VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Ungültige Kategorie")
    if platform is not None and platform not in _VALID_PLATFORMS:
        raise HTTPException(status_code=422, detail="Ungültige Plattform")

    # view=critical setzt implizit category
    if view == "critical":
        category = "KRITISCH"

    user = current_user(request)

    from services import read_state
    articles, total = cosmos_service.get_articles(
        category=category,
        platform=platform,
        page=page,
        page_size=page_size,
        collapse=collapse,
        view=view,
        q=q,
        topic=topic,
        source=source,
        since=since,
        user=user,
        read_map_fn=read_state.read_map,
    )

    # B2 — read_by / is_read Anreicherung
    ids  = [a.id for a in articles]
    rmap = read_state.read_map(ids)

    items_out = []
    for a in articles:
        d = a.model_dump()
        d["read_by"] = rmap.get(a.id, [])
        d["is_read"] = user in d["read_by"]
        d["is_priority"] = _is_priority(a)   # B3
        items_out.append(d)

    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "view":      view or "all",
        "collapse":  collapse,
        "items":     items_out,
    }


@router.get("/news/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """Gibt einen einzelnen Artikel nach ID zurück."""
    article = cosmos_service.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return article


# ---------------------------------------------------------------------------
# B2 — Team Read-State Endpunkte
# ---------------------------------------------------------------------------

@router.post("/articles/{article_id}/read", status_code=204)
async def mark_article_read(article_id: str, request: Request):
    """Markiert Artikel als gelesen für den aktuellen User."""
    from services import read_state
    read_state.mark_read(article_id, current_user(request))


@router.delete("/articles/{article_id}/read", status_code=204)
async def mark_article_unread(article_id: str, request: Request):
    """Entfernt Gelesen-Markierung für den aktuellen User."""
    from services import read_state
    read_state.mark_unread(article_id, current_user(request))


@router.post("/articles/read/bulk", status_code=204)
async def mark_articles_read_bulk(body: dict, request: Request):
    """Markiert mehrere Artikel als gelesen. Body: { 'ids': ['id1', 'id2', ...] }"""
    ids = body.get("ids", [])
    if not isinstance(ids, list):
        raise HTTPException(status_code=422, detail="'ids' muss eine Liste sein")
    ids = [str(i) for i in ids[:500]]  # max 500 auf einmal
    from services import read_state
    read_state.mark_read_bulk(ids, current_user(request))


# ---------------------------------------------------------------------------
# Refresh / Reklassifizierung
# ---------------------------------------------------------------------------

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
