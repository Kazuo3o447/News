"""
Pydantic-Datenmodell für einen News-Artikel.
Wird sowohl für API-Responses als auch als Cosmos DB-Dokument verwendet.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


Category = Literal["KRITISCH", "NORMAL", "DUMP", "OFF_TOPIC"]
Platform = Literal["windows", "apple", "android", "cross"]


class Article(BaseModel):
    id: str = Field(..., description="SHA-256 Hash der Artikel-URL (32 Zeichen)")
    title: str
    summary: str = ""
    url: str
    source: str
    published_at: str
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # KI-Klassifizierung (None = noch nicht klassifiziert)
    category: Category | None = None
    platform: Platform | None = None   # NEU: Plattform-Dimension
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    classification_reason: str = ""
    tags: list[str] = []
    topics: list[str] = []      # Server-seitig erkannte Topic-Keys (security/microsoft/…)

    def to_cosmos_doc(self) -> dict:
        """Serialisiert den Artikel als Cosmos DB Dokument."""
        doc = self.model_dump()
        doc["category"] = doc["category"] or "NORMAL"
        return doc

    @classmethod
    def from_cosmos_doc(cls, doc: dict) -> "Article":
        doc.pop("_rid",  None)
        doc.pop("_self", None)
        doc.pop("_etag", None)
        doc.pop("_ts",   None)
        doc.pop("_attachments", None)
        return cls(**doc)

    def to_cosmos_doc(self) -> dict:
        """Serialisiert den Artikel als Cosmos DB Dokument."""
        doc = self.model_dump()
        doc["category"] = doc["category"] or "NORMAL"
        return doc

    @classmethod
    def from_cosmos_doc(cls, doc: dict) -> "Article":
        doc.pop("_rid",  None)
        doc.pop("_self", None)
        doc.pop("_etag", None)
        doc.pop("_ts",   None)
        doc.pop("_attachments", None)
        return cls(**doc)
