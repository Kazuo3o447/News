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

Category = Literal["KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC", "PENDING"]

_VALID_CATEGORIES: frozenset[str] = frozenset({"KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC", "PENDING"})
_VALID_PLATFORMS:  frozenset[str] = frozenset({"windows", "apple", "android", "cross"})

# ---------------------------------------------------------------------------
# In-Memory-Speicher (Dev-Modus)
# ---------------------------------------------------------------------------
_memory_store: dict[str, dict] = {}


def _use_cosmos() -> bool:
    return bool(settings.AZURE_COSMOS_ENDPOINT and settings.AZURE_COSMOS_KEY)


# ---------------------------------------------------------------------------
# Cosmos DB Singleton (lazy init)
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
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _sort_kritisch_first(items: list[dict]) -> list[dict]:
    """KRITISCH zuerst, innerhalb jeder Gruppe absteigend nach published_at."""
    kritisch = sorted(
        [a for a in items if a.get("category") == "KRITISCH"],
        key=lambda a: a.get("published_at", ""), reverse=True,
    )
    others = sorted(
        [a for a in items if a.get("category") != "KRITISCH"],
        key=lambda a: a.get("published_at", ""), reverse=True,
    )
    return kritisch + others


def _collapse_clusters(items: list[dict]) -> list[dict]:
    """
    Wenn collapse=True: Pro cluster_id nur den Repräsentanten behalten.
    Repräsentant = höchste Kritikalität, dann neuestes published_at.
    Hängt cluster_size und cluster_sources ans Repräsentanten-Dict.
    """
    _PRIO = {"KRITISCH": 0, "NORMAL": 1, "DUMP": 2, "OFF_TOPIC": 3, "PENDING": 4}

    clusters: dict[str, list[dict]] = {}
    no_cluster: list[dict] = []

    for item in items:
        cid = item.get("cluster_id")
        if cid:
            clusters.setdefault(cid, []).append(item)
        else:
            no_cluster.append(item)

    representatives: list[dict] = []
    for cid, members in clusters.items():
        rep = sorted(
            members,
            key=lambda a: (
                _PRIO.get(a.get("category") or "PENDING", 99),
                "" if not a.get("published_at") else a["published_at"],
            ),
            reverse=False,
        )[0]
        rep = dict(rep)
        rep["cluster_size"] = len(members)
        rep["cluster_sources"] = sorted({m.get("source", "") for m in members if m.get("source")})
        representatives.append(rep)

    return _sort_kritisch_first(representatives + no_cluster)


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
    collapse: bool = False,
    # B1 — neue Filter
    view: str | None = None,       # "all" | "unread" | "critical"
    q: str | None = None,          # Freitext (title + summary + source)
    topic: str | None = None,      # Topic-Key
    source: str | None = None,     # Quellenname
    since: str | None = None,      # ISO-8601 — nur Artikel neuer als dieser Zeitstempel
    user: str | None = None,       # aktueller User (für view=unread / is_read Anreicherung)
    read_map_fn=None,              # injiziertes read_state.read_map (Circular-Import-Schutz)
) -> tuple[list[Article], int]:
    """
    Gibt paginierte Artikel zurück.
    collapse=True: Pro cluster_id nur den Repräsentanten zurückgeben.
    SICHERHEIT: Alle Filterwerte validiert/parametrisiert — keine SQL-Injection.
    """
    if category is not None and category not in _VALID_CATEGORIES:
        raise ValueError(f"Ungültige Kategorie: {category!r}")
    if platform is not None and platform not in _VALID_PLATFORMS:
        raise ValueError(f"Ungültige Plattform: {platform!r}")

    page_size = min(page_size, 60)  # B1: hart auf 60 deckeln

    # view shortcut
    if view == "critical":
        category = "KRITISCH"

    if _use_cosmos():
        # --- Parametrisierte Cosmos-Query ---
        conditions: list[str] = []
        params: list[dict] = []

        if category:
            conditions.append("c.category = @category")
            params.append({"name": "@category", "value": category})
        if platform:
            conditions.append("(c.platform = @platform OR c.platform = 'cross')")
            params.append({"name": "@platform", "value": platform})
        if q:
            q_lower = q.lower()
            conditions.append(
                "CONTAINS(LOWER(c.title), @q) OR CONTAINS(LOWER(c.summary), @q) OR CONTAINS(LOWER(c.source), @q)"
            )
            params.append({"name": "@q", "value": q_lower})
        if topic:
            conditions.append("ARRAY_CONTAINS(c.topics, @topic)")
            params.append({"name": "@topic", "value": topic})
        if source:
            conditions.append("c.source = @source")
            params.append({"name": "@source", "value": source})
        if since:
            conditions.append("(c.published_at > @since OR c.fetched_at > @since)")
            params.append({"name": "@since", "value": since})

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        items_query = f"SELECT * FROM c {where}"
        try:
            raw_items = list(_get_container().query_items(
                items_query,
                parameters=params if params else None,
                enable_cross_partition_query=True,
            ))
        except Exception as exc:
            logger.error("Cosmos get_articles failed: %s", exc)
            return [], 0

        if collapse:
            raw_items = _collapse_clusters(raw_items)
        else:
            raw_items = _sort_kritisch_first(raw_items)

        # view=unread — nach read_map filtern
        if view == "unread" and user and read_map_fn:
            ids = [a["id"] for a in raw_items]
            rmap = read_map_fn(ids)
            raw_items = [a for a in raw_items if user not in rmap.get(a["id"], [])]

        total      = len(raw_items)
        start      = (page - 1) * page_size
        page_items = raw_items[start: start + page_size]
        return [Article.from_cosmos_doc(doc) for doc in page_items], total

    else:
        # --- In-Memory-Pfad ---
        items = list(_memory_store.values())

        if category:
            items = [a for a in items if a.get("category") == category]
        if platform:
            items = [a for a in items if a.get("platform") in (platform, "cross")]
        if q:
            q_lower = q.lower()
            items = [
                a for a in items
                if q_lower in (a.get("title") or "").lower()
                or q_lower in (a.get("summary") or "").lower()
                or q_lower in (a.get("source") or "").lower()
            ]
        if topic:
            items = [a for a in items if topic in (a.get("topics") or [])]
        if source:
            items = [a for a in items if a.get("source") == source]
        if since:
            items = [
                a for a in items
                if (a.get("published_at") or a.get("fetched_at") or "") > since
            ]

        if collapse:
            items = _collapse_clusters(items)
        else:
            items = _sort_kritisch_first(items)

        # view=unread
        if view == "unread" and user and read_map_fn:
            ids = [a["id"] for a in items]
            rmap = read_map_fn(ids)
            items = [a for a in items if user not in rmap.get(a["id"], [])]

        total      = len(items)
        start      = (page - 1) * page_size
        page_items = items[start: start + page_size]
        return [Article.from_cosmos_doc(doc) for doc in page_items], total


def get_article_by_id(article_id: str) -> Article | None:
    if _use_cosmos():
        try:
            results = list(_get_container().query_items(
                "SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": article_id}],
                enable_cross_partition_query=True,
            ))
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


def get_pending_articles(limit: int = 200) -> list[Article]:
    """Gibt bis zu `limit` PENDING-Artikel zurück (älteste zuerst für FIFO-Retry)."""
    if _use_cosmos():
        query = f"SELECT TOP {int(limit)} * FROM c WHERE c.category = 'PENDING' ORDER BY c.fetched_at ASC"
        try:
            rows = list(_get_container().query_items(query, enable_cross_partition_query=True))
            return [Article.from_cosmos_doc(r) for r in rows]
        except Exception as exc:
            logger.error("Cosmos get_pending_articles failed: %s", exc)
            return []
    else:
        items = [
            doc for doc in _memory_store.values()
            if doc.get("category") == "PENDING"
        ]
        items.sort(key=lambda a: a.get("fetched_at", ""))
        return [Article.from_cosmos_doc(doc) for doc in items[:limit]]


def get_stale_articles(prompt_version: str, limit: int = 500) -> list[Article]:
    """Gibt Artikel zurück, deren prompt_version nicht der aktuellen entspricht."""
    if _use_cosmos():
        query = f"SELECT TOP {int(limit)} * FROM c WHERE c.prompt_version != @pv AND c.category != 'OFF_TOPIC'"
        try:
            rows = list(_get_container().query_items(
                query,
                parameters=[{"name": "@pv", "value": prompt_version}],
                enable_cross_partition_query=True,
            ))
            return [Article.from_cosmos_doc(r) for r in rows]
        except Exception as exc:
            logger.error("Cosmos get_stale_articles failed: %s", exc)
            return []
    else:
        items = [
            doc for doc in _memory_store.values()
            if doc.get("prompt_version", "") != prompt_version
            and doc.get("category") != "OFF_TOPIC"
        ]
        return [Article.from_cosmos_doc(doc) for doc in items[:limit]]


# ---------------------------------------------------------------------------
# Löschen
# ---------------------------------------------------------------------------

def delete_articles_older_than(cutoff_iso: str) -> int:
    """Löscht alle Artikel mit fetched_at < cutoff_iso."""
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
