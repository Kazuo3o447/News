# IT News Hub

Eine intelligente News-Aggregations-App für IT- und Microsoft-Nachrichten,
gehostet als Azure Web App mit KI-gestützter Vorklassifizierung via Groq.

---

## Überblick

| Aspekt | Details |
|---|---|
| **Hosting** | Azure App Service (Backend) + Azure Static Web Apps (Frontend) |
| **Sprache** | Python 3.12 (FastAPI) + React 18 (Vite) |
| **KI** | Groq API – Klassifizierung: Kritisch / Normal / Dump |
| **Daten** | RSS-Feed-Aggregation, Azure Cosmos DB |
| **CI/CD** | GitHub Actions → Azure |

---

## Dokumentation

| Datei | Inhalt |
|---|---|
| [docs/Manifest.md](docs/Manifest.md) | Architektur, Tech-Stack, Feed-Quellen, Azure-Infrastruktur |
| [docs/Status.md](docs/Status.md) | Projektstatus, Meilensteine, offene Punkte |
| [docs/Agent.md](docs/Agent.md) | Groq KI-Agent: Klassifizierungs-Logik & Prompts |

---

## Schnellstart (Lokal)

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # .env befüllen
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Projektstruktur

```
News/
├── backend/                # Python FastAPI
│   ├── api/routes/         # REST Endpunkte
│   ├── services/           # RSS-Fetcher, Groq-Classifier, Scheduler
│   ├── config/             # Einstellungen, Feed-Liste
│   └── main.py
├── frontend/               # React + Vite
│   ├── src/components/     # Header, Topbar, PlatformSwitcher, NewsRow
│   ├── src/hooks/          # useUIPrefs, useReadState
│   ├── src/pages/          # Dashboard (Triage-Board), Settings
│   ├── src/utils/          # platforms.js, topics.js
│   └── src/styles/         # GEMA Farbthema (theme.css)
├── infrastructure/         # Azure Bicep IaC
├── docs/                   # Projektdokumentation
└── .github/workflows/      # CI/CD Pipeline
```

---

## Aktueller Stand

| Brief | Beschreibung | Status |
|---|---|---|
| Brief 01 | Backend & KI-Pipeline | ✅ Abgeschlossen |
| Brief 02 | Frontend Grundgerüst | ✅ Abgeschlossen |
| Brief 03 | Backend, Daten & KI (Erweiterung) | ✅ Abgeschlossen |
| Brief 04 | Frontend-Redesign: Triage-UI | ✅ Abgeschlossen |
| Brief 04b | Triage-UI Korrekturen (K1–K6) | ✅ Abgeschlossen |
| Brief 05 | Azure Deployment | 🔲 Ausstehend |

---

> Farbschema: GEMA Corporate Identity — Navy `#003366` · Blau `#0052A5` · GEMA-Rot `#E2001A` als einzige Signalfarbe
