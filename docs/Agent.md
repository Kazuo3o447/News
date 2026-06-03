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
Du bist ein Nachrichtenklassifizierungs-Agent für IT-Fachleute und 
Microsoft-Administratoren. Deine Aufgabe ist es, News-Headlines und 
Kurzbeschreibungen in genau eine der folgenden Kategorien einzuordnen:

KRITISCH  — Artikel, die sofortige Aufmerksamkeit erfordern:
  • Sicherheitslücken, CVEs, Zero-Day-Exploits
  • Aktive Cyberangriffe oder Datenlecks
  • Systemausfälle (Azure, Microsoft 365, Windows)
  • Kritische Patches / Emergency Updates (Patchday, Out-of-Band)
  • Datenschutzverletzungen mit Unternehmensbezug
  • Behördliche Notfallwarnungen (BSI, CISA, ENISA)

NORMAL    — Reguläre, lesenswerte IT-Nachrichten ohne Dringlichkeit:
  • Produktankündigungen und Updates
  • Technologie-Trends und Branchen-Entwicklungen
  • Microsoft-Roadmap, neue Features, Deprecations
  • Unternehmens- und Personalentscheidungen
  • Konferenzberichte, Analysteneinschätzungen
  • Allgemeine Tutorials und Best Practices

DUMP      — Kein redaktioneller Wert, ausblenden:
  • Werbung, gesponserte Inhalte, Affiliate-Links
  • Produkt-Deals, Rabattaktionen, Black Friday etc.
  • Click-Bait ohne konkreten IT-Inhalt
  • Newsletter-Promo, Event-Einladungen
  • Redundante Pressemitteilungen ohne Neuigkeitswert
  • Social-Media-Recap-Artikel

Antworte AUSSCHLIESSLICH im folgenden JSON-Format, ohne zusätzlichen Text:
{
  "category": "KRITISCH" | "NORMAL" | "DUMP",
  "confidence": <Zahl zwischen 0.0 und 1.0>,
  "reason": "<Kurze Begründung auf Deutsch, max. 120 Zeichen>"
}
```

---

## 3. User-Prompt Template

```
Analysiere diesen IT-News-Artikel und klassifiziere ihn:

Titel: {title}
Quelle: {source}
Beschreibung: {summary}

Antworte nur mit dem JSON-Objekt.
```

---

## 4. Klassifizierungslogik (Beispiele)

### KRITISCH — Beispiele

| Headline | Begründung |
|---|---|
| `Kritische RCE-Lücke in Windows Server 2022 (CVE-2026-XXXXX)` | CVE + RCE = sofortiger Handlungsbedarf |
| `Microsoft Azure AD: Massenausfall in Region West Europe` | Produktionsausfall mit Unternehmensimpakt |
| `BSI warnt vor aktiver Ausnutzung von Exchange-Schwachstelle` | Behördliche Warnung + aktiver Angriff |
| `Notfall-Patch KB5040442 für Windows 11 verfügbar` | Out-of-Band Patch = kritisch |

### NORMAL — Beispiele

| Headline | Begründung |
|---|---|
| `Microsoft Copilot erhält neue Sprachfunktionen` | Feature-Update, kein Handlungsbedarf |
| `Windows 12 Release für Herbst 2026 erwartet` | Roadmap-Information |
| `Heise: Warum Zero Trust im Mittelstand unterschätzt wird` | Fachartikel, lesenswert |
| `Azure Cost Management bekommt KI-Empfehlungen` | Produktverbesserung |

### DUMP — Beispiele

| Headline | Begründung |
|---|---|
| `Microsoft Surface Pro 9 jetzt für 299€ – nur heute!` | Werbung / Deal |
| `[Sponsored] Warum Cloud-Backup Ihre Daten rettet` | Gesponsert |
| `5 Gründe, warum Sie Windows 11 JETZT upgraden sollten` | Click-Bait |
| `Einladung: Unser Webinar zu Microsoft 365 Security` | Event-Promo |

---

## 5. API-Integration (Python)

```python
from groq import Groq
import json

SYSTEM_PROMPT = """..."""  # Siehe Abschnitt 2

def classify_article(title: str, source: str, summary: str) -> dict:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    
    user_prompt = f"""Analysiere diesen IT-News-Artikel:

Titel: {title}
Quelle: {source}
Beschreibung: {summary[:500]}

Antworte nur mit dem JSON-Objekt."""

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.1,      # Niedrig für konsistente Klassifizierung
        max_tokens=150,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return {
        "category":   result.get("category", "NORMAL"),
        "confidence": float(result.get("confidence", 0.5)),
        "reason":     result.get("reason", "")
    }
```

---

## 6. Konfigurationsparameter

| Parameter | Wert | Begründung |
|---|---|---|
| `model` | `llama-3.1-70b-versatile` | Beste Balance aus Qualität + Geschwindigkeit |
| `temperature` | `0.1` | Deterministische Klassifizierung |
| `max_tokens` | `150` | JSON-Antwort ist kurz |
| `response_format` | `json_object` | Garantiert valides JSON |
| Fallback-Kategorie | `NORMAL` | Im Fehlerfall lieber zeigen als verbergen |

---

## 7. Batch-Verarbeitung

Um Kosten zu optimieren, werden Artikel in Batches klassifiziert:

- **Batch-Größe**: 20 Artikel pro Groq-Request (Multi-Item-Prompt)
- **Rate Limit**: Groq Free Tier: 30 req/min → Throttling bei Bedarf
- **Cache**: Bereits klassifizierte URLs werden nicht erneut verarbeitet
- **Retry**: Bei API-Fehler: 3 Versuche mit exponential backoff

---

## 8. Qualitätssicherung

### Confidence-Schwellwerte

| Confidence | Aktion |
|---|---|
| `≥ 0.85` | Kategorie direkt übernehmen |
| `0.60 – 0.84` | Kategorie übernehmen + in Review-Queue eintragen |
| `< 0.60` | Als `NORMAL` einstufen (sicherer Fallback) |

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
