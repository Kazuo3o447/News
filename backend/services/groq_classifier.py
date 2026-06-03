"""
Groq KI-Klassifizierung für News-Artikel.
Kategorien: KRITISCH | NORMAL | DUMP
Plattformen: windows | apple | android | cross

B4: Zwei Modelle — GROQ_MODEL_CLASSIFY (schnell, 8b) für Batch-Klassifizierung,
                    GROQ_MODEL_SUMMARY  (stark, 120b) für KRITISCH TL;DR.
B5: ENABLE_CRITICAL_TLDR default True; summarize_critical() als separater Call.
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
- Azure-Outages / Dienstunterbrechungen in Produktionsregionen
- Entra ID / AAD Authentifizierungsausfälle

NORMAL = Admin-relevant, aber nicht eilig:
- OS-/App-Updates und Feature-Releases (Windows, macOS, iOS, Android Enterprise)
- MDM-Funktionen (Intune, Jamf, Android Enterprise, Samsung Knox)
- Security-Research, Threat-Intel (ohne aktive Exploitierung)
- Compliance (NIS2/DORA), Roadmaps, neue Admin-Tools, Konfigurations-Guides
- M365 Message Center Roadmap-Einträge (MC......) ohne Sicherheitsbezug
- Azure-Feature-Updates, neue bedingte Zugriffs-Vorlagen

DUMP = Kein Admin-Wert — PLATTFORMUNABHÄNGIG:
- Consumer-Gerät-Tests/Reviews (auch iOS, macOS, Android – wenn kein Admin-Bezug)
- Gaming, Krypto, Deals/Werbung, Gerüchte/Hardware-Leaks ohne Security-Relevanz
- Allgemeiner KI-Hype ohne Enterprise-Bezug
- Wirtschafts-/Startup-News ohne Security/IT-Admin-Relevanz
→ WICHTIG: Plattform allein macht KEINEN DUMP.
  „iOS 18.5 schließt aktiv ausgenutzte Lücke" = KRITISCH/apple
  „iPhone 17 Testbericht" = DUMP/cross

platform = woher der Admin-Handlungsbedarf kommt:
- "windows" = Microsoft (Windows, Azure, M365, Entra, Intune, Exchange, MSRC, Teams)
- "apple"   = Apple (macOS, iOS, iPadOS, Jamf, ABM, Apple MDM, Rapid Security Response)
- "android" = Android (Android Enterprise, Knox, Samsung SMR, Zero-Touch, NowSecure)
- "cross"   = betrifft alle Plattformen (allg. Security, IAM, Cloud-Infra ohne MS-spezifisch)

Antwortformat für Batch-Anfragen (mehrere Items mit idx):
{"items":[{"idx":0,"criticality":"KRITISCH"|"NORMAL"|"DUMP","platform":"windows"|"apple"|"android"|"cross","tags":["tag1","tag2"],"reason":"<max 90 Zeichen deutsch>"},...]}

BEISPIELE (Few-Shot):

[windows/KRITISCH]
Titel: "Microsoft Patches Critical Zero-Day in MSHTML Under Active Exploitation"
→ {"idx":0,"criticality":"KRITISCH","platform":"windows","tags":["zero-day","mshtml","rce","patch"],"reason":"Aktiv ausgenutzte Zero-Day-Lücke in Windows MSHTML – sofortiger Patch nötig"}

[windows/KRITISCH — Azure Outage]
Titel: "Azure outage: service degradation affecting West Europe — authentication failures"
→ {"idx":1,"criticality":"KRITISCH","platform":"windows","tags":["azure","outage","authentication"],"reason":"Azure-Ausfall in West Europe mit Auth-Auswirkungen – Incident-Status prüfen"}

[windows/KRITISCH — Entra ID]
Titel: "Entra ID sign-in failures reported across multiple tenants in EU regions"
→ {"idx":2,"criticality":"KRITISCH","platform":"windows","tags":["entra","aad","authentication","outage"],"reason":"Entra ID Authentifizierungsausfall – betroffene Tenants sofort prüfen"}

[windows/NORMAL — M365 Message Center]
Titel: "MC123456: Upcoming changes to SharePoint site creation permissions in M365"
→ {"idx":3,"criticality":"NORMAL","platform":"windows","tags":["m365","sharepoint","mc","roadmap"],"reason":"M365-Roadmap-Änderung bei SharePoint-Berechtigungen – rechtzeitig planen"}

[windows/NORMAL]
Titel: "Microsoft Intune adds new app deployment policy for Windows 11 22H2"
→ {"idx":4,"criticality":"NORMAL","platform":"windows","tags":["intune","mdm","windows11","policy"],"reason":"Neues MDM-Feature für Intune – admin-relevant, kein Sofortbedarf"}

[apple/KRITISCH]
Titel: "Apple releases Rapid Security Response for actively exploited WebKit flaw"
→ {"idx":5,"criticality":"KRITISCH","platform":"apple","tags":["webkit","rapid-security-response","exploit","ios"],"reason":"Aktiv ausgenutzte WebKit-Lücke – Apple RSR sofort einspielen"}

[apple/NORMAL]
Titel: "Jamf Pro 11.4 released: new Declarative Device Management features for macOS"
→ {"idx":6,"criticality":"NORMAL","platform":"apple","tags":["jamf","ddm","macos","mdm"],"reason":"Neues Jamf-Release mit Admin-Funktionen – relevant für macOS-Flotten"}

[android/KRITISCH]
Titel: "Android Security Bulletin June 2025: Critical RCE in Bluetooth stack, CVSS 9.8"
→ {"idx":7,"criticality":"KRITISCH","platform":"android","tags":["android","bluetooth","rce","cvss-critical"],"reason":"Kritische RCE im Android-Bluetooth – Patching für verwaltete Geräte priorisieren"}

[android/NORMAL]
Titel: "Google expands Android Enterprise Zero-Touch Enrollment to new OEM partners"
→ {"idx":8,"criticality":"NORMAL","platform":"android","tags":["android-enterprise","zero-touch","mdm","oem"],"reason":"Erweiterung des Zero-Touch-Programms – relevant für Android-MDM-Admins"}

[DUMP]
Titel: "iPhone 17 Pro: Leaked renders show new titanium design and periscope lens"
→ {"idx":9,"criticality":"DUMP","platform":"cross","tags":["iphone","leak","hardware"],"reason":"Consumer-Hardware-Gerücht ohne Admin-Relevanz"}"""

TLDR_SYSTEM_PROMPT = """Du bist IT-Admin-Assistent. Schreibe für jeden KRITISCH-Artikel eine kurze Handlungszeile auf Deutsch.
Maximal 140 Zeichen. Fokus: WAS MUSS DER ADMIN TUN — nicht was passiert ist.
Beispiele:
  Gut: "Exchange on-prem betroffen — OOB-Patch KB5040442 sofort einspielen, kein Workaround."
  Gut: "Entra ID Auth-Ausfall EU — Incident MC987654 tracken, Fallback-Auth prüfen."
  Gut: "Android Bluetooth RCE (CVSS 9.8) — Juni-Bulletin pushen, Jamf/Intune-Policy erzwingen."
  Schlecht: "Eine kritische Lücke wurde entdeckt." (keine Handlung)
Antworte AUSSCHLIESSLICH mit JSON: {"items":[{"idx":0,"tldr":"<max 140 Zeichen>"},...]}"""


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
    Klassifiziert eine Liste von Artikeln in einem einzigen Groq-Request.
    B4: nutzt GROQ_MODEL_CLASSIFY (schnelles 8b-Modell).

    items = [{"idx": int, "title": str, "source": str, "summary": str}, ...]
    Rückgabe: Liste in gleicher Reihenfolge.
    """
    client = _get_client()
    if client is None:
        logger.debug("Groq nicht konfiguriert — Batch als NORMAL eingestuft")
        return [
            {
                "idx": item["idx"], "criticality": "NORMAL", "platform": "cross",
                "tags": [], "reason": "Kein Groq API-Key konfiguriert", "tldr": "",
            }
            for item in items
        ]

    lines = []
    for item in items:
        summary = (item.get("summary") or "")[:280]
        lines.append(
            f"[{item['idx']}] Quelle: {item['source']}\n"
            f"    Titel: {item['title']}\n"
            f"    Summary: {summary}"
        )

    user_prompt = (
        f'Klassifiziere folgende Artikel als Batch. Antworte mit {{"items":[...]}}.\n\n'
        + "\n\n".join(lines)
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL_CLASSIFY,   # B4: schnelles Modell
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=len(items) * 100 + 100,
                response_format={"type": "json_object"},
            )
            raw = json.loads(response.choices[0].message.content)
            llm_items = raw.get("items", [])

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
                    "tldr":        "",  # TL;DR kommt aus summarize_critical, nicht aus classify_batch
                }

            output = []
            for item in items:
                if item["idx"] in results:
                    output.append(results[item["idx"]])
                else:
                    logger.warning("Batch: kein LLM-Ergebnis für idx=%d — Fallback", item["idx"])
                    output.append({
                        "idx":         item["idx"],
                        "criticality": "PENDING",
                        "platform":    "cross",
                        "tags":        [],
                        "reason":      "Fallback: kein LLM-Ergebnis",
                        "tldr":        "",
                    })
            return output

        except Exception as exc:
            logger.warning("Groq classify attempt %d failed: %s", attempt + 1, exc)
            time.sleep(2 ** attempt)

    logger.error("Groq classify failed after 3 attempts — PENDING fallback")
    return [
        {
            "idx": item["idx"], "criticality": "PENDING", "platform": "cross",
            "tags": [], "reason": "Klassifizierung fehlgeschlagen nach 3 Versuchen", "tldr": "",
        }
        for item in items
    ]


def summarize_critical(articles) -> dict[str, str]:
    """
    B5: Generiert deutsche Handlungszeilen (TL;DR) für KRITISCH-Artikel.
    Nutzt GROQ_MODEL_SUMMARY (starkes Modell).
    Gibt dict[article_id -> tldr_str] zurück.
    Wird nur für KRITISCH aufgerufen (Kostenkontrolle).
    """
    if not settings.ENABLE_CRITICAL_TLDR:
        return {}

    client = _get_client()
    if not client or not articles:
        return {}

    items = []
    for i, a in enumerate(articles):
        title   = a.title if hasattr(a, "title") else a.get("title", "")
        summary = (a.summary if hasattr(a, "summary") else a.get("summary", "") or "")[:300]
        source  = a.source if hasattr(a, "source") else a.get("source", "")
        items.append({"idx": i, "title": title, "source": source, "summary": summary})

    lines = [
        f"[{it['idx']}] Quelle: {it['source']} | Titel: {it['title']} | {it['summary']}"
        for it in items
    ]
    user_prompt = 'Erstelle Handlungszeilen für folgende KRITISCH-Artikel:\n\n' + "\n".join(lines)

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL_SUMMARY,
            messages=[
                {"role": "system", "content": TLDR_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=len(articles) * 60 + 50,
            response_format={"type": "json_object"},
        )
        raw = json.loads(response.choices[0].message.content)
        result: dict[str, str] = {}
        for entry in raw.get("items", []):
            idx  = entry.get("idx")
            tldr = str(entry.get("tldr", ""))[:140]
            if idx is not None and 0 <= int(idx) < len(articles):
                a = articles[int(idx)]
                aid = a.id if hasattr(a, "id") else a.get("id", "")
                result[aid] = tldr
        logger.info("summarize_critical: %d TL;DRs generiert", len(result))
        return result

    except Exception as exc:
        logger.warning("summarize_critical failed: %s", exc)
        return {}


def classify_article(title: str, source: str, summary: str) -> dict:
    """
    Klassifiziert einen einzelnen Artikel.
    Dünner Wrapper auf classify_batch() für Rückwärtskompatibilität der Tests.
    """
    result = classify_batch([{"idx": 0, "title": title, "source": source, "summary": summary}])
    item   = result[0]
    return {
        "category":   item["criticality"],
        "platform":   item["platform"],
        "confidence": None,
        "reason":     item["reason"],
        "tags":       item["tags"],
    }


