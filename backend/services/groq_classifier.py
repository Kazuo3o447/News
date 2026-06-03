"""
Groq KI-Klassifizierung für News-Artikel.
Kategorien: KRITISCH | NORMAL | DUMP
"""
import json
import logging
import os
import time

from groq import Groq

from config.settings import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du klassifizierst IT-News für ein Microsoft-/Security-Team. Antworte NUR mit JSON.

KRITISCH = Sofort-Handlungsbedarf: CVEs, Zero-Days, aktive Exploits, MS-Patch-Tuesday-OOB,
Azure/M365/Entra-Ausfälle, Ransomware-Wellen, kritische Lücken in Enterprise-Software.

NORMAL = Relevant aber nicht eilig: Microsoft-Produkte (Azure, M365, Defender, Intune,
Copilot, Entra, Exchange, Windows-Server), Security-Research, Threat-Intel, Kubernetes,
DevSecOps, Identity, NIS2/DORA, MS-Roadmap.

DUMP = Für uns irrelevant (auch wenn tech-nah): Consumer-Gadgets, iPhone/Android-Reviews,
Gaming, E-Autos, Krypto, Startup-/Wirtschafts-News, Werbung/Deals/Anzeigen, allgemeiner
KI-Hype ohne Enterprise-Bezug. Im Zweifel → DUMP.

Format: {"category":"KRITISCH"|"NORMAL"|"DUMP","confidence":0.0-1.0,"reason":"<max 100 Z. dt.>"}"""


_client: Groq | None = None


def _get_client() -> Groq | None:
    global _client
    if not settings.GROQ_API_KEY:
        return None
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def classify_article(title: str, source: str, summary: str) -> dict:
    """
    Klassifiziert einen einzelnen Artikel via Groq.
    Gibt dict mit 'category', 'confidence', 'reason' zurück.
    Fallback bei Fehler oder fehlendem Key: category=NORMAL, confidence=0.0
    """
    client = _get_client()
    if client is None:
        logger.debug("Groq nicht konfiguriert — Artikel wird als NORMAL eingestuft: %s", title)
        return {"category": "NORMAL", "confidence": 0.0, "reason": "Kein Groq API-Key konfiguriert"}
    user_prompt = (
        f"Titel: {title}\n"
        f"Quelle: {source}\n"
        f"Beschreibung: {summary[:300]}"
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=100,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            category   = result.get("category", "NORMAL").upper()
            confidence = float(result.get("confidence", 0.5))
            reason     = result.get("reason", "")

            if category not in ("KRITISCH", "NORMAL", "DUMP"):
                category = "NORMAL"
            # Confidence wird nicht mehr auf NORMAL gemappt — DUMP soll DUMP bleiben.

            return {"category": category, "confidence": confidence, "reason": reason}

        except Exception as exc:
            logger.warning("Groq classify attempt %d failed: %s", attempt + 1, exc)
            time.sleep(2 ** attempt)   # exponential backoff: 1s, 2s, 4s

    logger.error("Groq classification failed after 3 attempts — falling back to NORMAL")
    return {"category": "NORMAL", "confidence": 0.0, "reason": "Klassifizierung fehlgeschlagen"}
