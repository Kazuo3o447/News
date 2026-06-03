"""
RSS Feed-Fetcher: Liest alle konfigurierten Feeds und gibt normalisierte Artikel zurück.
"""
import hashlib
import html
import logging
import re
from datetime import datetime, timezone

import feedparser

from config.feeds import FEEDS
from config.settings import settings
from services import feed_health

logger = logging.getLogger(__name__)

# HTML-Tag-Muster zum Strippen
_RE_TAGS = re.compile(r"<[^>]+>")
# Mehrfach-Whitespace kollabieren
_RE_WS   = re.compile(r"\s+")


def clean_summary(raw: str, max_len: int = 500) -> str:
    """Entfernt HTML-Tags und -Entities, kollabiert Whitespace, kürzt auf max_len."""
    text = _RE_TAGS.sub(" ", raw or "")
    text = html.unescape(text)
    text = _RE_WS.sub(" ", text).strip()
    return text[:max_len]


def _parse_date(entry) -> str:
    """Extrahiert ISO-8601-Datum aus einem feedparser-Entry; Fallback: jetzt (UTC)."""
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def fetch_feed(feed_cfg: dict) -> list[dict]:
    """Fetcht einen einzelnen Feed und gibt rohe Artikel-Dicts zurück."""
    name = feed_cfg["name"]
    url  = feed_cfg["url"]
    try:
        parsed = feedparser.parse(url, agent="ITNewsHub/0.1")
        if parsed.bozo and not parsed.entries:
            logger.warning("Feed '%s' returned bozo error: %s", name, parsed.bozo_exception)
            feed_health.record(name, ok=False)
            return []

        articles = []
        for entry in parsed.entries[: settings.MAX_ARTICLES_PER_FEED]:
            link    = getattr(entry, "link", "")
            title   = html.unescape(getattr(entry, "title", "").strip())
            summary = clean_summary(getattr(entry, "summary", ""))

            if not link or not title:
                continue

            articles.append({
                "id":           _article_id(link),
                "title":        title,
                "summary":      summary,
                "url":          link,
                "source":       name,
                "published_at": _parse_date(entry),
                "fetched_at":   datetime.now(timezone.utc).isoformat(),
                "category":     None,
                "confidence":   None,
                "reason":       None,
            })

        feed_health.record(name, ok=True)
        logger.info("Fetched %d articles from '%s'", len(articles), name)
        return articles

    except Exception as exc:
        logger.error("Error fetching feed '%s': %s", name, exc)
        feed_health.record(name, ok=False)
        return []


def fetch_all_feeds(priorities: set[str] | None = None) -> list[dict]:
    """
    Fetcht alle konfigurierten Feeds und gibt kombinierte Artikel zurück.
    B3: priorities-Filter (z.B. {"high"}) für Tiered Polling.
    """
    all_articles = []
    for feed_cfg in FEEDS:
        if priorities is not None and feed_cfg.get("priority", "medium") not in priorities:
            continue
        all_articles.extend(fetch_feed(feed_cfg))
    return all_articles
