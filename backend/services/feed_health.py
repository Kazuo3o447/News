"""
Feed-Health-Tracking: In-Memory-Zustand pro Feed-Quelle.
Meldet tote Feeds via WARN-Log sobald 3 aufeinanderfolgende Fehler auftreten.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# { source_name: { "last_success": iso|None, "consecutive_failures": int } }
_health: dict[str, dict] = {}

_WARN_THRESHOLD = 3


def record(source: str, ok: bool) -> None:
    """Erfasst einen Fetch-Versuch für eine Feed-Quelle."""
    entry = _health.setdefault(source, {"last_success": None, "consecutive_failures": 0})
    if ok:
        entry["last_success"] = datetime.now(timezone.utc).isoformat()
        entry["consecutive_failures"] = 0
    else:
        entry["consecutive_failures"] += 1
        if entry["consecutive_failures"] >= _WARN_THRESHOLD:
            logger.warning(
                "Feed '%s' seit %d Läufen nicht erreichbar (letzter Erfolg: %s)",
                source,
                entry["consecutive_failures"],
                entry["last_success"] or "nie",
            )


def get_health() -> dict[str, dict]:
    """Gibt den aktuellen Gesundheitszustand aller bekannten Feeds zurück."""
    return {
        source: {
            "last_success":          entry["last_success"],
            "consecutive_failures":  entry["consecutive_failures"],
            "status":                "ok" if entry["consecutive_failures"] == 0 else
                                     ("warn" if entry["consecutive_failures"] < _WARN_THRESHOLD else "dead"),
        }
        for source, entry in _health.items()
    }
