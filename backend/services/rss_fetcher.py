"""
RSS Feed-Fetcher: Liest alle konfigurierten Feeds und gibt normalisierte Artikel zurück.
"""
import hashlib
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from config.feeds import FEEDS
from config.settings import settings

logger = logging.getLogger(__name__)


def _parse_date(entry) -> str:
    """Extrahiert ISO-8601-Datum aus einem feedparser-Entry."""
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
            return []

        articles = []
        for entry in parsed.entries[: settings.MAX_ARTICLES_PER_FEED]:
            link    = getattr(entry, "link", "")
            title   = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "").strip()

            if not link or not title:
                continue

            articles.append({
                "id":           _article_id(link),
                "title":        title,
                "summary":      summary[:1000],
                "url":          link,
                "source":       name,
                "published_at": _parse_date(entry),
                "fetched_at":   datetime.now(timezone.utc).isoformat(),
                # Klassifizierung wird separat durch groq_classifier befüllt
                "category":     None,
                "confidence":   None,
                "reason":       None,
            })
        logger.info("Fetched %d articles from '%s'", len(articles), name)
        return articles

    except Exception as exc:
        logger.error("Error fetching feed '%s': %s", name, exc)
        return []


def fetch_all_feeds() -> list[dict]:
    """Fetcht alle konfigurierten Feeds und gibt kombinierte Artikel zurück."""
    all_articles = []
    for feed_cfg in FEEDS:
        all_articles.extend(fetch_feed(feed_cfg))
    return all_articles
