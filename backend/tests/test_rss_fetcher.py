"""
Unit-Tests für den RSS-Fetcher.
"""
import sys
import types

# feedparser-Stub
fp_stub = types.ModuleType("feedparser")

def _fake_parse(url, agent=None):
    return types.SimpleNamespace(
        bozo=False,
        bozo_exception=None,
        entries=[
            types.SimpleNamespace(
                link="https://example.com/article-1",
                title="Kritische Lücke in Windows 11",
                summary="Eine neue Schwachstelle wurde entdeckt.",
                published_parsed=(2026, 5, 27, 10, 0, 0, 0, 0, 0),
                updated_parsed=None,
            )
        ],
    )

fp_stub.parse = _fake_parse
sys.modules["feedparser"] = fp_stub

import os
os.environ.setdefault("GROQ_API_KEY",           "test")
os.environ.setdefault("AZURE_COSMOS_ENDPOINT",  "https://test.documents.azure.com")
os.environ.setdefault("AZURE_COSMOS_KEY",       "dGVzdA==")

from services.rss_fetcher import fetch_feed  # noqa: E402


def test_fetch_feed_returns_articles():
    feed = {"name": "Test Feed", "url": "https://example.com/rss", "priority": "high"}
    articles = fetch_feed(feed)
    assert len(articles) == 1


def test_fetch_feed_article_fields():
    feed = {"name": "Test Feed", "url": "https://example.com/rss", "priority": "high"}
    articles = fetch_feed(feed)
    a = articles[0]
    assert a["title"]   == "Kritische Lücke in Windows 11"
    assert a["source"]  == "Test Feed"
    assert a["url"]     == "https://example.com/article-1"
    assert a["id"]                     # SHA-256 Hash vorhanden
    assert a["category"] is None       # Noch nicht klassifiziert


def test_fetch_feed_empty_on_error():
    feed = {"name": "Broken Feed", "url": "https://this-will-fail.invalid/rss", "priority": "low"}
    # feedparser gibt bozo=True + keine entries zurück
    import services.rss_fetcher as mod
    import feedparser as fp
    original = fp.parse

    def broken_parse(url, agent=None):
        return types.SimpleNamespace(bozo=True, bozo_exception=Exception("fail"), entries=[])

    fp.parse = broken_parse
    articles = fetch_feed(feed)
    fp.parse = original
    assert articles == []
