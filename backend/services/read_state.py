"""
B2 — Team-Gelesen-Status.

Speichert pro Artikel, welche User ihn als gelesen markiert haben.
Cosmos-Container "reads": { "id": article_id, "read_by": ["max.muster", "anna.k"] }
In-Memory-Fallback: dict[str, set[str]]
"""
from __future__ import annotations

import logging

from config.settings import settings

logger = logging.getLogger(__name__)

# In-Memory-Fallback
_memory_reads: dict[str, set[str]] = {}


def _use_cosmos() -> bool:
    return bool(settings.AZURE_COSMOS_ENDPOINT and settings.AZURE_COSMOS_KEY)


_reads_container = None


def _get_container():
    global _reads_container
    if _reads_container is None:
        from azure.cosmos import CosmosClient
        client = CosmosClient(
            url=settings.AZURE_COSMOS_ENDPOINT,
            credential=settings.AZURE_COSMOS_KEY,
        )
        db = _reads_container = client.get_database_client(settings.AZURE_COSMOS_DB)
        _reads_container = db.get_container_client(settings.AZURE_COSMOS_READS_CONTAINER)
    return _reads_container


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------

def mark_read(article_id: str, user: str) -> None:
    if _use_cosmos():
        try:
            c = _get_container()
            try:
                doc = c.read_item(article_id, partition_key=article_id)
            except Exception:
                doc = {"id": article_id, "read_by": []}
            if user not in doc["read_by"]:
                doc["read_by"].append(user)
                c.upsert_item(doc)
        except Exception as exc:
            logger.warning("read_state.mark_read failed: %s", exc)
    else:
        _memory_reads.setdefault(article_id, set()).add(user)


def mark_unread(article_id: str, user: str) -> None:
    if _use_cosmos():
        try:
            c = _get_container()
            try:
                doc = c.read_item(article_id, partition_key=article_id)
                if user in doc["read_by"]:
                    doc["read_by"].remove(user)
                    c.upsert_item(doc)
            except Exception:
                pass  # doc existiert nicht — war nie gelesen
        except Exception as exc:
            logger.warning("read_state.mark_unread failed: %s", exc)
    else:
        _memory_reads.get(article_id, set()).discard(user)


def mark_read_bulk(article_ids: list[str], user: str) -> None:
    for aid in article_ids:
        mark_read(aid, user)


def read_map(article_ids: list[str]) -> dict[str, list[str]]:
    """Gibt für jeden article_id die Liste der User zurück, die ihn gelesen haben."""
    if not article_ids:
        return {}

    if _use_cosmos():
        result: dict[str, list[str]] = {aid: [] for aid in article_ids}
        try:
            c = _get_container()
            placeholders = ", ".join(f"@id{i}" for i in range(len(article_ids)))
            params = [{"name": f"@id{i}", "value": aid} for i, aid in enumerate(article_ids)]
            query = f"SELECT c.id, c.read_by FROM c WHERE c.id IN ({placeholders})"
            for doc in c.query_items(query, parameters=params, enable_cross_partition_query=True):
                result[doc["id"]] = doc.get("read_by", [])
        except Exception as exc:
            logger.warning("read_state.read_map failed: %s", exc)
        return result
    else:
        return {
            aid: list(_memory_reads.get(aid, set()))
            for aid in article_ids
        }


def is_read(article_id: str, user: str) -> bool:
    if _use_cosmos():
        try:
            doc = _get_container().read_item(article_id, partition_key=article_id)
            return user in doc.get("read_by", [])
        except Exception:
            return False
    else:
        return user in _memory_reads.get(article_id, set())
