"""
KRITISCH-Push via Teams-Webhook (Power Automate HTTP-Trigger oder Legacy Incoming Webhook).
Wenn TEAMS_WEBHOOK_URL leer ist, ist dieser Dienst ein No-op.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from config.settings import settings

if TYPE_CHECKING:
    from api.models.article import Article

logger = logging.getLogger(__name__)


def notify_critical(articles: list["Article"]) -> None:
    """
    Sendet neue KRITISCH-Artikel als kompakten JSON-Payload an den konfigurierten Webhook.

    - Kein Webhook konfiguriert (leer) → No-op, kein Fehler.
    - Fehler beim Senden → WARN-Log, Pipeline crasht NICHT.
    - Idempotenz: Der Aufrufer (Scheduler) übergiebt nur Artikel, die in DIESEM Lauf
      neu als KRITISCH klassifiziert wurden.
    """
    if not settings.TEAMS_WEBHOOK_URL:
        return

    if not articles:
        return

    try:
        import httpx

        items = []
        for a in articles:
            items.append({
                "title":    a.title,
                "platform": a.platform or "cross",
                "cvss":     a.cvss,
                "cve_ids":  a.cve_ids,
                "url":      a.url,
                "source":   a.source,
                "tldr":     a.tldr or "",
            })

        payload = {
            "summary":       f"{len(articles)} neue kritische Meldung(en)",
            "alert_count":   len(articles),
            "items":         items,
        }

        response = httpx.post(
            settings.TEAMS_WEBHOOK_URL,
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("notify_critical: %d Meldungen gesendet (HTTP %s)", len(articles), response.status_code)

    except Exception as exc:
        logger.warning(
            "notify_critical: Push fehlgeschlagen (%d Meldungen) — %s",
            len(articles),
            exc,
        )
