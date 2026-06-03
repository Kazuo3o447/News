"""
Groq KI-Klassifizierung für News-Artikel.
Kategorien: KRITISCH | NORMAL | DUMP
Plattformen: windows | apple | android | cross
"""
import json
import logging
import time

from groq import Groq

from config.settings import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du klassifizierst IT-Admin-News. Antworte AUSSCHLIESSLICH mit JSON.

KRITISCH = Sofort-Handlungsbedarf auf IRGENDEINER Plattform:
- Aktiv ausgenutzte Sicherheitslücken / Zero-Days / 0-Days
- Kritische CVEs (CVSS >= 9.0 oder aktiv in-the-wild)
- OOB/Notfall-Patches, Rapid Security Response (Apple oder Windows oder Android)
- Cloud-/Identity-Ausfälle (Entra/M365/Workspace/iCloud für Business)
- Ransomware-Wellen, aktive Angriffskampagnen

NORMAL = Admin-relevant, aber nicht eilig:
- OS-/App-Updates und Feature-Releases (Windows, macOS, iOS, Android Enterprise)
- MDM-Funktionen (Intune, Jamf, Android Enterprise, Samsung Knox)
- Security-Research, Threat-Intel (ohne aktive Exploitierung)
- Compliance (NIS2/DORA), Roadmaps, neue Admin-Tools, Konfigurations-Guides

DUMP = Kein Admin-Wert — PLATTFORMUNABHÄNGIG:
- Consumer-Gerät-Tests/Reviews (auch iOS, macOS, Android – wenn kein Admin-Bezug)
- Gaming, Krypto, Deals/Werbung, Gerüchte/Hardware-Leaks ohne Security-Relevanz
- Allgemeiner KI-Hype ohne Enterprise-Bezug
- Wirtschafts-/Startup-News ohne Security/IT-Admin-Relevanz
→ WICHTIG: Plattform allein macht KEINEN DUMP.
  „iOS 18.5 schließt aktiv ausgenutzte Lücke" = KRITISCH/apple
  „iPhone 17 Testbericht" = DUMP/cross

platform = woher der Admin-Handlungsbedarf kommt:
- "windows" = Microsoft (Windows, Azure, M365, Entra, Intune, Exchange, MSRC)
- "apple"   = Apple (macOS, iOS, iPadOS, Jamf, ABM, Apple MDM, Rapid Security Response)
- "android" = Android (Android Enterprise, Knox, Samsung SMR, Zero-Touch, NowSecure)
- "cross"   = betrifft alle Plattformen (M365/Entra, allg. Security, IAM, Cloud-Infra)

Antwortformat für Batch-Anfragen (mehrere Items mit idx):
{"items":[{"idx":0,"criticality":"KRITISCH"|"NORMAL"|"DUMP","platform":"windows"|"apple"|"android"|"cross","tags":["tag1","tag2"],"reason":"<max 90 Zeichen deutsch>"},...]}

BEISPIELE (Few-Shot):

[windows/KRITISCH]
Titel: "Microsoft Patches Critical Zero-Day in MSHTML Under Active Exploitation"
→ {"idx":0,"criticality":"KRITISCH","platform":"windows","tags":["zero-day","mshtml","rce","patch"],"reason":"Aktiv ausgenutzte Zero-Day-Lücke in Windows MSHTML – sofortiger Patch nötig"}

[windows/NORMAL]
Titel: "Microsoft Intune adds new app deployment policy for Windows 11 22H2"
→ {"idx":1,"criticality":"NORMAL","platform":"windows","tags":["intune","mdm","windows11","policy"],"reason":"Neues MDM-Feature für Intune – admin-relevant, kein Sofortbedarf"}

[apple/KRITISCH]
Titel: "Apple releases Rapid Security Response for actively exploited WebKit flaw"
→ {"idx":2,"criticality":"KRITISCH","platform":"apple","tags":["webkit","rapid-security-response","exploit","ios"],"reason":"Aktiv ausgenutzte WebKit-Lücke – Apple RSR sofort einspielen"}

[apple/NORMAL]
Titel: "Jamf Pro 11.4 released: new Declarative Device Management features for macOS"
→ {"idx":3,"criticality":"NORMAL","platform":"apple","tags":["jamf","ddm","macos","mdm"],"reason":"Neues Jamf-Release mit Admin-Funktionen – relevant für macOS-Flotten"}

[android/KRITISCH]
Titel: "Android Security Bulletin June 2025: Critical RCE in Bluetooth stack, CVSS 9.8"
→ {"idx":4,"criticality":"KRITISCH","platform":"android","tags":["android","bluetooth","rce","cvss-critical"],"reason":"Kritische RCE im Android-Bluetooth – Patching für verwaltete Geräte priorisieren"}

[android/NORMAL]
Titel: "Google expands Android Enterprise Zero-Touch Enrollment to new OEM partners"
→ {"idx":5,"criticality":"NORMAL","platform":"android","tags":["android-enterprise","zero-touch","mdm","oem"],"reason":"Erweiterung des Zero-Touch-Programms – relevant für Android-MDM-Admins"}

[DUMP]
Titel: "iPhone 17 Pro: Leaked renders show new titanium design and periscope lens"
→ {"idx":6,"criticality":"DUMP","platform":"cross","tags":["iphone","leak","hardware"],"reason":"Consumer-Hardware-Gerücht ohne Admin-Relevanz"}"""


_client: Groq | None = None
_VALID_CRITICALITY = {"KRITISCH", "NORMAL", "DUMP"}
_VALID_PLATFORMS   = {"windows", "apple", "android", "cross"}


def _get_client() -> Groq | None:
    global _client
    if not settings.GROQ_API_KEY:
        return None
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def classify_batch(items: list[dict]) -> list[dict]:
    """
    Klassifiziert eine Liste von Artikeln (10–15 Stück) in einem einzigen Groq-Request.

    items = [{"idx": int, "title": str, "source": str, "summary": str}, ...]

    Rückgabe: Liste in gleicher Reihenfolge wie items, jedes Element:
        {"idx": int, "criticality": str, "platform": str, "tags": list[str], "reason": str}

    confidence wird NICHT vom LLM erwartet — der Scheduler leitet sie deterministisch ab.
    """
    client = _get_client()
    if client is None:
        logger.debug("Groq nicht konfiguriert — Batch als NORMAL eingestuft")
        return [
            {
                "idx": item["idx"], "criticality": "NORMAL", "platform": "cross",
                "tags": [], "reason": "Kein Groq API-Key konfiguriert",
            }
            for item in items
        ]

    # Nummerierte Liste für den User-Prompt
    lines = []
    for item in items:
        summary = (item.get("summary") or "")[:280]
        lines.append(
            f"[{item['idx']}] Quelle: {item['source']}\n"
            f"    Titel: {item['title']}\n"
            f"    Summary: {summary}"
        )
    user_prompt = (
        'Klassifiziere folgende Artikel als Batch. Antworte mit {"items":[...]}:\n\n'
        + "\n\n".join(lines)
    )

    for attempt in range(3):
        try:
            response = _get_client().chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=len(items) * 120 + 100,
                response_format={"type": "json_object"},
            )
            raw = json.loads(response.choices[0].message.content)
            llm_items = raw.get("items", [])

            # idx → result-Map aufbauen und validieren
            results: dict[int, dict] = {}
            for entry in llm_items:
                idx = entry.get("idx")
                if idx is None:
                    continue
                criticality = str(entry.get("criticality", "NORMAL")).upper()
                platform    = str(entry.get("platform", "cross")).lower()
                if criticality not in _VALID_CRITICALITY:
                    criticality = "NORMAL"
                if platform not in _VALID_PLATFORMS:
                    platform = "cross"
                tags = [str(t) for t in entry.get("tags", [])[:4]]
                results[int(idx)] = {
                    "idx":         int(idx),
                    "criticality": criticality,
                    "platform":    platform,
                    "tags":        tags,
                    "reason":      str(entry.get("reason", ""))[:120],
                }

            # Fehlende Items mit Fallback auffüllen
            output = []
            for item in items:
                if item["idx"] in results:
                    output.append(results[item["idx"]])
                else:
                    logger.warning("Batch: kein LLM-Ergebnis für idx=%d — Fallback", item["idx"])
                    output.append({
                        "idx":         item["idx"],
                        "criticality": "NORMAL",
                        "platform":    "cross",
                        "tags":        [],
                        "reason":      "Fallback: kein LLM-Ergebnis",
                    })
            return output

        except Exception as exc:
            logger.warning("Groq batch attempt %d failed: %s", attempt + 1, exc)
            time.sleep(2 ** attempt)   # exponential backoff: 1s, 2s, 4s

    logger.error("Groq batch classification failed after 3 attempts — NORMAL fallback")
    return [
        {
            "idx": item["idx"], "criticality": "NORMAL", "platform": "cross",
            "tags": [], "reason": "Klassifizierung fehlgeschlagen",
        }
        for item in items
    ]


def classify_article(title: str, source: str, summary: str) -> dict:
    """
    Klassifiziert einen einzelnen Artikel.
    Dünner Wrapper auf classify_batch() für Rückwärtskompatibilität der Tests.
    Im Produktiv-Scheduler sollte classify_batch direkt verwendet werden.
    """
    result = classify_batch([{"idx": 0, "title": title, "source": source, "summary": summary}])
    item   = result[0]
    return {
        "category":   item["criticality"],
        "platform":   item["platform"],
        "confidence": None,   # confidence wird im Scheduler deterministisch abgeleitet
        "reason":     item["reason"],
        "tags":       item["tags"],
    }
