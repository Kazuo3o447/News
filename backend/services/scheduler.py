"""
Pipeline: RSS-Fetch → Groq-Klassifizierung → Cosmos DB Upsert
Wird durch APScheduler alle N Minuten ausgeführt.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from api.models.article import Article
from config.settings import settings
from services.cosmos_service import delete_articles_older_than, get_known_ids, upsert_many
from services.groq_classifier import classify_article
from services.pre_filter import pre_filter
from services.rss_fetcher import fetch_all_feeds

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


# ---------------------------------------------------------------------------
# Pipeline-Job
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    """
    Haupt-Pipeline:
    1. Alle RSS-Feeds abrufen
    2. Bereits bekannte Artikel (Duplikate) überspringen
    3. Neue Artikel via Groq klassifizieren
    4. In Cosmos DB speichern
    """
    logger.info("Pipeline gestartet …")

    raw_articles = fetch_all_feeds()
    if not raw_articles:
        logger.warning("Pipeline: Keine Artikel von Feeds erhalten.")
        return

    known_ids = get_known_ids()
    new_raw   = [a for a in raw_articles if a["id"] not in known_ids]
    logger.info("Pipeline: %d gesamt, %d neu (davon %d bekannt)",
                len(raw_articles), len(new_raw), len(raw_articles) - len(new_raw))

    if not new_raw:
        logger.info("Pipeline: Nichts Neues. Abgeschlossen.")
        return

    # Klassifizieren — jeder neue Artikel läuft durch Groq.
    # Throttling für Groq Free Tier llama-3.1-8b-instant:
    #   RPM=30  → 2 s/Request würde RPM einhalten
    #   TPM=6K  → effektiv begrenzt durch Tokens, ~10 RPM machbar (System-Prompt ~250
    #             + User ~200 + Antwort ~100 = 550 Tokens, 6000/550 ≈ 11 Req/Min)
    # Konservativ: 6 s Pause = max. 10 RPM = ~5500 TPM (sicher unter Limit).
    THROTTLE_SECONDS = 6.0 if settings.GROQ_API_KEY else 0.0
    BATCH_SIZE       = 10            # zwischenzeitlich persistieren, damit das Frontend früh sieht
    articles: list[Article] = []
    off_topic_signals = 0
    pending_groq      = 0
    total_ok          = 0
    total_err         = 0

    def _flush_batch() -> None:
        nonlocal articles, total_ok, total_err
        if not articles:
            return
        ok, err = upsert_many(articles)
        total_ok  += ok
        total_err += err
        articles = []

    for raw in new_raw:
        pre = pre_filter(raw["title"], raw.get("summary", ""))

        if pre["off_topic"]:
            off_topic_signals += 1

        clf = classify_article(
            title=raw["title"],
            source=raw["source"],
            summary=raw.get("summary", ""),
        )
        articles.append(Article(
            **{k: v for k, v in raw.items() if k not in ("category", "confidence", "reason")},
            category=clf["category"],
            confidence=clf["confidence"],
            classification_reason=clf["reason"],
            topics=pre["topics"],
        ))
        pending_groq += 1
        if len(articles) >= BATCH_SIZE:
            _flush_batch()
        if THROTTLE_SECONDS and pending_groq < len(new_raw):
            time.sleep(THROTTLE_SECONDS)

    _flush_batch()
    logger.info("Pre-Filter: %d off-topic Signale, %d an Groq", off_topic_signals, pending_groq)
    logger.info("Pipeline abgeschlossen: %d gespeichert, %d Fehler.", total_ok, total_err)
    run_cleanup()


def run_cleanup() -> None:
    """Löscht Artikel außerhalb des konfigurierten Retention-Fensters."""
    retention_days = max(1, settings.ARTICLE_RETENTION_DAYS)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat()
    deleted = delete_articles_older_than(cutoff_iso)
    logger.info(
        "Cleanup abgeschlossen: %d Artikel gelöscht (Retention: %d Tage, cutoff=%s)",
        deleted,
        retention_days,
        cutoff_iso,
    )


# ---------------------------------------------------------------------------
# Scheduler-Lifecycle (von main.py aufgerufen)
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(minutes=settings.FEED_REFRESH_INTERVAL_MINUTES),
        id="rss_pipeline",
        replace_existing=True,
        max_instances=1,          # Kein paralleles Ausführen
    )
    _scheduler.add_job(
        run_cleanup,
        trigger=IntervalTrigger(hours=max(1, settings.ARTICLE_CLEANUP_INTERVAL_HOURS)),
        id="rss_cleanup",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        "Scheduler gestartet — Intervall: %d Minuten.",
        settings.FEED_REFRESH_INTERVAL_MINUTES,
    )
    # Initial-Run nicht synchron (sonst blockiert FastAPI-Lifespan und der
    # HTTP-Socket wird nie gebunden). Stattdessen über den Scheduler-Thread
    # in 2 Sekunden starten.
    _scheduler.add_job(
        run_pipeline,
        trigger="date",
        run_date=datetime.utcnow() + timedelta(seconds=2),
        id="rss_pipeline_initial",
        replace_existing=True,
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler gestoppt.")
