"""
Unit-Tests für den Groq-Klassifizierer.
Nutzt monkeypatching — kein echter Groq-API-Call nötig.
"""
import json
import sys
import types
import pytest

# ---------------------------------------------------------------------------
# Minimal-Stub für das groq-Paket (kein echter API-Key nötig)
# ---------------------------------------------------------------------------
groq_stub = types.ModuleType("groq")

class _FakeCompletion:
    def __init__(self, content):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]

class _FakeClient:
    def __init__(self, **_):
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        # Simuliert eine KRITISCH-Antwort im neuen Batch-Format
        return _FakeCompletion(json.dumps({
            "items": [
                {
                    "idx": 0,
                    "criticality": "KRITISCH",
                    "platform": "windows",
                    "tags": ["rce", "windows"],
                    "reason": "Sicherheitslücke erkannt",
                }
            ]
        }))

groq_stub.Groq = _FakeClient
sys.modules["groq"] = groq_stub

# Settings-Stub
import os
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("GROQ_MODEL",   "openai/gpt-oss-120b")

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
from services.groq_classifier import classify_article  # noqa: E402


def test_classify_returns_expected_keys():
    result = classify_article("Windows RCE-Lücke", "Heise", "Kritische Sicherheitslücke entdeckt")
    assert "category"   in result
    assert "confidence" in result
    assert "reason"     in result


def test_classify_category_valid():
    result = classify_article("Windows RCE-Lücke", "Heise", "Kritische Sicherheitslücke entdeckt")
    assert result["category"] in ("KRITISCH", "NORMAL", "DUMP")


def test_classify_confidence_is_none():
    """confidence wird nicht mehr vom LLM bestimmt, sondern im Scheduler abgeleitet."""
    result = classify_article("Windows RCE-Lücke", "Heise", "Kritische Sicherheitslücke entdeckt")
    assert result["confidence"] is None


def test_classify_returns_platform():
    result = classify_article("Windows RCE-Lücke", "Heise", "Kritische Sicherheitslücke entdeckt")
    assert result.get("platform") in ("windows", "apple", "android", "cross")


def test_classify_returns_tags():
    result = classify_article("Windows RCE-Lücke", "Heise", "Kritische Sicherheitslücke entdeckt")
    assert isinstance(result.get("tags"), list)
