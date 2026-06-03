"""
Pipeline: RSS-Fetch → Pre-Filter → Regelschicht → Groq-Batch → Merge → Cosmos DB Upsert
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
from services.android_scraper import scrape_android_bulletin, scrape_samsung_smr
from services.cosmos_service import delete_articles_older_than, get_known_ids, upsert_many
from services.groq_classifier import classify_batch
from services.pre_filter import pre_filter
from services.rule_classifier import apply_rules
from services.rss_fetcher import fetch_all_feeds
from services.topics import detect_topics

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

# Pause zwischen Groq-Batches (nicht pro Artikel!) -- Batching entlastet RPM stark
THROTTLE_SECONDS = 1.0
# Artikel pro Groq-Request (10-15 lt. Brief)
GROQ_CHUNK_SIZE  = 12
# Zwischenzeitlich an Cosmos persistieren (damit Frontend fruh sieht)
PERSIST_BATCH    = 10


# ---------------------------------------------------------------------------
# Pipeline-Job
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    logger.info("Pipeline gestartet ...")

    raw_articles = fetch_all_feeds()
    if not raw_articles:
        logger.warning("Pipeline: Keine Artikel von Feeds erhalten.")
        return

    known_ids = get_known_ids()
    new_raw   = [a for a in raw_articles if a["id"] not in known_ids]
    logger.info("Pipeline: %d gesamt, %d neu", len(raw_articles), len(new_raw))

    if not new_raw:
        logger.info("Pipeline: Nichts Neues. Abgeschlossen.")
        return

    articles:     list[Article] = []
    to_classify:  list[dict]    = []
    rule_data:    dict[str, dict] = {}
    total_ok      = 0
    total_err     = 0
    off_topic_count = 0

    def _flush() -> None:
        nonlocal articles, total_ok, total_err
        if not articles:
            return
        ok, err = upsert_many(articles)
        total_ok  += ok
        total_err += err
        articles = []

    for raw in new_raw:
        title   = raw["title"]
        summary = raw.get("summary", "")
        source  = raw.get("source", "")

        pf = pre_filter(title, summary)

        if pf["off_topic"]:
            off_topic_count += 1
            rules    = apply_rules(title, summary, source)
            platform = rules.get("platform_hint") or settings.DEFAULT_PLATFORM
            articles.append(Article(
                **{k: v for k, v in raw.items() if k not in ("category", "platform")},
                category="OFF_TOPIC",
                platform=platform,
                confidence=None,
                classification_reason=pf["reason"],
                tags=[],
                topics=pf["topics"],
            ))
            if len(articles) >= PERSIST_BATCH:
                _flush()
            continue

        rules = apply_rules(title, summary, source)
        rule_data[raw["id"]] = rules
        to_classify.append(raw)

    chunks = [
        to_classify[i: i + GROQ_CHUNK_SIZE]
        for i in range(0, len(to_classify), GROQ_CHUNK_SIZE)
    ]
    logger.info(
        "Pipeline: %d off_topic, %d zur Klassifizierung (%d Batches, chunk=%d)",
        off_topic_count, len(to_classify), len(chunks), GROQ_CHUNK_SIZE,
    )

    classified: dict[str, dict] = {}

    for chunk_idx, chunk in enumerate(chunks):
        batch_items = [
            {
                "idx":     i,
                "title":   a["title"],
                "source":  a.get("source", ""),
                "summary": a.get("summary", ""),
            }
            for i, a in enumerate(chunk)
        ]
        results = classify_batch(batch_items)
        for res, raw in zip(results, chunk):
            classified[raw["id"]] = res

        if THROTTLE_SECONDS and settings.GROQ_API_KEY and chunk_idx < len(chunks) - 1:
            time.sleep(THROTTLE_SECONDS)

    forced_critical_count = 0

    for raw in to_classify:
        llm   = classified.get(raw["id"], {})
        rules = rule_data.get(raw["id"], {})

        forced_critical = rules.get("forced_critical", False)
        platform_hint   = rules.get("platform_hint")

        if forced_critical:
            forced_critical_count += 1

        category = "KRITISCH" if forced_critical else llm.get("criticality", "NORMAL")
        platform = llm.get("platform") or platform_hint or settings.DEFAULT_PLATFORM
        tags     = llm.get("tags", [])

        if forced_critical:
            confidence = 1.0
        elif platform_hint and platform_hint == llm.get("platform"):
            confidence = 0.9
        else:
            confidence = 0.6

        articles.append(Article(
            **{k: v for k, v in raw.items() if k not in ("category", "platform")},
            category=category,
            platform=platform,
            confidence=confidence,
            classification_reason=llm.get("reason", ""),
            tags=tags,
            topics=detect_topics(raw["title"], raw.get("summary", "")),
        ))
        if len(articles) >= PERSIST_BATCH:
            _flush()

    _flush()

    logger.info(
        "Pipeline abgeschlossen: off_topic=%d, batches=%d, forced_critical=%d, gespeichert=%d, fehler=%d",
        off_topic_count, len(chunks), forced_critical_count, total_ok, total_err,
    )
    run_cleanup()


def run_cleanup() -> None:
    retention_days = max(1, settings.ARTICLE_RETENTION_DAYS)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff.isoformat()
    deleted = delete_articles_older_than(cutoff_iso)
    logger.info(
        "Cleanup abgeschlossen: %d Artikel geloscht (Retention: %d Tage, cutoff=%s)",
        deleted, retention_days, cutoff_iso,
    )


def _run_android_scraper() -> None:
    logger.info("Android-Scraper gestartet ...")
    raw_articles = scrape_android_bulletin() + scrape_samsung_smr()
    if not raw_articles:
        logger.info("Android-Scraper: Keine neuen Eintrage.")
        return

    known_ids = get_known_ids()
    new_raw   = [a for a in raw_articles if a["id"] not in known_ids]
    if not new_raw:
        logger.info("Android-Scraper: Alle Eintrage bereits bekannt.")
        return

    batch_items = [
        {"idx": i, "title": a["title"], "source": a.get("source", ""), "summary": a.get("summary", "")}
        for i, a in enumerate(new_raw)
    ]
    results = classify_batch(batch_items)

    articles = []
    for res, raw in zip(results, new_raw):
        rules           = apply_rules(raw["title"], raw.get("summary", ""), raw.get("source", ""))
        forced_critical = rules.get("forced_critical", False)
        platform_hint   = rules.get("platform_hint") or raw.get("platform", settings.DEFAULT_PLATFORM)

        category   = "KRITISCH" if forced_critical else res.get("criticality", "NORMAL")
        platform   = res.get("platform") or platform_hint
        confidence = 1.0 if forced_critical else (0.9 if platform_hint == res.get("platform") else 0.6)

        articles.append(Article(
            **{k: v for k, v in raw.items() if k not in ("category", "platform")},
            category=category,
            platform=platform,
            confidence=confidence,
            classification_reason=res.get("reason", ""),
            tags=res.get("tags", []),
            topics=detect_topics(raw["title"], raw.get("summary", "")),
        ))

    ok, err = upsert_many(articles)
    logger.info("Android-Scraper abgeschlossen: %d gespeichert, %d Fehler.", ok, err)


# ---------------------------------------------------------------------------
# Scheduler-Lifecycle
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(minutes=settings.FEED_REFRESH_INTERVAL_MINUTES),
        id="rss_pipeline",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        run_cleanup,
        trigger=IntervalTrigger(hours=max(1, settings.ARTICLE_CLEANUP_INTERVAL_HOURS)),
        id="rss_cleanup",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        _run_android_scraper,
        trigger="cron",
        day_of_week="mon",
        hour=6,
        minute=0,
        id="android_scraper",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info("Scheduler gestartet -- Intervall: %d Minuten.", settings.FEED_REFRESH_INTERVAL_MINUTES)
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
