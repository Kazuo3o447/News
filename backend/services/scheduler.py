"""
Pipeline: RSS-Fetch -> Pre-Filter -> Regelschicht -> Groq-Batch -> Merge -> Dedup -> Cosmos DB Upsert
Wird durch APScheduler alle N Minuten ausgefuhrt.
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
from services.vendor_scraper import scrape_apple_security
from services.cosmos_service import (
    delete_articles_older_than,
    get_articles,
    get_known_ids,
    get_pending_articles,
    get_stale_articles,
    upsert_many,
)
from services.dedup import cluster_key
from services.groq_classifier import classify_batch
from services.notifier import notify_critical
from services.pre_filter import pre_filter
from services.rule_classifier import apply_rules
from services.rss_fetcher import fetch_all_feeds
from services.topics import detect_topics

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

THROTTLE_SECONDS = 1.0
GROQ_CHUNK_SIZE  = 12
PERSIST_BATCH    = 10


# ---------------------------------------------------------------------------
# Merge-Hilfsfunktion
# ---------------------------------------------------------------------------

def _merge_article(raw: dict, llm: dict, rules: dict, recent: list[Article]) -> Article:
    """Baut aus raw-dict + LLM-Ergebnis + Regelschicht einen Article zusammen."""
    forced_critical = rules.get("forced_critical", False)
    platform_hint   = rules.get("platform_hint")

    llm_criticality = llm.get("criticality", "PENDING")
    # PENDING-Fallback vom LLM nicht als endgultige Kategorie behandeln
    if llm_criticality == "PENDING":
        category   = "PENDING"
        confidence = None
    elif forced_critical:
        category   = "KRITISCH"
        confidence = 1.0
    else:
        category = llm_criticality
        if platform_hint and platform_hint == llm.get("platform"):
            confidence = 0.9
        else:
            confidence = 0.6

    platform = llm.get("platform") or platform_hint or settings.DEFAULT_PLATFORM

    article = Article(
        **{k: v for k, v in raw.items() if k not in ("category", "platform", "confidence", "reason")},
        category=category,
        platform=platform,
        confidence=confidence,
        classification_reason=llm.get("reason", ""),
        tags=llm.get("tags", []),
        topics=detect_topics(raw["title"], raw.get("summary", "")),
        cve_ids=rules.get("cve_ids", []),
        cvss=rules.get("cvss"),
        prompt_version=settings.PROMPT_VERSION if category != "PENDING" else "",
        tldr=llm.get("tldr", ""),
    )
    article.cluster_id = cluster_key(article, recent)
    return article


# ---------------------------------------------------------------------------
# Pipeline-Job
# ---------------------------------------------------------------------------

def run_pipeline(priority_filter: set[str] | None = None) -> None:
    """
    B3: priority_filter steuert welche Feeds gefetcht werden.
    None = alle (Fallback/manueller Aufruf).
    """
    label = f"priority={priority_filter}" if priority_filter else "alle"
    logger.info("Pipeline gestartet (%s) ...", label)

    raw_articles = fetch_all_feeds(priorities=priority_filter)
    if not raw_articles:
        logger.warning("Pipeline: Keine Artikel von Feeds erhalten.")
        return

    known_ids = get_known_ids()
    new_raw   = [a for a in raw_articles if a["id"] not in known_ids]
    logger.info("Pipeline: %d gesamt, %d neu", len(raw_articles), len(new_raw))

    if not new_raw:
        logger.info("Pipeline: Nichts Neues. Abgeschlossen.")
        return

    # Letzte Artikel fur Cluster-Dedup laden (max 200 aus dem Speicher)
    recent_articles, _ = get_articles(page_size=200)

    articles:     list[Article] = []
    to_classify:  list[dict]    = []
    rule_data:    dict[str, dict] = {}
    total_ok      = 0
    total_err     = 0
    off_topic_count = 0
    new_kritisch: list[Article] = []

    def _flush(final: bool = False) -> None:
        nonlocal articles, total_ok, total_err, new_kritisch
        if not articles:
            return
        ok, err = upsert_many(articles)
        total_ok  += ok
        total_err += err
        new_kritisch.extend(a for a in articles if a.category == "KRITISCH")
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
            a = Article(
                **{k: v for k, v in raw.items() if k not in ("category", "platform", "confidence", "reason")},
                category="OFF_TOPIC",
                platform=platform,
                confidence=None,
                classification_reason=pf["reason"],
                tags=[],
                topics=pf["topics"],
                cve_ids=[],
                cvss=None,
                prompt_version=settings.PROMPT_VERSION,
            )
            a.cluster_id = cluster_key(a, recent_articles)
            articles.append(a)
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
        if rules.get("forced_critical"):
            forced_critical_count += 1

        article = _merge_article(raw, llm, rules, recent_articles)
        articles.append(article)
        if len(articles) >= PERSIST_BATCH:
            _flush()

    _flush()

    logger.info(
        "Pipeline abgeschlossen: off_topic=%d, batches=%d, forced_critical=%d, ok=%d, err=%d",
        off_topic_count, len(chunks), forced_critical_count, total_ok, total_err,
    )

    # B5: TL;DR für KRITISCH-Artikel generieren, dann re-persist
    if new_kritisch and settings.ENABLE_CRITICAL_TLDR:
        from services.groq_classifier import summarize_critical
        tldr_map = summarize_critical(new_kritisch)
        if tldr_map:
            for a in new_kritisch:
                if a.id in tldr_map and tldr_map[a.id]:
                    a.tldr = tldr_map[a.id]
            upsert_many(new_kritisch)
            logger.info("B5: %d KRITISCH-TL;DRs persistiert.", len(tldr_map))

    # Teams-Push fur neu klassifizierte KRITISCH-Artikel
    if new_kritisch:
        notify_critical(new_kritisch)

    # PENDING-Retry-Sweep (max 1 Batch pro Lauf)
    reclassify_pending()

    run_cleanup()


# ---------------------------------------------------------------------------
# PENDING-Retry
# ---------------------------------------------------------------------------

def reclassify_pending(max_items: int = GROQ_CHUNK_SIZE) -> None:
    """Holt PENDING-Artikel und versucht, sie erneut zu klassifizieren (max 1 Batch)."""
    pending = get_pending_articles(limit=max_items)
    if not pending:
        return

    logger.info("reclassify_pending: %d PENDING-Artikel werden erneut klassifiziert", len(pending))
    recent_articles, _ = get_articles(page_size=200)

    batch_items = [
        {"idx": i, "title": a.title, "source": a.source, "summary": a.summary}
        for i, a in enumerate(pending)
    ]
    results = classify_batch(batch_items)

    updated: list[Article] = []
    for res, article in zip(results, pending):
        if res.get("criticality") in ("PENDING", None):
            continue  # noch nicht klassifizierbar - nicht uberschreiben
        raw = article.model_dump()
        rules = apply_rules(article.title, article.summary, article.source)
        merged = _merge_article(raw, res, rules, recent_articles)
        updated.append(merged)

    if updated:
        ok, err = upsert_many(updated)
        logger.info("reclassify_pending: %d aktualisiert, %d Fehler", ok, err)


# ---------------------------------------------------------------------------
# Stale-Reklassifizierung (POST /api/reclassify?stale=true)
# ---------------------------------------------------------------------------

def reclassify_stale() -> dict:
    """
    Reklassifiziert alle Artikel, deren prompt_version != settings.PROMPT_VERSION.
    Gibt eine Zusammenfassung zuruck.
    """
    stale = get_stale_articles(settings.PROMPT_VERSION, limit=500)
    if not stale:
        return {"reclassified": 0, "prompt_version": settings.PROMPT_VERSION}

    logger.info("reclassify_stale: %d veraltete Artikel werden nachgezogen", len(stale))
    recent_articles, _ = get_articles(page_size=200)

    total_ok = total_err = 0
    chunks = [stale[i: i + GROQ_CHUNK_SIZE] for i in range(0, len(stale), GROQ_CHUNK_SIZE)]

    for chunk_idx, chunk in enumerate(chunks):
        batch_items = [
            {"idx": i, "title": a.title, "source": a.source, "summary": a.summary}
            for i, a in enumerate(chunk)
        ]
        results = classify_batch(batch_items)
        updated: list[Article] = []
        for res, article in zip(results, chunk):
            if res.get("criticality") in ("PENDING", None):
                continue
            raw   = article.model_dump()
            rules = apply_rules(article.title, article.summary, article.source)
            updated.append(_merge_article(raw, res, rules, recent_articles))

        ok, err = upsert_many(updated)
        total_ok  += ok
        total_err += err

        if THROTTLE_SECONDS and settings.GROQ_API_KEY and chunk_idx < len(chunks) - 1:
            time.sleep(THROTTLE_SECONDS)

    return {
        "reclassified": total_ok,
        "errors":       total_err,
        "prompt_version": settings.PROMPT_VERSION,
    }


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def run_cleanup() -> None:
    retention_days = max(1, settings.ARTICLE_RETENTION_DAYS)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = delete_articles_older_than(cutoff.isoformat())
    logger.info(
        "Cleanup: %d Artikel geloscht (Retention: %d Tage)",
        deleted, retention_days,
    )


# ---------------------------------------------------------------------------
# Android-Scraper
# ---------------------------------------------------------------------------

def _run_android_scraper() -> None:
    logger.info("Android-Scraper gestartet ...")
    raw_articles = scrape_android_bulletin() + scrape_samsung_smr()
    if not raw_articles:
        logger.info("Android-Scraper: Keine neuen Eintrge.")
        return

    known_ids = get_known_ids()
    new_raw   = [a for a in raw_articles if a["id"] not in known_ids]
    if not new_raw:
        logger.info("Android-Scraper: Alle Eintrge bereits bekannt.")
        return

    recent_articles, _ = get_articles(page_size=200)
    batch_items = [
        {"idx": i, "title": a["title"], "source": a.get("source", ""), "summary": a.get("summary", "")}
        for i, a in enumerate(new_raw)
    ]
    results = classify_batch(batch_items)
    articles: list[Article] = []
    for res, raw in zip(results, new_raw):
        rules = apply_rules(raw["title"], raw.get("summary", ""), raw.get("source", ""))
        articles.append(_merge_article(raw, res, rules, recent_articles))

    upsert_many(articles)
    logger.info("Android-Scraper: %d Artikel gespeichert.", len(articles))


# ---------------------------------------------------------------------------
# Apple-Scraper (täglich)
# ---------------------------------------------------------------------------

def _run_apple_scraper() -> None:
    logger.info("Apple-Scraper gestartet ...")
    raw_articles = scrape_apple_security()
    if not raw_articles:
        logger.info("Apple-Scraper: Keine neuen Einträge.")
        return

    known_ids = get_known_ids()
    new_raw   = [a for a in raw_articles if a["id"] not in known_ids]
    if not new_raw:
        logger.info("Apple-Scraper: Alle Einträge bereits bekannt.")
        return

    recent_articles, _ = get_articles(page_size=200)
    batch_items = [
        {"idx": i, "title": a["title"], "source": a.get("source", ""), "summary": a.get("summary", "")}
        for i, a in enumerate(new_raw)
    ]
    results = classify_batch(batch_items)
    articles: list[Article] = []
    for res, raw in zip(results, new_raw):
        rules = apply_rules(raw["title"], raw.get("summary", ""), raw.get("source", ""))
        articles.append(_merge_article(raw, res, rules, recent_articles))

    upsert_many(articles)
    logger.info("Apple-Scraper: %d Artikel gespeichert.", len(articles))


# ---------------------------------------------------------------------------
# APScheduler
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    global _scheduler
    # B7: scale-safe guard — nur starten wenn RUN_SCHEDULER=true
    if not settings.RUN_SCHEDULER:
        logger.info("Scheduler deaktiviert (RUN_SCHEDULER=false). Bei Scale-out nur eine Instanz aktivieren.")
        return

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()

    # B3: Tiered Polling — high=10 min, medium=30 min, low=60 min
    _scheduler.add_job(
        lambda: run_pipeline(priority_filter={"high"}),
        trigger=IntervalTrigger(minutes=10),
        id="pipeline_high",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        lambda: run_pipeline(priority_filter={"medium"}),
        trigger=IntervalTrigger(minutes=30),
        id="pipeline_medium",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        lambda: run_pipeline(priority_filter={"low"}),
        trigger=IntervalTrigger(minutes=60),
        id="pipeline_low",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.add_job(
        _run_android_scraper,
        trigger="cron",
        day_of_week="mon",
        hour=6,
        id="android_scraper",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.add_job(
        _run_apple_scraper,
        trigger="cron",
        hour=7,
        id="apple_scraper",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info(
        "Scheduler gestartet (high=10 min, medium=30 min, low=60 min; "
        "Android-Scraper montags 06:00 UTC, Apple-Scraper täglich 07:00 UTC)"
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler gestoppt.")
