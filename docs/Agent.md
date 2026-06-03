# Agent — Groq KI-Klassifizierung

> Groq API · Modell: `openai/gpt-oss-120b` · Stand: Juni 2026 (Copilot-Brief 01)

---

## 1. Aufgabe des Agents

Der Groq-Agent analysiert Headline + Beschreibung jedes eingehenden RSS-Artikels
(**Batch: 12 Artikel pro Request**) und ordnet jeden Artikel zwei Achsen zu:

| Achse | Werte |
|---|---|
| **Kritikalität** | `KRITISCH` / `NORMAL` / `DUMP` |
| **Plattform** | `windows` / `apple` / `android` / `cross` |

| Kategorie | Symbol | Bedeutung |
|---|---|---|
| `KRITISCH` | 🔴 | Sofortiger Handlungsbedarf auf **irgendeiner** Plattform |
| `NORMAL` | 🔵 | Admin-relevant, kein Sofortbedarf |
| `DUMP` | ⚫ | Kein Admin-Wert — plattformunabhängig (Consumer-Reviews, Gaming, Deals …) |

> **DUMP ist plattformunabhängig.** Ein Apple-Artikel ist NICHT DUMP weil er Apple betrifft.
> Er ist DUMP wenn er keinen Admin-Wert hat (z. B. „iPhone 17 Testbericht").

### Vorgelagerte Stufen (LLM-Bypass)

| Stufe | Was passiert |
|---|---|
| **Pre-Filter** | Denylist-Treffer → sofort `OFF_TOPIC`, kein LLM-Call |
| **Regelschicht** | CVE / aktiver Exploit / Advisory-Quelle → `forced_critical=True` |

---

## 2. System-Prompt

```
Du klassifizierst IT-Admin-News. Antworte AUSSCHLIESSLICH mit JSON.

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
```

---

## 3. User-Prompt Template (Batch)

```
Klassifiziere folgende {n} IT-News-Artikel als JSON-Batch:

0 Titel: "{title_0}" | Quelle: "{source_0}" | Beschreibung: "{summary_0[:300]}"
1 Titel: "{title_1}" | Quelle: "{source_1}" | Beschreibung: "{summary_1[:300]}"
...

Antworte mit dem JSON-Batch-Format (items-Array mit idx).
```

---

## 4. Klassifizierungslogik (Beispiele)

### KRITISCH — Beispiele

| Headline | Plattform | Begründung |
|---|---|---|
| `Kritische RCE-Lücke in Windows Server 2022 (CVE-2026-XXXXX)` | `windows` | CVE + RCE = sofortiger Handlungsbedarf |
| `Microsoft Azure AD: Massenausfall in Region West Europe` | `windows` | Produktionsausfall mit Unternehmensimpakt |
| `BSI warnt vor aktiver Ausnutzung von Exchange-Schwachstelle` | `windows` | Behördliche Warnung + aktiver Angriff |
| `Notfall-Patch KB5040442 für Windows 11 verfügbar` | `windows` | Out-of-Band Patch = kritisch |
| `Apple releases Rapid Security Response for actively exploited WebKit flaw` | `apple` | Aktiv ausgenutzte WebKit-Lücke – Apple RSR sofort einspielen |
| `Android Security Bulletin June 2026: Critical RCE in Bluetooth (CVSS 9.8)` | `android` | Kritische RCE – Patching für verwaltete Android-Geräte priorisieren |

### NORMAL — Beispiele

| Headline | Plattform | Begründung |
|---|---|---|
| `Microsoft Copilot erhält neue Sprachfunktionen` | `windows` | Feature-Update, kein Handlungsbedarf |
| `Windows 12 Release für Herbst 2026 erwartet` | `windows` | Roadmap-Information |
| `Heise: Warum Zero Trust im Mittelstand unterschätzt wird` | `cross` | Fachartikel, lesenswert |
| `Azure Cost Management bekommt KI-Empfehlungen` | `windows` | Produktverbesserung |
| `Jamf Pro 11.4: new Declarative Device Management features for macOS` | `apple` | Neues Jamf-Release mit Admin-Funktionen |
| `Google expands Android Enterprise Zero-Touch Enrollment to new OEM partners` | `android` | Erweiterung des Zero-Touch-Programms |

### DUMP — Beispiele

| Headline | Begründung |
|---|---|
| `Microsoft Surface Pro 9 jetzt für 299€ – nur heute!` | Werbung / Deal |
| `[Sponsored] Warum Cloud-Backup Ihre Daten rettet` | Gesponsert |
| `5 Gründe, warum Sie Windows 11 JETZT upgraden sollten` | Click-Bait |
| `Einladung: Unser Webinar zu Microsoft 365 Security` | Event-Promo |
| `iPhone 17 Pro: Leaked renders show new titanium design and periscope lens` | Consumer-Hardware-Gerücht, kein Admin-Bezug |
| `Google Pixel 9a: Hands-on review — Kamera, Akku, Performance` | Consumer-Produkttest, kein Admin-Bezug |

---

## 5. API-Integration (Python)

```python
from groq import Groq
import json

SYSTEM_PROMPT = """..."""  # Siehe Abschnitt 2

def classify_batch(items: list[dict]) -> list[dict]:
    """Klassifiziert 10–12 Artikel in einem Groq-Request."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    lines = [
        f"{i} Titel: \"{it['title']}\" | Quelle: \"{it['source']}\" "
        f"| Beschreibung: \"{it.get('summary', '')[:300]}\""
        for i, it in enumerate(items)
    ]
    user_prompt = (
        f"Klassifiziere folgende {len(items)} IT-News-Artikel als JSON-Batch:\n\n"
        + "\n".join(lines)
    )

    response = client.chat.completions.create(
        model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    data = json.loads(response.choices[0].message.content)
    return data.get("items", [])
```

---

## 6. Konfigurationsparameter

| Parameter | Wert | Begründung |
|---|---|---|
| `model` | `openai/gpt-oss-120b` | Höhere Qualität bei Cross-Platform-News; via `GROQ_MODEL` Env-Var überschreibbar |
| `temperature` | `0.1` | Deterministische Klassifizierung |
| `max_tokens` | `150` | JSON-Antwort ist kurz |
| `response_format` | `json_object` | Garantiert valides JSON |
| Fallback-Kategorie | `NORMAL` | Im Fehlerfall lieber zeigen als verbergen |

---

## 7. Batch-Verarbeitung

Um Kosten zu optimieren, werden Artikel in Batches klassifiziert:

- **Batch-Größe**: 12 Artikel pro Groq-Request (`GROQ_CHUNK_SIZE`)
- **Rate Limit**: 1.0 s Pause zwischen Batches (`THROTTLE_SECONDS`); Batching reduziert RPM-Verbrauch drastisch
- **Cache**: Bereits klassifizierte URLs werden nicht erneut verarbeitet
- **Retry**: Bei API-Fehler: 3 Versuche mit exponential backoff

---

## 8. Qualitätssicherung

### Confidence-Derivation (deterministisch)

Confidence wird **nicht** vom LLM geliefert, sondern im Scheduler deterministisch berechnet:

| Bedingung | Confidence |
|---|---|
| `forced_critical=True` (CVE / aktiver Exploit / Advisory-Quelle) | `1.0` |
| Rule-Plattform == LLM-Plattform | `0.9` |
| Plattform-Mismatch zwischen Regelschicht und LLM | `0.6` |

### Manuelle Korrekturen

Nutzer können Artikel manuell umkategorisieren. Diese Korrekturen werden
geloggt und können zukünftig für Prompt-Verbesserungen verwendet werden.

---

## 9. Kosten-Schätzung (Groq)

| Szenario | Artikel/Tag | Tokens/Artikel | Tokens/Monat | Kosten/Monat |
|---|---|---|---|---|
| Klein | 200 | ~300 | 1,8 Mio | ~$0.05 |
| Mittel | 500 | ~300 | 4,5 Mio | ~$0.13 |
| Groß | 2.000 | ~300 | 18 Mio | ~$0.54 |

> Groq llama-3.1-70b: ca. $0.59 / 1 Mio. Input-Tokens (Stand Mai 2026)

---

## 10. Weiterentwicklung (Roadmap)

- [ ] **Tag-Extraktion**: Neben Kategorie auch Tags extrahieren (z.B. `azure`, `security`, `windows`)
- [ ] **Zusammenfassung**: Kurze deutsche Zusammenfassung für englische Artikel generieren
- [ ] **Trend-Erkennung**: Clustering ähnlicher Meldungen zum selben Ereignis
- [ ] **Relevanz-Score**: Individueller Score basierend auf konfigurierten Interessen-Tags
