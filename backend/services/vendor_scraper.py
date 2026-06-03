"""
Scraper für Vendor-Security-Quellen ohne offizielles RSS-Feed.

- scrape_apple_security()  → Apple Security Releases (PFLICHT, T9)
  Quelle: https://support.apple.com/en-us/100100

Abhängigkeiten (muss in requirements.txt sein):
    httpx>=0.27
    beautifulsoup4>=4.12
    lxml>=5.0  (oder html.parser als Fallback)

Fallback-Hinweis: Wer keine eigenen Scraper warten will, kann diese Quellen
alternativ über eine RSSHub-Instanz als pseudo-RSS in feeds.py einhängen:
    https://rsshub.app/apple/security-updates
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_APPLE_RELEASES_URL = "https://support.apple.com/en-us/100100"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ITNewsHub/1.0; +https://github.com/Kazuo3o447/News)"
}

_MAX_RELEASES = 20


def _make_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def _parse_apple_date(text: str) -> str:
    """
    Parst Apple-Datumsformat ("June 5, 2026" / "05 Jun 2026") → UTC-ISO-String.
    Bei Fehler: aktuelles Datum.
    """
    text = text.strip()
    formats = ["%B %d, %Y", "%d %b %Y", "%b %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def _platform_from_title(title: str) -> str:
    """Leitet den Plattform-Prior aus dem Release-Namen ab."""
    t = title.lower()
    if any(kw in t for kw in ("ios", "ipados", "iphone", "ipad", "watchos", "tvos", "visionos")):
        return "apple"
    if any(kw in t for kw in ("macos", "mac os", "safari", "xcode", "itunes")):
        return "apple"
    return "apple"   # alle Apple-Releases → platform="apple"


# ---------------------------------------------------------------------------
# Apple Security Releases
# ---------------------------------------------------------------------------

def scrape_apple_security() -> list[dict]:
    """
    Holt die aktuellen Apple Security Releases von support.apple.com/en-us/100100.

    Die Seite enthält eine Tabelle aller Releases mit Release-Name, Link zum
    Advisory und Datum. Gibt eine Liste von Artikel-Dicts im selben Schema wie
    rss_fetcher zurück. Gibt bei Fehler eine leere Liste zurück.
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("vendor_scraper: httpx oder beautifulsoup4 nicht installiert")
        return []

    try:
        response = httpx.get(_APPLE_RELEASES_URL, headers=_HEADERS, timeout=20, follow_redirects=True)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("vendor_scraper: Apple-Seite nicht erreichbar — %s", exc)
        return []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        articles: list[dict] = []
        seen_urls: set[str] = set()

        # Die Seite enthält eine Tabelle mit <tr> je Release.
        # Spalten: Release-Name (mit Link), Datum.
        # Alternativ: <li> oder <p>-Blöcke — wir suchen robust nach Links mit Advisory-URLs.
        rows = soup.select("table tr")

        if not rows:
            # Fallback: Links auf /en-us/HT* (Apple Advisory-IDs) direkt suchen
            rows = []

        release_entries: list[tuple[str, str, str]] = []  # (title, url, date_text)

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            # Erste Zelle: Release-Name + optional Link
            name_cell = cells[0]
            link_tag = name_cell.find("a")
            title = name_cell.get_text(separator=" ", strip=True)
            if not title or title.lower() in ("name", "release"):
                continue

            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                if not href.startswith("http"):
                    href = "https://support.apple.com" + href
            else:
                # Kein Advisory-Link (z.B. "Rapid Security Response already applied")
                href = _APPLE_RELEASES_URL

            # Letzte Zelle: Datum
            date_text = cells[-1].get_text(strip=True)

            if href not in seen_urls:
                seen_urls.add(href)
                release_entries.append((title, href, date_text))

        # Fallback wenn Tabellen-Parsing nichts ergab: Links auf Apple HT-Advisories
        if not release_entries:
            for link in soup.find_all("a", href=re.compile(r"/en-us/HT\d+")):
                href = link["href"]
                if not href.startswith("http"):
                    href = "https://support.apple.com" + href
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                title = link.get_text(strip=True) or "Apple Security Update"
                # Datum aus umliegendem Text extrahieren
                parent_text = (link.parent or link).get_text(separator=" ", strip=True)
                date_match = re.search(r"(\w+ \d{1,2},?\s*\d{4}|\d{1,2} \w+ \d{4})", parent_text)
                date_text = date_match.group(1) if date_match else ""
                release_entries.append((title, href, date_text))

        for title, url, date_text in release_entries[:_MAX_RELEASES]:
            published_at = _parse_apple_date(date_text) if date_text else datetime.now(timezone.utc).isoformat()
            platform = _platform_from_title(title)

            articles.append({
                "id":           _make_id(url),
                "title":        title,
                "summary":      f"Apple Security Release: {title}. Weitere Details im Advisory unter {url}.",
                "url":          url,
                "source":       "Apple Security Releases",
                "published_at": published_at,
                "platform":     platform,
                "category":     None,
                "tags":         [],
                "topics":       [],
            })

        logger.info("vendor_scraper: %d Apple Security Releases gefunden", len(articles))
        return articles

    except Exception as exc:
        logger.warning("vendor_scraper: Fehler beim Parsen der Apple-Seite — %s", exc)
        return []
