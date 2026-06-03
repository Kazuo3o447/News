# Eval-Harness

Misst die Klassifizierungsqualität der Pipeline gegen einen manuell erstellten Gold-Set.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `gold_set.jsonl` | 15 gelabelte Beispiele (alle 4 Plattformen, KRITISCH/NORMAL/DUMP/OFF_TOPIC) |
| `run_eval.py` | Hauptskript: führt jeden Eintrag durch die echte Pipeline, berechnet Metriken |

## Verwendung

```bash
cd backend
python eval/run_eval.py
```

### Voraussetzungen

- Virtuelle Umgebung aktiv (`venv\Scripts\activate` auf Windows)
- `.env`-Datei vorhanden mit `GROQ_API_KEY` (andernfalls wird kein LLM-Aufruf gemacht)

### Ausgabe

```
=== Eval-Harness ===  PROMPT_VERSION=2025-06-01  Items=15

── Kategorie ──────────────────────────────────────────────
Klasse       Precision   Recall     F1  Support
...
  Makro-F1 (Kategorie): 0.856

── Plattform ──────────────────────────────────────────────
...

── Confusion-Matrix (Kategorie, Zeile=erwartet, Spalte=erhalten) ──
...

[PASS] Makro-F1 0.823 >= Schwelle 0.75
```

### Exit-Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Makro-F1 (Ø Kategorie + Plattform) ≥ 0.75 |
| `1` | F1 unter Schwelle **oder** kritischer Fehler |

## Gold-Set-Format

Jede Zeile in `gold_set.jsonl` ist ein JSON-Objekt:

```json
{
  "title":             "...",
  "source":            "...",
  "summary":           "...",
  "expected_category": "KRITISCH|NORMAL|DUMP|OFF_TOPIC",
  "expected_platform": "windows|apple|android|cross"
}
```

## Neue Beispiele hinzufügen

Einfach weitere Zeilen an `gold_set.jsonl` anhängen. Alle 4 Kategorien und alle 4 Plattformen
sollten mindestens 2 Beispiele haben, damit Recall-Werte sinnvoll sind.

## Schwellenwert ändern

In `run_eval.py`, Zeile `FAIL_THRESHOLD = 0.75` anpassen.

## Prompt-Version hochzählen

Nach einer Prompt-Änderung in `.env`:

```env
PROMPT_VERSION=2025-07-01
```

Dann erneut `python eval/run_eval.py` ausführen, um sicherzustellen, dass
der neue Prompt die Schwelle nicht unterschreitet.
