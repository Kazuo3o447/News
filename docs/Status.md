# Projektstatus — IT News Hub

> Letzte Aktualisierung: Mai 2026

---

## Gesamtfortschritt

```
Infrastruktur  ░░░░░░░░░░  0 %
Backend        ░░░░░░░░░░  0 %
Frontend       ░░░░░░░░░░  0 %
KI / Groq      ░░░░░░░░░░  0 %
Deployment     ░░░░░░░░░░  0 %
```

---

## Phase 1 — Projektaufbau ✅

- [x] Konzept & Architektur definiert
- [x] Ordnerstruktur angelegt
- [x] Manifest.md erstellt
- [x] Agent.md (Groq) erstellt
- [x] .env.example definiert
- [x] .gitignore erstellt
- [x] README.md erstellt

---

## Phase 2 — Backend Grundgerüst 🔄 In Arbeit

- [ ] FastAPI App initialisiert (`backend/main.py`)
- [ ] Pydantic-Datenmodell `Article` definiert
- [ ] Endpunkt `GET /api/health` implementiert
- [ ] Endpunkt `GET /api/news` implementiert (mock data)
- [ ] RSS-Fetcher Service (`rss_fetcher.py`) implementiert
- [ ] Feed-Konfiguration (`config/feeds.py`) befüllt
- [ ] Groq-Classifier Service (`groq_classifier.py`) implementiert
- [ ] APScheduler für automatischen Feed-Refresh eingerichtet
- [ ] Azure Cosmos DB Anbindung implementiert
- [ ] Unit-Tests für Services geschrieben
- [ ] `requirements.txt` finalisiert

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

---

## Nächste Schritte

1. Python-Umgebung einrichten (`python -m venv .venv`)
2. Backend `main.py` und `requirements.txt` vervollständigen
3. Groq API-Key besorgen und in `.env` eintragen
4. Ersten RSS-Fetch + Klassifizierung lokal testen
