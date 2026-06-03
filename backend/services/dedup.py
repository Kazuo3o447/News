"""
Dedup / Clustering-Schicht.

Ordnet jeden neuen Artikel einem cluster_id zu:
- Hat der Artikel cve_ids: kleinste CVE-ID (lexikografisch) als Schlüssel.
- Sonst: normalisierter Titel. Existiert ein Artikel mit gleichem Normaltitel in
  den letzten DEDUP_WINDOW_HOURS → cluster_id übernehmen; sonst sha1(normtitel)[:12].
"""
from __future__ import annotations

import hashlib
import re

from api.models.article import Article
from config.settings import settings

# Stopwörter und Satzzeichen für Normalisierung
_RE_NON_ALPHA = re.compile(r"[^a-z0-9\s]")
_RE_WS        = re.compile(r"\s+")
_STOPWORDS = frozenset({
    "a", "an", "the", "in", "on", "at", "is", "are", "was", "were", "for", "of",
    "to", "and", "or", "but", "mit", "in", "für", "von", "und", "der", "die", "das",
    "ein", "eine", "zu", "auf", "bei", "als", "mit", "nach", "aus", "im", "an",
})


def _normalize_title(title: str) -> str:
    """Lowercase, Satzzeichen entfernen, Stopwörter raus, Whitespace kollabieren."""
    t = title.lower()
    t = _RE_NON_ALPHA.sub(" ", t)
    words = [w for w in _RE_WS.split(t) if w and w not in _STOPWORDS]
    return " ".join(words)


def cluster_key(article: Article, recent: list[Article]) -> str:
    """
    Berechnet einen cluster_id für den Artikel.

    Priorität:
    1. Kleinste CVE-ID wenn vorhanden (alle Artikel mit derselben CVE teilen sich den Cluster).
    2. Normalisierter Titel — falls ein Artikel aus `recent` gleichen Normaltitel hat,
       wird dessen cluster_id übernommen.
    3. Neuer sha1(normtitel)[:12] für neue Cluster.
    """
    # --- CVE-Cluster ---
    if article.cve_ids:
        return min(article.cve_ids)   # lexikografisch kleinste CVE-ID

    # --- Titelbasierter Cluster ---
    norm = _normalize_title(article.title)
    if not norm:
        # Leerer normalisierter Titel — jeder Artikel bekommt eigene ID
        return hashlib.sha1(article.id.encode()).hexdigest()[:12]

    # Passendes recent-Objekt suchen
    for r in recent:
        r_norm = _normalize_title(r.title)
        if r_norm == norm and r.cluster_id:
            return r.cluster_id

    # Neuen Cluster anlegen
    return hashlib.sha1(norm.encode()).hexdigest()[:12]
