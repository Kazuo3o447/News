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
        # Simuliert eine KRITISCH-Antwort
        return _FakeCompletion(json.dumps({
            "category": "KRITISCH",
            "confidence": 0.95,
            "reason": "Sicherheitslücke erkannt",
        }))

groq_stub.Groq = _FakeClient
sys.modules["groq"] = groq_stub

# Settings-Stub
import os
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("GROQ_MODEL",   "llama-3.1-70b-versatile")

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


def test_classify_confidence_range():
    result = classify_article("Windows RCE-Lücke", "Heise", "Kritische Sicherheitslücke entdeckt")
    assert 0.0 <= result["confidence"] <= 1.0


def test_classify_fallback_on_low_confidence(monkeypatch):
    """Confidence < 0.60 → Kategorie wird auf NORMAL gesetzt."""
    def fake_create(**kwargs):
        return _FakeCompletion(json.dumps({
            "category": "KRITISCH",
            "confidence": 0.3,
            "reason": "Unsicher",
        }))

    import services.groq_classifier as mod
    monkeypatch.setattr(mod._get_client().chat.completions, "create", fake_create)
    # Neuen Client erzwingen
    mod._client = None
    result = classify_article("Test", "Test", "Test")
    assert result["category"] == "NORMAL"
