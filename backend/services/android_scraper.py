"""
Monatlicher Scraper für Android Security Bulletin und Samsung SMR.

Diese Quellen haben kein offizielles RSS-Feed — sie erscheinen am ersten Montag
jedes Monats. Dieser Scraper wird über einen APScheduler-CronTrigger aufgerufen.

Abhängigkeiten (muss in requirements.txt sein):
    httpx>=0.27
    beautifulsoup4>=4.12
    lxml>=5.0  (oder html.parser als Fallback)
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
_ANDROID_BULLETIN_URL = "https://source.android.com/docs/security/bulletin"
_SAMSUNG_SMR_URL      = "https://security.samsungmobile.com/securityUpdate.smsb"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ITNewsHub/1.0; +https://github.com/Kazuo3o447/News)"
}


def _make_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Android Security Bulletin
# ---------------------------------------------------------------------------

def scrape_android_bulletin() -> list[dict]:
    """
    Holt das neueste Android Security Bulletin von source.android.com.
    Gibt eine Liste von Artikel-Dicts im selben Schema wie rss_fetcher zurück.
    Gibt bei Fehler eine leere Liste zurück (robust gegen Layout-Änderungen).
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("android_scraper: httpx oder beautifulsoup4 nicht installiert")
        return []

    try:
        response = httpx.get(_ANDROID_BULLETIN_URL, headers=_HEADERS, timeout=15, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        # Suche die neueste Bulletin-Kachel / Liste (Layout: table oder article links)
        links = soup.select("a[href*='/docs/security/bulletin/']")
        seen_urls: set[str] = set()

        for link in links[:5]:   # max. 5 neueste
            href = link.get("href", "")
            if not href or href == _ANDROID_BULLETIN_URL.replace("https://source.android.com", ""):
                continue
            if not href.startswith("http"):
                href = "https://source.android.com" + href
            if href in seen_urls:
                continue
            seen_urls.add(href)

            title = link.get_text(strip=True) or "Android Security Bulletin"
            if not title or title.lower() == "android security bulletin":
                title = f"Android Security Bulletin — {link.get_text(strip=True)}"

            articles.append({
                "id":           _make_id(href),
                "title":        title,
                "summary":      "Monatliches Android Security Bulletin — geprüfte Schwachstellen und Patches.",
                "url":          href,
                "source":       "Android Security Bulletin",
                "platform":     "android",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at":   datetime.now(timezone.utc).isoformat(),
            })

        logger.info("android_scraper: %d Android Bulletin-Einträge gefunden", len(articles))
        return articles

    except Exception as exc:
        logger.error("android_scraper: Android Bulletin scraping fehlgeschlagen: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Samsung SMR (Security Maintenance Release)
# ---------------------------------------------------------------------------

def scrape_samsung_smr() -> list[dict]:
    """
    Holt die neuesten Samsung SMR-Einträge von security.samsungmobile.com.
    Gibt eine Liste von Artikel-Dicts zurück (leere Liste bei Fehler).
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("android_scraper: httpx oder beautifulsoup4 nicht installiert")
        return []

    try:
        response = httpx.get(_SAMSUNG_SMR_URL, headers=_HEADERS, timeout=15, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        # Samsung SMR-Seite listet Einträge — suche nach Bulletin-Links
        links = soup.select("a[href*='securityUpdate']") or soup.find_all("a", href=True)

        seen_urls: set[str] = set()
        for link in links[:5]:
            href = link.get("href", "")
            if not href or "security" not in href.lower():
                continue
            if not href.startswith("http"):
                href = "https://security.samsungmobile.com/" + href.lstrip("/")
            if href in seen_urls or href == _SAMSUNG_SMR_URL:
                continue
            seen_urls.add(href)

            title_text = link.get_text(strip=True)
            title = f"Samsung SMR — {title_text}" if title_text else "Samsung Security Maintenance Release"

            articles.append({
                "id":           _make_id(href),
                "title":        title,
                "summary":      "Samsung monatliches Security Maintenance Release (SMR) — Patches für Galaxy-Geräte.",
                "url":          href,
                "source":       "Samsung SMR",
                "platform":     "android",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at":   datetime.now(timezone.utc).isoformat(),
            })

        logger.info("android_scraper: %d Samsung SMR-Einträge gefunden", len(articles))
        return articles

    except Exception as exc:
        logger.error("android_scraper: Samsung SMR scraping fehlgeschlagen: %s", exc)
        return []
