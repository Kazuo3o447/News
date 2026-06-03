# Projektstatus — IT News Hub

> Letzte Aktualisierung: Juni 2026 (Copilot-Brief 04b — Triage-UI Korrekturen)

---

## Gesamtfortschritt

```
Infrastruktur  ████░░░░░░  40 %
Backend        ██████████ 100 %
Frontend       █████████░  96 %
KI / Groq      ██████████ 100 %
Deployment     ░░░░░░░░░░   0 %
```

---

## Copilot-Brief 04b — Triage-UI Korrekturen ✅ Abgeschlossen (Juni 2026)

- [x] **K1** `components/NewsRow.jsx`: Rotes Akzent-Element `news-row__bar` (4px-Span) ersetzt `border-left`; rot **nur** auf `.news-row--kritisch`, transparent auf NORMAL; `.news-row--priority` border-left entfernt; Fokus-Ring neutral (kein Rot)
- [x] **K2** `components/NewsRow.jsx`: `cat-chip` (Kritisch/Normal) + `plat-chip` auf **jeder** Zeile; TL;DR mit rotem `ki-tag`-Badge inline auf KRITISCH ohne Klick; CVE/CVSS/Quellen-Pillen direkt sichtbar auf KRITISCH; `classification_reason` bleibt kollapsierbar („Warum? ▼") — kein leerer Stub
- [x] **K3** `pages/Dashboard.jsx`: Zwei feste Sektionen — „● Sofort prüfen · {n}" (KRITISCH, roter Punkt) und „⌷ Übrige · {n}" (NORMAL, neutral); leere KRITISCH-Sektion zeigt „Aktuell nichts Kritisches."; Keyboard-Nav (`j/k`) traversiert beide Sektionen via `querySelectorAll("[data-id]")`
- [x] **K4** `pages/Dashboard.jsx` + `NewsRow.jsx`: `selectMode`-State in Dashboard; „Auswählen"-Button in results-bar; Checkboxen in NewsRow nur wenn `selectMode=true`; Shift+Klick aktiviert selectMode automatisch; Kopieren- + Ticket-Buttons als `.action-btn--hover` (opacity 0, bei Hover sichtbar)
- [x] **K5** `pages/Dashboard.jsx`: `fetchCounts` übergibt `collapse: true`; nach jedem Haupt-Fetch `setCounts(prev => ({ ...prev, [platform]: total }))` → „Alle N"-Switcher-Badge == „N Artikel"-Resultsbar; Zähler-Diskrepanz behoben
- [x] **K6** `components/NewsRow.jsx`: `read_by` als Text „gelesen von anna.k." via `shortUser()`; keine Avatar-Kreise mehr; NORMAL-Titelzeile `font-weight: 400`; `.news-row--priority` Blau-Balken entfernt
- [x] **K1–K6** `styles/theme.css`: CSS-Overrides für alle neuen Klassen ergänzt — `.news-row__bar`, `.cat-chip`, `.plat-chip`, `.new-chip`, `.ki-tag`, `.triage-section`, `.triage-section__head`, `.triage-dot`, `.triage-count`, `.triage-empty`, `.action-btn--hover`, `.results-bar__select-btn`

---

## Copilot-Brief 04 — Frontend-Redesign: Triage-UI ✅ Abgeschlossen (Juni 2026)

- [x] **F0** Zustand-Dependency entfernt; `utils/platforms.js` **NEU**: `PLATFORMS`-Array, `platformLabel()`, `PLATFORM_LABEL`-Map
- [x] **F1** `components/Topbar.jsx` **NEU**: PlatformSwitcher · Suchfeld · View-Toggle (Ungelesen/Alle) · Filter-Chips (Topic, Quelle); `components/PlatformSwitcher.jsx` überarbeitet — Label „Microsoft" statt „Windows", Text-only, Unread-Count-Badges
- [x] **F2** `components/NewsRow.jsx` komplett neu: ~48px-Flex-Zeile mit Plattform-Icon, isNew-Punkt, Titel, Quelle, Alter, Aktionszeile; server-basierter Read-State
- [x] **F3** `pages/Dashboard.jsx`: Keyboard-Navigation (j/k, o, e, u, t, /, g+u, g+a); Shift+Klick Multi-Select; focusIdx scrollt in View
- [x] **F4** `hooks/useReadState.js` **NEU**: Server-basierter Team-Read-State, optimistische Updates; `hooks/useUIPrefs.js` **NEU**: localStorage `itnews.ui.v4` (platform, view, darkMode, lastVisitAt)
- [x] **F5** `components/Header.jsx` überarbeitet: Dark-Mode-Toggle (☀/☽), kritischUnread-Pill, Höhe 52px; `styles/theme.css`: Dark-Mode-Token, Mobile-Breakpoints
- [x] **F6** `pages/Dashboard.jsx` komplett neu: Flache Liste mit Paginierung, Dump-Toggle, Skeleton-Loader, Error-State, Zähler-Badges

---

## Copilot-Brief 03 — Backend, Daten & KI ✅ Abgeschlossen (Juni 2026)

- [x] **B1** `services/cosmos_service.py`: Server-seitiger Filter/Suche/Sort — neue Parameter `view`, `q`, `topic`, `source`, `since` in `get_articles()`; `page_size` hard-cap 60; Platform-Filter inkl. `cross`; **alle** Cosmos-Queries nun parametrisiert (SQL-Injection-Fix)
- [x] **B1** `api/routes/news.py`: Vollständig neu geschrieben — `GET /api/news` mit neuen Query-Params `view`, `q`, `topic`, `source`, `since`, `collapse`; Response-Struktur `{total, page, page_size, view, collapse, items}`; `is_priority` Flag pro Artikel
- [x] **B2** `services/identity.py` **NEU**: User-Extraktion aus `X-MS-CLIENT-PRINCIPAL-NAME` → `X-User` → `"anonymous"` (kein Login-Build nötig)
- [x] **B2** `services/read_state.py` **NEU**: Team-Read-State (per User, per Artikel); Cosmos `reads`-Container + In-Memory-Fallback; `mark_read`, `mark_unread`, `mark_read_bulk`, `read_map`, `is_read`; parametrisierte IN-Clause
- [x] **B2** `api/routes/news.py`: Neue Endpunkte `POST /api/articles/{id}/read`, `DELETE /api/articles/{id}/read`, `POST /api/articles/read/bulk` (max 500); Response-Anreicherung mit `read_by`, `is_read`
- [x] **B3** `services/rss_fetcher.py`: `fetch_all_feeds(priorities: set[str] | None)` — filtert FEEDS nach `feed_cfg["priority"]` wenn angegeben
- [x] **B3** `services/scheduler.py`: `run_pipeline(priority_filter)` — 3 Tiered-Jobs: `pipeline_high` (10 min), `pipeline_medium` (30 min), `pipeline_low` (60 min)
- [x] **B4** `services/groq_classifier.py`: Zweistufige Groq-Modelle — `GROQ_MODEL_CLASSIFY` (`llama-3.1-8b-instant`) für `classify_batch()`; `GROQ_MODEL_SUMMARY` (`openai/gpt-oss-120b`) für `summarize_critical()`
- [x] **B4/B5** `services/groq_classifier.py`: SYSTEM_PROMPT erweitert mit M365/Azure Few-Shots: Azure Outage → KRITISCH/windows; Entra ID Auth-Ausfall → KRITISCH/windows; MC-Einträge ohne Security → NORMAL/windows
- [x] **B5** `services/groq_classifier.py`: `summarize_critical(articles)` **NEU** — deutsche Handlungszeilen ≤140 Zeichen für KRITISCH-Artikel via starkem Modell; `TLDR_SYSTEM_PROMPT` separat
- [x] **B5** `services/scheduler.py`: TL;DR-Block nach Klassifizierung — `summarize_critical(new_kritisch)` → `a.tldr` setzen → `upsert_many()` re-persist vor Teams-Push
- [x] **B6** `services/notifier.py`: Cluster-Dedup mit In-Memory Dict + optionaler Cosmos `notified`-Persistenz (TTL = `DEDUP_WINDOW_HOURS`); `was_notified()`, `mark_notified()`; `notify_critical()` filtert bereits notifizierte Cluster; Payload mit `tldr` + `cluster_size`
- [x] **B7** `services/scheduler.py`: `start_scheduler()` prüft `settings.RUN_SCHEDULER` — bei `False` No-op (scale-out-sicher, kein Doppel-Job auf mehreren Instanzen)
- [x] **B8** `eval/gold_set.jsonl`: 15 → **45 Einträge** — M365 Message Center (MC), Azure Outages, Entra ID Auth-Ausfälle, MSRC Patch Tuesday (kritisch + normal), Android Security Bulletin, Samsung SMR, Apple RSR, OpenSSL/Log4j (cross), CISA KEV, NIS2; + DUMP-Fälle
- [x] **B8** `eval/run_eval.py`: Separate Accuracy-Ausgabe für Criticality (`>= 0.80`) und Platform (`>= 0.70`); Exit-Code ≠ 0 bei Unterschreitung beider Schwellen



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

## Copilot-Brief 02 — Frontend & UX ✅ Abgeschlossen (Juni 2026)

- [x] **F1** `hooks/usePrefs.js`: `selectedPlatform`, `readIds` (Set O(1)), `lastVisitAt`; neue Aktionen `setSelectedPlatform`, `markRead`, `markAllRead`, `isRead`, `touchVisit`; Migration aus v1-Key (`itnews.prefs.v1` → `itnews.prefs.v2`)
- [x] **F2** `components/PlatformSwitcher.jsx` **NEU**: Segmented Control (🌐 Alle | 🪟 Windows | Apple | Android); GEMA-Rot aktiv; Artikelzahl pro Segment (eigene + cross); mobil umbrechen
- [x] **F3** `pages/Dashboard.jsx` — Logik: Plattform-Filter (platform === sel || cross), KRITISCH-First-Sortierung, `touchVisit()` beim Mount, Neu/Kritisch-Stats im Header, „Alle gelesen"-Button
- [x] **F4** `pages/Dashboard.jsx` — Layout: Sektion A „Sofort prüfen (N)" als `NewsCard`-Grid; Sektion B „Übrige" als `NewsRow`-Liste (paginiert 30/Seite); leere-Kritisch-Hinweis
- [x] **F5** `components/NewsCard.jsx`: Confidence-% entfernt; Plattform-Badge; `classification_reason` als Tooltip; `isNew`-Indikator; Aktionszeile (Öffnen / Gelesen / Kopieren / Ticket-Stub); gelesene Karten ausgegraut
- [x] **F5** `components/NewsRow.jsx` **NEU**: Kompakte ~48px-Flex-Zeile (Plattform-Icon · isNew-Dot · Titel · Quelle · Zeit · Aktionen); Hover-only Aktionen
- [x] **F6** `components/FilterSidebar.jsx`: Plattform-Panel (Single-Select); Topics via `GET /api/topics` (Fallback utils/topics.js); „Dump (Werbung)" → „Aussortiert anzeigen"; OFF_TOPIC-Zweig aktiv
- [x] **F7** `styles/theme.css`: Plattform-Farbtoken (`--plat-windows/apple/android/cross` + `-bg`); Klassen `.platform-switcher`, `.badge--platform`, `.dot--new`, `.badge--new`, `.section-head`, `.news-rows`/`.news-row`, `.action-btn`, `.mark-all-btn`

---

## Phase 3 — Frontend ✅ Abgeschlossen

- [x] Vite + React Projekt initialisiert
- [x] GEMA Farbthema in CSS Custom Properties umgesetzt (GEMA-Rot `#E2001A` als einzige Signalfarbe)
- [x] `Header` Komponente erstellt
- [x] `NewsCard` Komponente erstellt (Kategorie-Badge, Plattform-Badge, Aktionszeile)
- [x] `NewsRow` Komponente erstellt (kompakte Listenzeile für Übrige-Sektion)
- [x] `PlatformSwitcher` Komponente erstellt (segmentierte Steuerung)
- [x] `FilterSidebar` Komponente erstellt (Plattform, Themen, Kritikalität, Quelle)
- [x] `Dashboard` Seite implementiert (Zwei-Ebenen-Layout: Kritisch-Karten / Übrige-Liste)
- [x] `Settings` Seite implementiert (Themen-Abos, Quellen-Mute, Reset)
- [x] Responsives Layout umgesetzt
- [x] API-Anbindung (Axios) implementiert; Topics aus `GET /api/topics`
- [x] Loading/Error-States implementiert
- [x] localStorage-Persistenz: Plattform-Stack, gelesen/ungelesen, letzter Besuch (`itnews.prefs.v2`)

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
| 1 | Groq-API-Key nicht gesetzt → alle Artikel `OFF_TOPIC` (kein LLM-Call) | Niedrig | Offen — `.env` lokal befüllen |

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
| Juni 2026 | Kein Tailwind / keine UI-Library | GEMA-Rot als einzige Signalfarbe; saubere CSS Custom Properties in theme.css |
| Juni 2026 | `DUMP` → „Aussortiert" (UI-Begriff) | „Werbung" war zu eng; DUMP = plattformunabhängiges Rauschen (Consumer, Deals, Gerüchte) |
| Juni 2026 | Zwei-Ebenen-Layout (Karten + Listenzeilen) | KRITISCH muss schreien; 200 NORMAL-Karten kosten zu viel Scroll |
| Juni 2026 | localStorage `readIds` als Set | O(1)-Lookup für `isRead(id)`; als Array persistiert (JSON-kompatibel) |

---

## Nächste Schritte

1. Azure: Infrastruktur provisionieren (`infrastructure/main.bicep`)
2. CI/CD: GitHub Actions für Backend (pytest + ruff) und Frontend (build) einrichten
3. Deployment: Erstes Deployment auf Azure App Service + Static Web Apps
4. Backend: server-seitigen Plattform-/Kategorie-Filter in `GET /api/news` schärfen (statt page_size=500 + Client-Filter)
5. Frontend: `GET /api/platforms` im PlatformSwitcher konsumieren (derzeit hardcodiert)
