# Projektstatus — IT News Hub

> Letzte Aktualisierung: Juni 2026 (Copilot-Brief 01 — Cross-Platform-Umbau)

---

## Gesamtfortschritt

```
Infrastruktur  ████░░░░░░  40 %
Backend        █████████░  85 %
Frontend       █████░░░░░  55 %
KI / Groq      █████████░  90 %
Deployment     ░░░░░░░░░░   0 %
```

---

## Copilot-Brief 01 — Backend & KI-Pipeline ✅ Abgeschlossen (Juni 2026)

- [x] `config/feeds.py`: platform-Feld + Apple/Android-Feeds (Jamf, Intego, Mr. Macintosh, Eclectic Light, Android Developers, Google Workspace, NowSecure)
- [x] `api/models/article.py`: `platform: Platform | None` als neues Feld
- [x] `config/settings.py`: GROQ_MODEL → `openai/gpt-oss-120b`, neue Felder REFRESH_SECRET / HALO_TICKET_BASE_URL / DEFAULT_PLATFORM
- [x] `services/topics.py`: PLATFORMS-Liste + platform_label() — Single Source of Truth
- [x] `api/routes/news.py`: GET /api/topics + GET /api/platforms; platform-Filter; OFF_TOPIC; POST /api/refresh Auth via X-Refresh-Secret
- [x] `services/pre_filter.py`: Apple/Android-Keywords in ALLOWLIST; `autopilot` aus DENYLIST (kollidiert mit Windows Autopilot); platform_hint-Feld im Rückgabe-Dict
- [x] `services/rule_classifier.py` **NEU**: Deterministische Schicht (CVE / CVSS / aktiver Exploit / Advisory-Quelle → forced_critical); Source→Platform-Map
- [x] `tests/test_rule_classifier.py` **NEU**: ~25 Unit-Tests
- [x] `services/groq_classifier.py`: Cross-Platform-Prompt; classify_batch() (12 Artikel/Request); classify_article() als Wrapper; Modell via settings.GROQ_MODEL
- [x] `services/scheduler.py`: Pipeline vollständig verdrahtet (Pre-Filter → Regelschicht → Groq-Batch → Merge → Cosmos); THROTTLE 6s→1s; Bug 1+2 behoben
- [x] `services/android_scraper.py` **NEU**: Monatlicher Scraper für Android Security Bulletin + Samsung SMR (kein RSS)
- [x] `services/vendor_scraper.py` **NEU** (T9): `scrape_apple_security()` — täglich von support.apple.com/en-us/100100 (iOS, macOS, Safari, Xcode); in Scheduler als täglicher Cron-Job 07:00 UTC eingehängt; gleiche Pipeline wie RSS-Feeds (Pre-Filter → Regelschicht → Batch-LLM → Merge → Cosmos)
- [x] `.env.example` aktualisiert

- [x] Konzept & Architektur definiert
- [x] Ordnerstruktur angelegt
- [x] Manifest.md erstellt
- [x] Agent.md (Groq) erstellt
- [x] .env.example definiert
- [x] .gitignore erstellt
- [x] README.md erstellt

---

## Phase 2 — Backend Grundgerüst ✅ Abgeschlossen

- [x] FastAPI App initialisiert (`backend/main.py`)
- [x] Pydantic-Datenmodell `Article` definiert (`platform`, `category`, `confidence`-Felder)
- [x] Endpunkt `GET /api/health` implementiert
- [x] Endpunkt `GET /api/news` implementiert (inkl. `platform`- und `category`-Filter, KRITISCH-Sortierung)
- [x] Endpunkt `GET /api/topics` + `GET /api/platforms` implementiert
- [x] Endpunkt `POST /api/refresh` mit `X-Refresh-Secret`-Auth implementiert
- [x] RSS-Fetcher Service (`rss_fetcher.py`) implementiert
- [x] Feed-Konfiguration (`config/feeds.py`) befüllt (23 Feeds: Windows + Apple + Android + Cross)
- [x] Groq-Classifier Service (`groq_classifier.py`) implementiert (Batch 12/Request, Cross-Platform-Prompt)
- [x] Rule-Classifier Service (`rule_classifier.py`) implementiert (deterministisch: CVE / CVSS / Exploit-Signale)
- [x] Android Scraper (`android_scraper.py`) implementiert (monatlich via APScheduler)
- [x] Apple Scraper (`vendor_scraper.py`, `scrape_apple_security()`) implementiert (täglich via APScheduler; support.apple.com/en-us/100100)
- [x] APScheduler für automatischen Feed-Refresh eingerichtet (30 min; Android monatlich montags; Apple täglich 07:00 UTC)
- [x] Azure Cosmos DB Anbindung implementiert (In-Memory-Fallback für lokale Entwicklung)
- [x] Unit-Tests für Services geschrieben (37 Tests, alle grün)
- [x] `requirements.txt` finalisiert

---

## Phase 3 — Frontend 🔲 Ausstehend

- [ ] Vite + React Projekt initialisiert
- [ ] GEMA Farbthema in CSS Custom Properties umgesetzt
- [ ] `Header` Komponente erstellt
- [ ] `NewsCard` Komponente erstellt (mit Kategorie-Badge)
- [ ] `FilterBar` Komponente erstellt (KRITISCH / NORMAL / DUMP)
- [ ] `Dashboard` Seite implementiert
- [ ] `Settings` Seite (Feed-Verwaltung) implementiert
- [ ] Responsives Layout umgesetzt
- [ ] API-Anbindung (Axios) implementiert
- [ ] Loading/Error-States implementiert

---

## Phase 4 — Azure Infrastruktur 🔲 Ausstehend

- [ ] Azure Subscription / Resource Group eingerichtet
- [ ] Azure App Service Plan (B1 Dev) provisioniert
- [ ] Azure Static Web App provisioniert
- [ ] Azure Cosmos DB (Serverless) eingerichtet
- [ ] Azure Key Vault eingerichtet + Secrets hinterlegt
- [ ] Application Insights konfiguriert
- [ ] Bicep-Templates (`infrastructure/`) finalisiert
- [ ] Manuelle Erstdeployment durchgeführt

---

## Phase 5 — CI/CD & Testing 🔲 Ausstehend

- [ ] GitHub Actions Workflow für Backend (lint + test)
- [ ] GitHub Actions Workflow für Frontend (build + test)
- [ ] GitHub Actions Deploy → Azure App Service
- [ ] GitHub Actions Deploy → Azure Static Web Apps
- [ ] Umgebungsvariablen in GitHub Secrets hinterlegt
- [ ] End-to-End Test: Feed-Fetch → Klassifizierung → Anzeige

---

## Phase 6 — Produktion 🔲 Ausstehend

- [ ] App Service Plan auf B2 hochgestuft
- [ ] Custom Domain konfiguriert
- [ ] SSL-Zertifikat (Azure Managed) eingerichtet
- [ ] Monitoring-Alerts in Application Insights konfiguriert
- [ ] Feed-Quellen final kuratiert
- [ ] Performance-Tests durchgeführt
- [ ] Security Review (OWASP Top 10 Checklist)

---

## Bekannte Probleme / Blocker

| # | Beschreibung | Priorität | Status |
|---|---|---|---|
| — | Keine offenen Blocker | — | — |

---

## Entscheidungslog

| Datum | Entscheidung | Begründung |
|---|---|---|
| Mai 2026 | FastAPI statt Flask | Async-Support, automatische OpenAPI-Docs |
| Mai 2026 | Cosmos DB statt SQL | Schemalos, gut für variable RSS-Felder |
| Mai 2026 | Groq llama-3.1-70b | Schnell, kostengünstig, gute DE/EN-Leistung |
| Mai 2026 | GEMA Farbschema | Corporate Identity, klare Blau-Hierarchie |
| Juni 2026 | Groq-Modell → `openai/gpt-oss-120b` | Bessere Qualität bei Cross-Platform-Klassifizierung |
| Juni 2026 | Cross-Platform statt Microsoft-only | Windows + Apple + Android gleichwertig; Copilot-Brief 01 |
| Juni 2026 | Confidence deterministisch (nicht vom LLM) | `1.0` forced_critical / `0.9` match / `0.6` mismatch — reproduzierbar |
| Juni 2026 | Rule-Classifier vor LLM | CVE/CVSS/aktiver Exploit zuverlässiger per Regex als per LLM |

---

## Nächste Schritte

1. Frontend: Platform-Filter und Plattform-Badges in `FilterSidebar.jsx` + `NewsCard.jsx` integrieren
2. Frontend: `GET /api/platforms` und `GET /api/topics` konsumieren (statt hard-coded Listen)
3. Azure: Infrastruktur provisionieren (`infrastructure/main.bicep`)
4. CI/CD: GitHub Actions für Backend (pytest + ruff) und Frontend (build) einrichten
5. Deployment: Erstes Deployment auf Azure App Service + Static Web Apps
