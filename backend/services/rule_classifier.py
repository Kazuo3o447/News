"""
Deterministische Regelschicht — läuft VOR dem LLM.

Ziel:
- Harte Security-Signale (CVE, aktive Exploits, kritische CVSS-Werte …) zuverlässig
  als KRITISCH kennzeichnen, ohne ein LLM zu benötigen.
- Plattform-Prior aus der Feed-Quelle ableiten (Source→Platform-Map).

Gibt forced_critical=True zurück, wenn ein oder mehrere Signale zutreffen.
Der Scheduler lässt forced_critical über das LLM-Ergebnis gewinnen (Merge-Regeln).
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Source → Platform-Mapping
# ---------------------------------------------------------------------------
_SOURCE_TO_PLATFORM: dict[str, str] = {
    # Windows / Microsoft
    "M365 Message Center":      "windows",
    "Azure Blog":               "windows",
    "Microsoft Security Blog":  "windows",
    "Microsoft Tech Community": "windows",
    "Windows Blog":             "windows",
    "Microsoft 365 Blog":       "windows",
    "MSRC":                     "windows",
    # Apple
    "Jamf Blog":                "apple",
    "Apple Developer Releases": "apple",
    "Intego Mac Security":      "apple",
    "Mr. Macintosh":            "apple",
    "Eclectic Light":           "apple",
    # Android
    "Android Developers":       "android",
    "NowSecure":                "android",
    "Android Security Bulletin":"android",
    "Samsung SMR":              "android",
    # Cross (plattformübergreifende Security/IT)
    "Google Workspace Updates": "cross",
    "BleepingComputer":         "cross",
    "Krebs on Security":        "cross",
    "The Hacker News":          "cross",
    "Heise Security":           "cross",
    "BSI Warnungen":            "cross",
    "CISA Advisories":          "cross",
    "Heise Developer":          "cross",
    "iX":                       "cross",
}

# Advisory-Quellen → immer forced_critical
_ADVISORY_SOURCES = {"MSRC", "BSI Warnungen", "CISA Advisories"}

# Regex-Muster für CVE-IDs
_RE_CVE = re.compile(r"cve-\d{4}-\d{4,}", re.IGNORECASE)

# Regex für CVSS-Wert — extrahiert die Zahl nach "CVSS" oder "CVSS:3.x"
_RE_CVSS = re.compile(r"cvss[:\s]?v?\d?[:\s]?(\d{1,2}\.\d)", re.IGNORECASE)

# Phrasen für aktive Ausnutzung (case-insensitive, als lowercase-Strings)
_ACTIVE_EXPLOIT_PHRASES: tuple[str, ...] = (
    "actively exploited",
    "aktiv ausgenutzt",
    "in the wild",
    "zero-day",
    "zero day",
    "0-day",
    "out-of-band",
    "out of band",
    "emergency update",
    "notfall-patch",
    "rapid security response",
    "under attack",
    "wird angegriffen",
)


def apply_rules(title: str, summary: str, source: str) -> dict:
    """
    Führt die deterministische Regelschicht aus.

    Parameter:
        title   – Artikeltitel
        summary – Artikelzusammenfassung
        source  – Name der Feed-Quelle (muss mit _SOURCE_TO_PLATFORM-Keys übereinstimmen)

    Rückgabe::
        {
            "forced_critical": bool,
            "platform_hint":   str | None,   # aus Source-Map; None wenn unbekannte Quelle
            "signals":         list[str],    # ausgelöste Regel-Signale (für Logging)
            "cve_ids":         list[str],    # alle gefundenen CVE-IDs (uppercase, dedupliziert)
            "cvss":            float | None, # höchster gefundener CVSS-Wert
        }
    """
    text_lower = f" {(title or '').lower()} {(summary or '').lower()} "
    signals: list[str] = []

    # --- Regel 1: CVE-IDs extrahieren ---
    cve_matches = _RE_CVE.findall(text_lower)
    cve_ids: list[str] = sorted({m.upper() for m in cve_matches})
    if cve_ids:
        signals.append("cve")

    # --- Regel 2: Höchsten CVSS-Wert extrahieren ---
    cvss: float | None = None
    for match in _RE_CVSS.finditer(text_lower):
        try:
            val = float(match.group(1))
            if cvss is None or val > cvss:
                cvss = val
            if val >= 9.0:
                signals.append("cvss_critical")
                break
        except ValueError:
            pass

    # --- Regel 3: Phrasen für aktive Ausnutzung ---
    for phrase in _ACTIVE_EXPLOIT_PHRASES:
        if phrase in text_lower:
            signals.append("active_exploit")
            break

    # --- Regel 4: Android Security Bulletin + "critical" ---
    if "android security bulletin" in text_lower and (
        "critical" in text_lower or "kritisch" in text_lower
    ):
        signals.append("android_critical")

    # --- Regel 5: Samsung SMR + "critical" ---
    if "smr" in text_lower and "critical" in text_lower:
        signals.append("samsung_critical")

    # --- Regel 6: Advisory-Quelle → immer kritisch ---
    if source in _ADVISORY_SOURCES:
        signals.append("advisory_source")

    platform_hint = _SOURCE_TO_PLATFORM.get(source)

    return {
        "forced_critical": len(signals) > 0,
        "platform_hint":   platform_hint,
        "signals":         signals,
        "cve_ids":         cve_ids,
        "cvss":            cvss,
    }
