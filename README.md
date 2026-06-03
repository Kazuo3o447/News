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
│   ├── src/components/     # NewsCard, FilterBar, Header
│   ├── src/pages/          # Dashboard, Settings
│   └── src/styles/         # GEMA Farbthema
├── infrastructure/         # Azure Bicep IaC
├── docs/                   # Projektdokumentation
└── .github/workflows/      # CI/CD Pipeline
```

---

> Farbschema: GEMA Corporate Identity — Navy `#003366` · Blau `#0052A5` · Cyan `#4DA6E0`
