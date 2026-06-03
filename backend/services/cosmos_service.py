"""
Azure Cosmos DB Service Layer.
Kapselt alle Datenbankoperationen für Articles.
Fallback: In-Memory-Speicher wenn AZURE_COSMOS_ENDPOINT nicht konfiguriert (Dev-Modus).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

from api.models.article import Article
from config.settings import settings

logger = logging.getLogger(__name__)

# OFF_TOPIC als gültiger Partition-Key-Wert — Partition Key bleibt "category"
Category = Literal["KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC"]

_VALID_CATEGORIES: frozenset[str] = frozenset({"KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC"})
_VALID_PLATFORMS:  frozenset[str] = frozenset({"windows", "apple", "android", "cross"})

# ---------------------------------------------------------------------------
# In-Memory-Speicher (Dev-Modus)
# ---------------------------------------------------------------------------
_memory_store: dict[str, dict] = {}


def _use_cosmos() -> bool:
    return bool(settings.AZURE_COSMOS_ENDPOINT and settings.AZURE_COSMOS_KEY)


# ---------------------------------------------------------------------------
# Cosmos DB Singleton (lazy init — nur wenn konfiguriert)
# ---------------------------------------------------------------------------
_container = None


def _get_container():
    global _container
    if _container is None:
        from azure.cosmos import CosmosClient
        client = CosmosClient(
            url=settings.AZURE_COSMOS_ENDPOINT,
            credential=settings.AZURE_COSMOS_KEY,
        )
        db = client.get_database_client(settings.AZURE_COSMOS_DB)
        _container = db.get_container_client(settings.AZURE_COSMOS_CONTAINER)
    return _container


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------

def upsert_article(article: Article) -> None:
    if _use_cosmos():
        try:
            _get_container().upsert_item(article.to_cosmos_doc())
        except Exception as exc:
            logger.error("Cosmos upsert failed for '%s': %s", article.id, exc)
            raise
    else:
        _memory_store[article.id] = article.to_cosmos_doc()


def upsert_many(articles: list[Article]) -> tuple[int, int]:
    ok = err = 0
    for article in articles:
        try:
            upsert_article(article)
            ok += 1
        except Exception:
            err += 1
    logger.info("upsert_many: %d ok, %d errors (mode=%s)", ok, err, "cosmos" if _use_cosmos() else "memory")
    return ok, err


# ---------------------------------------------------------------------------
# Lesen
# ---------------------------------------------------------------------------

def get_articles(
    category: Category | None = None,
    platform: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Article], int]:
    """
    Gibt paginierte Artikel zurück, optional gefiltert nach category und/oder platform.
    Sortierung: KRITISCH zuerst, dann absteigend nach published_at.

    SICHERHEIT: category und platform werden gegen erlaubte Enum-Werte geprüft
    bevor sie in Queries verwendet werden.
    """
    # Eingabe gegen erlaubte Werte prüfen (Query-Injection-Schutz)
    if category is not None and category not in _VALID_CATEGORIES:
        raise ValueError(f"Ungültige Kategorie: {category!r}")
    if platform is not None and platform not in _VALID_PLATFORMS:
        raise ValueError(f"Ungültige Plattform: {platform!r}")

    if _use_cosmos():
        # WHERE-Klauseln aufbauen (Werte sind durch Enum-Validierung oben sicher)
        conditions = []
        if category:
            conditions.append(f"c.category = '{category}'")
        if platform:
            conditions.append(f"c.platform = '{platform}'")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        # Cosmos DB unterstützt kein ORDER BY auf Ausdrücken → alle Matches holen,
        # in Python sortieren (KRITISCH first), dann paginieren.
        # Das Dataset ist durch ARTICLE_RETENTION_DAYS begrenzt (Default 7 Tage).
        items_query = f"SELECT * FROM c {where}"
        try:
            container = _get_container()
            raw_items = list(container.query_items(items_query, enable_cross_partition_query=True))
        except Exception as exc:
            logger.error("Cosmos get_articles failed: %s", exc)
            return [], 0

        # Sortierung: KRITISCH=0, sonst=1; sekundär published_at DESC
        raw_items.sort(
            key=lambda a: (0 if a.get("category") == "KRITISCH" else 1,
                           a.get("published_at", "")),
            reverse=False,
        )
        # published_at soll DESC sein, aber KRITISCH-Priorität ASC → kombinierter Key
        raw_items.sort(key=lambda a: (
            0 if a.get("category") == "KRITISCH" else 1,
            # Negierung simulieren: invertiertes ISO-Datum (funktioniert für gleich lange Strings)
        ))
        # Sauberere Variante: zweistufig sortieren
        raw_items = sorted(
            raw_items,
            key=lambda a: (
                0 if a.get("category") == "KRITISCH" else 1,
                "~" if not a.get("published_at") else
                "".join(chr(0x7E - ord(c)) if c.isdigit() else c
                        for c in a.get("published_at", "")),
            ),
        )

        total      = len(raw_items)
        start      = (page - 1) * page_size
        page_items = raw_items[start: start + page_size]
        return [Article.from_cosmos_doc(doc) for doc in page_items], total

    else:
        # In-Memory
        items = list(_memory_store.values())
        if category:
            items = [a for a in items if a.get("category") == category]
        if platform:
            items = [a for a in items if a.get("platform") == platform]

        # KRITISCH zuerst, dann published_at DESC
        items.sort(
            key=lambda a: (
                0 if a.get("category") == "KRITISCH" else 1,
                a.get("published_at", ""),
            ),
        )
        # published_at DESC innerhalb jeder Prioritätsstufe
        kritisch = [a for a in items if a.get("category") == "KRITISCH"]
        others   = [a for a in items if a.get("category") != "KRITISCH"]
        kritisch.sort(key=lambda a: a.get("published_at", ""), reverse=True)
        others.sort(key=lambda a: a.get("published_at", ""), reverse=True)
        items = kritisch + others

        total      = len(items)
        start      = (page - 1) * page_size
        page_items = items[start: start + page_size]
        return [Article.from_cosmos_doc(doc) for doc in page_items], total


def get_article_by_id(article_id: str) -> Article | None:
    if _use_cosmos():
        # Parametrisieren ist bei Cosmos SDK nicht verfügbar → ID-Format validieren
        # IDs sind SHA-256-Hashes (64 Hex-Zeichen) oder kürzer — einfache Validierung
        if not article_id.replace("-", "").replace("_", "").isalnum():
            return None
        query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
        try:
            results = list(_get_container().query_items(query, enable_cross_partition_query=True))
            return Article.from_cosmos_doc(results[0]) if results else None
        except Exception as exc:
            logger.error("Cosmos get_article_by_id failed: %s", exc)
            return None
    else:
        doc = _memory_store.get(article_id)
        return Article.from_cosmos_doc(doc) if doc else None


def get_known_ids() -> set[str]:
    if _use_cosmos():
        query = "SELECT c.id FROM c"
        try:
            return {doc["id"] for doc in _get_container().query_items(query, enable_cross_partition_query=True)}
        except Exception as exc:
            logger.error("Cosmos get_known_ids failed: %s", exc)
            return set()
    else:
        return set(_memory_store.keys())


def delete_articles_older_than(cutoff_iso: str) -> int:
    """
    Löscht alle Artikel mit fetched_at < cutoff_iso.
    cutoff_iso muss als UTC-ISO-String vorliegen.
    Partition Key ist category → delete_item muss partition_key=row["category"] verwenden.
    """
    deleted = 0
    if _use_cosmos():
        query = (
            "SELECT c.id, c.category FROM c "
            f"WHERE IS_DEFINED(c.fetched_at) AND c.fetched_at < '{cutoff_iso}'"
        )
        try:
            container = _get_container()
            rows = list(container.query_items(query, enable_cross_partition_query=True))
            for row in rows:
                container.delete_item(item=row["id"], partition_key=row["category"])
                deleted += 1
        except Exception as exc:
            logger.error("Cosmos cleanup failed: %s", exc)
            return 0
        logger.info("cleanup: %d alte Artikel gelöscht (mode=cosmos)", deleted)
        return deleted

    for article_id, doc in list(_memory_store.items()):
        fetched_at = doc.get("fetched_at")
        if not fetched_at:
            continue
        try:
            if datetime.fromisoformat(fetched_at) < datetime.fromisoformat(cutoff_iso):
                _memory_store.pop(article_id, None)
                deleted += 1
        except ValueError:
            continue

    logger.info("cleanup: %d alte Artikel gelöscht (mode=memory)", deleted)
    return deleted

# ---------------------------------------------------------------------------
# In-Memory-Speicher (Dev-Modus)
# ---------------------------------------------------------------------------
_memory_store: dict[str, dict] = {}


def _use_cosmos() -> bool:
    return bool(settings.AZURE_COSMOS_ENDPOINT and settings.AZURE_COSMOS_KEY)


# ---------------------------------------------------------------------------
# Cosmos DB Singleton (lazy init — nur wenn konfiguriert)
# ---------------------------------------------------------------------------
_container = None


def _get_container():
    global _container
    if _container is None:
        from azure.cosmos import CosmosClient
        client = CosmosClient(
            url=settings.AZURE_COSMOS_ENDPOINT,
            credential=settings.AZURE_COSMOS_KEY,
        )
        db = client.get_database_client(settings.AZURE_COSMOS_DB)
        _container = db.get_container_client(settings.AZURE_COSMOS_CONTAINER)
    return _container


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------

def upsert_article(article: Article) -> None:
    if _use_cosmos():
        try:
            from azure.cosmos import exceptions
            _get_container().upsert_item(article.to_cosmos_doc())
        except Exception as exc:
            logger.error("Cosmos upsert failed for '%s': %s", article.id, exc)
            raise
    else:
        _memory_store[article.id] = article.to_cosmos_doc()


def upsert_many(articles: list[Article]) -> tuple[int, int]:
    ok = err = 0
    for article in articles:
        try:
            upsert_article(article)
            ok += 1
        except Exception:
            err += 1
    logger.info("upsert_many: %d ok, %d errors (mode=%s)", ok, err, "cosmos" if _use_cosmos() else "memory")
    return ok, err


# ---------------------------------------------------------------------------
# Lesen
# ---------------------------------------------------------------------------

def get_articles(
    category: Category | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Article], int]:
    if _use_cosmos():
        query_filter = f"WHERE c.category = '{category}'" if category else ""
        count_query  = f"SELECT VALUE COUNT(1) FROM c {query_filter}"
        items_query  = (
            f"SELECT * FROM c {query_filter} "
            f"ORDER BY c.published_at DESC "
            f"OFFSET {(page - 1) * page_size} LIMIT {page_size}"
        )
        try:
            container = _get_container()
            total     = list(container.query_items(count_query, enable_cross_partition_query=True))[0]
            raw_items = list(container.query_items(items_query, enable_cross_partition_query=True))
            return [Article.from_cosmos_doc(doc) for doc in raw_items], total
        except Exception as exc:
            logger.error("Cosmos get_articles failed: %s", exc)
            return [], 0
    else:
        # In-Memory
        items = list(_memory_store.values())
        if category:
            items = [a for a in items if a.get("category") == category]
        items.sort(key=lambda a: a.get("published_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start: start + page_size]
        return [Article.from_cosmos_doc(doc) for doc in page_items], total


def get_article_by_id(article_id: str) -> Article | None:
    if _use_cosmos():
        query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
        try:
            results = list(_get_container().query_items(query, enable_cross_partition_query=True))
            return Article.from_cosmos_doc(results[0]) if results else None
        except Exception as exc:
            logger.error("Cosmos get_article_by_id failed: %s", exc)
            return None
    else:
        doc = _memory_store.get(article_id)
        return Article.from_cosmos_doc(doc) if doc else None


def get_known_ids() -> set[str]:
    if _use_cosmos():
        query = "SELECT c.id FROM c"
        try:
            return {doc["id"] for doc in _get_container().query_items(query, enable_cross_partition_query=True)}
        except Exception as exc:
            logger.error("Cosmos get_known_ids failed: %s", exc)
            return set()
    else:
        return set(_memory_store.keys())


def delete_articles_older_than(cutoff_iso: str) -> int:
    """
    Löscht alle Artikel mit fetched_at < cutoff_iso.
    cutoff_iso muss als UTC-ISO-String vorliegen.
    """
    deleted = 0
    if _use_cosmos():
        query = (
            "SELECT c.id, c.category FROM c "
            f"WHERE IS_DEFINED(c.fetched_at) AND c.fetched_at < '{cutoff_iso}'"
        )
        try:
            container = _get_container()
            rows = list(container.query_items(query, enable_cross_partition_query=True))
            for row in rows:
                container.delete_item(item=row["id"], partition_key=row["category"])
                deleted += 1
        except Exception as exc:
            logger.error("Cosmos cleanup failed: %s", exc)
            return 0
        logger.info("cleanup: %d alte Artikel gelöscht (mode=cosmos)", deleted)
        return deleted

    for article_id, doc in list(_memory_store.items()):
        fetched_at = doc.get("fetched_at")
        if not fetched_at:
            continue
        try:
            if datetime.fromisoformat(fetched_at) < datetime.fromisoformat(cutoff_iso):
                _memory_store.pop(article_id, None)
                deleted += 1
        except ValueError:
            continue

    logger.info("cleanup: %d alte Artikel gelöscht (mode=memory)", deleted)
    return deleted
