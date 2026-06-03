"""
KRITISCH-Push via Teams-Webhook (Power Automate HTTP-Trigger oder Legacy Incoming Webhook).
Wenn TEAMS_WEBHOOK_URL leer ist, ist dieser Dienst ein No-op.

B6: Cluster-Dedup — pro cluster_id wird höchstens einmal innerhalb des DEDUP_WINDOW_HOURS
    eine Benachrichtigung ausgelöst.  In-Memory Set + optionale Cosmos-Persistenz.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from config.settings import settings

if TYPE_CHECKING:
    from api.models.article import Article

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# B6: In-Memory Cluster-Dedup
# ---------------------------------------------------------------------------
# Jeder Eintrag: cluster_id -> unix-Timestamp wann zuerst notifiziert
_notified_clusters: dict[str, float] = {}


def _dedup_ttl_seconds() -> float:
    return max(1, settings.DEDUP_WINDOW_HOURS) * 3600


def _evict_expired() -> None:
    """Entfernt abgelaufene Einträge aus dem In-Memory-Cache."""
    now = time.time()
    ttl = _dedup_ttl_seconds()
    expired = [k for k, ts in _notified_clusters.items() if now - ts > ttl]
    for k in expired:
        del _notified_clusters[k]


def was_notified(cluster_id: str) -> bool:
    """True wenn cluster_id innerhalb des Dedup-Fensters bereits notifiziert wurde."""
    ts = _notified_clusters.get(cluster_id)
    if ts is None:
        return False
    if time.time() - ts > _dedup_ttl_seconds():
        del _notified_clusters[cluster_id]
        return False
    return True


def mark_notified(cluster_id: str) -> None:
    """Markiert cluster_id als notifiziert (mit aktuellem Timestamp)."""
    _evict_expired()
    _notified_clusters[cluster_id] = time.time()

    # Optional: Cosmos-Persistenz über notified-Container
    try:
        from azure.cosmos import CosmosClient
        from config.settings import settings as _s
        if not (_s.AZURE_COSMOS_ENDPOINT and _s.AZURE_COSMOS_KEY):
            return
        client = CosmosClient(_s.AZURE_COSMOS_ENDPOINT, credential=_s.AZURE_COSMOS_KEY)
        db   = client.get_database_client(_s.AZURE_COSMOS_DATABASE)
        cont = db.get_container_client(_s.AZURE_COSMOS_NOTIFIED_CONTAINER)
        ttl  = int(_dedup_ttl_seconds())
        cont.upsert_item({
            "id":          cluster_id,
            "notified_at": datetime.now(timezone.utc).isoformat(),
            "ttl":         ttl,
        })
    except Exception as exc:
        logger.debug("mark_notified: Cosmos-Schreib-Fehler ignoriert — %s", exc)


# ---------------------------------------------------------------------------
# Teams Webhook Push
# ---------------------------------------------------------------------------

def notify_critical(articles: list["Article"]) -> None:
    """
    Sendet neue KRITISCH-Artikel als kompakten JSON-Payload an den konfigurierten Webhook.
    B6: Filtert bereits notifizierte Cluster heraus.

    - Kein Webhook konfiguriert (leer) → No-op, kein Fehler.
    - Fehler beim Senden → WARN-Log, Pipeline crasht NICHT.
    """
    if not settings.TEAMS_WEBHOOK_URL:
        return
    if not articles:
        return

    # B6: Nur un-notifizierte Cluster senden
    new_articles = [a for a in articles if not was_notified(a.cluster_id or a.id)]
    if not new_articles:
        logger.info("notify_critical: alle %d Artikel bereits notifiziert (Dedup).", len(articles))
        return

    # Cluster-IDs sofort markieren (vor dem HTTP-Call, verhindert Doppelsendung bei Retry)
    for a in new_articles:
        mark_notified(a.cluster_id or a.id)

    try:
        import httpx

        # Cluster-Größe: Anzahl Artikel pro cluster_id in dieser Runde
        cluster_counts: dict[str, int] = {}
        for a in articles:
            cid = a.cluster_id or a.id
            cluster_counts[cid] = cluster_counts.get(cid, 0) + 1

        items = []
        for a in new_articles:
            items.append({
                "title":        a.title,
                "platform":     a.platform or "cross",
                "cvss":         a.cvss,
                "cve_ids":      a.cve_ids,
                "url":          a.url,
                "source":       a.source,
                "tldr":         a.tldr or "",
                "cluster_size": cluster_counts.get(a.cluster_id or a.id, 1),
            })

        payload = {
            "summary":       f"{len(new_articles)} neue kritische Meldung(en)",
            "alert_count":   len(new_articles),
            "items":         items,
        }

        response = httpx.post(
            settings.TEAMS_WEBHOOK_URL,
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info(
            "notify_critical: %d Meldungen gesendet (HTTP %s, %d durch Dedup gefiltert)",
            len(new_articles), response.status_code, len(articles) - len(new_articles),
        )

    except Exception as exc:
        logger.warning(
            "notify_critical: Push fehlgeschlagen (%d Meldungen) — %s",
            len(new_articles),
            exc,
        )
