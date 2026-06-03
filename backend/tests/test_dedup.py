"""
Unit-Tests für services/dedup.py
"""
import os
import sys

os.environ.setdefault("GROQ_API_KEY",          "test")
os.environ.setdefault("AZURE_COSMOS_ENDPOINT", "https://test.documents.azure.com")
os.environ.setdefault("AZURE_COSMOS_KEY",      "dGVzdA==")

from api.models.article import Article
from services.dedup import cluster_key


def _make_article(**kwargs) -> Article:
    defaults = dict(
        id="test-id",
        title="Test Article",
        url="https://example.com/1",
        source="TestSource",
        category="NORMAL",
        platform="windows",
        published_at="2026-01-01T10:00:00+00:00",
        summary="",
        cve_ids=[],
        cvss=None,
        cluster_id=None,
    )
    defaults.update(kwargs)
    return Article(**defaults)


def test_same_cve_same_cluster():
    """Drei Artikel aus verschiedenen Quellen mit gleichem CVE erhalten denselben cluster_id."""
    cve = "CVE-2026-11111"
    a1 = _make_article(id="id1", title="MS patches CVE-2026-11111",         source="MSRC",    cve_ids=[cve])
    a2 = _make_article(id="id2", title="Critical flaw CVE-2026-11111 found", source="BleepComp", cve_ids=[cve])
    a3 = _make_article(id="id3", title="Update for CVE-2026-11111 released", source="Heise",   cve_ids=[cve])

    k1 = cluster_key(a1, [])
    k2 = cluster_key(a2, [a1])
    k3 = cluster_key(a3, [a1, a2])

    assert k1 == k2 == k3 == cve.upper()


def test_different_cve_different_cluster():
    """Zwei Artikel mit unterschiedlichen CVEs bekommen unterschiedliche cluster_ids."""
    a1 = _make_article(id="id1", title="Patch for CVE-2026-11111", cve_ids=["CVE-2026-11111"])
    a2 = _make_article(id="id2", title="Fix for CVE-2026-22222",   cve_ids=["CVE-2026-22222"])

    k1 = cluster_key(a1, [])
    k2 = cluster_key(a2, [a1])

    assert k1 != k2


def test_no_cve_similar_title_same_cluster():
    """Zwei Artikel ohne CVE, aber sehr ähnlichen Titeln → selbe cluster_id."""
    a1 = _make_article(id="id1", title="Windows 11 critical update released")
    a2 = _make_article(id="id2", title="Windows 11 critical update released")  # exakt gleich

    k1 = cluster_key(a1, [])
    # a1 schon mit cluster_id versehen (wie scheduler es tut)
    a1.cluster_id = k1
    k2 = cluster_key(a2, [a1])

    assert k1 == k2


def test_no_cve_different_title_different_cluster():
    """Zwei Artikel ohne CVE und verschiedenen Titeln → unterschiedliche cluster_ids."""
    a1 = _make_article(id="id1", title="Apple releases security update for macOS")
    a2 = _make_article(id="id2", title="Android kernel vulnerability patched")

    k1 = cluster_key(a1, [])
    a1.cluster_id = k1
    k2 = cluster_key(a2, [a1])

    assert k1 != k2
