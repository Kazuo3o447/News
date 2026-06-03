# Manifest — IT News Hub

> Version: 0.1.0 · Stand: Mai 2026 · Autor: Projektteam

---

## 1. Projektziel

Ein zentrales Dashboard für IT-Fachkräfte, das Nachrichten aus führenden
IT- und Microsoft-Quellen aggregiert und via Groq KI in drei Prioritätsstufen
vorklassifiziert — damit das Wichtigste sofort sichtbar ist.

---

## 2. Klassifizierungsstufen

| Stufe | Bedeutung | Farbe |
|---|---|---|
| 🔴 **KRITISCH** | Sicherheitslücken, Outages, Zero-Days, kritische Patches | `#CC2200` |
| 🔵 **NORMAL** | Produktneuheiten, Branchen-News, technische Artikel | `#0052A5` |
| ⚫ **DUMP** | Werbung, Sponsored Content, Click-Bait, Deals | `#A0AEC0` |

---

## 3. Architektur

```
┌─────────────────────────────────────────────────────────┐
│                     Azure (Cloud)                       │
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │  Azure Static    │    │   Azure App Service       │   │
│  │  Web Apps        │◄──►│   (Python / FastAPI)      │   │
│  │  (React Frontend)│    │                           │   │
│  └──────────────────┘    │  ┌─────────────────────┐  │   │
│                          │  │  RSS Feed Service   │  │   │
│                          │  │  (Scheduler 30 min) │  │   │
│                          │  └────────┬────────────┘  │   │
│                          │           │               │   │
│                          │  ┌────────▼────────────┐  │   │
│                          │  │  Groq Classifier    │  │   │
│                          │  │  (llama-3.1-70b)    │  │   │
│                          │  └────────┬────────────┘  │   │
│                          └───────────┼───────────────┘   │
│                                      │                   │
│  ┌───────────────────────────────────▼─────────────┐     │
│  │           Azure Cosmos DB (NoSQL)               │     │
│  │           Container: articles                  │     │
│  └─────────────────────────────────────────────────┘     │
│                                                         │
│  ┌─────────────────┐   ┌──────────────────────────┐      │
│  │  Azure Key Vault│   │  Application Insights    │      │
│  │  (API Keys)     │   │  (Monitoring/Logging)    │      │
│  └─────────────────┘   └──────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
        ▲
        │  RSS Polls (extern)
        │
┌───────┴──────────────────────────────────────────────────┐
│  News-Quellen (RSS)                                      │
│  Heise, The Verge, Ars Technica, Microsoft Blog, ...     │
└──────────────────────────────────────────────────────────┘
```

---

## 4. RSS Feed-Quellen

### Microsoft-spezifisch

| Quelle | RSS URL | Priorität |
|---|---|---|
| Microsoft Tech Community | `https://techcommunity.microsoft.com/rss` | Hoch |
| Microsoft Security Blog | `https://www.microsoft.com/en-us/security/blog/feed/` | Hoch |
| Windows Blog | `https://blogs.windows.com/feed/` | Mittel |
| Azure Blog | `https://azure.microsoft.com/en-us/blog/feed/` | Hoch |
| Microsoft 365 Blog | `https://www.microsoft.com/en-us/microsoft-365/blog/feed/` | Mittel |
| Windows Central | `https://www.windowscentral.com/rss.xml` | Mittel |

### Allgemeine IT-Nachrichten (DE)

| Quelle | RSS URL | Priorität |
|---|---|---|
| Heise Online | `https://www.heise.de/rss/heise-atom.xml` | Hoch |
| Golem.de | `https://rss.golem.de/rss.php?feed=RSS2.0` | Hoch |
| t3n | `https://t3n.de/rss.xml` | Mittel |
| Computerwoche | `https://www.computerwoche.de/feed/news` | Mittel |
| IT-Times | `https://www.it-times.de/rss/news.xml` | Niedrig |

### Allgemeine IT-Nachrichten (EN)

| Quelle | RSS URL | Priorität |
|---|---|---|
| Ars Technica | `https://feeds.arstechnica.com/arstechnica/index` | Hoch |
| The Verge (Tech) | `https://www.theverge.com/rss/index.xml` | Mittel |
| TechCrunch | `https://techcrunch.com/feed/` | Mittel |
| ZDNet | `https://www.zdnet.com/news/rss.xml` | Mittel |
| BleepingComputer | `https://www.bleepingcomputer.com/feed/` | Hoch (Security) |
| Krebs on Security | `https://krebsonsecurity.com/feed/` | Hoch (Security) |

---

## 5. Tech-Stack

### Backend

| Komponente | Technologie | Begründung |
|---|---|---|
| Framework | FastAPI 0.111+ | Async, schnell, OpenAPI-Docs automatisch |
| RSS-Parsing | feedparser 6.x | Bewährt, unterstützt Atom + RSS |
| Scheduler | APScheduler 3.x | Feed-Refresh alle 30 Minuten |
| KI-Klassifizierung | Groq Python SDK | Schnell, kostengünstig, llama-3.1-70b |
| DB-Client | azure-cosmos 4.x | Offizielles Azure SDK |
| Runtime | Python 3.12 | Aktuell, Azure App Service support |

### Frontend

| Komponente | Technologie | Begründung |
|---|---|---|
| Framework | React 18 + Vite | Schnell, modernes Ökosystem |
| Styling | CSS Custom Properties | GEMA-Farbthema, kein Framework-Overhead |
| HTTP-Client | Axios | Einfach, weit verbreitet |
| State | Zustand (Zustand.js) | Leichtgewichtig für diesen Use-Case |

### Azure-Infrastruktur

| Ressource | Tier | Zweck |
|---|---|---|
| App Service Plan | B2 (Dev: B1) | Backend-Hosting |
| Static Web Apps | Free / Standard | Frontend-Hosting + CDN |
| Cosmos DB | Serverless | Artikel-Persistenz |
| Key Vault | Standard | API-Keys sicher speichern |
| Application Insights | Basic | Monitoring & Fehlertracking |

---

## 6. API-Endpunkte (Backend)

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/api/news` | Alle Artikel (paginiert, filter per Query-Param) |
| `GET` | `/api/news/{id}` | Einzelner Artikel |
| `GET` | `/api/news?category=KRITISCH` | Gefiltert nach Kategorie |
| `POST` | `/api/refresh` | Manuelle Feed-Aktualisierung (Auth required) |
| `GET` | `/api/health` | Health-Check Endpunkt |
| `GET` | `/api/feeds` | Liste aller konfigurierten Feeds |

---

## 7. Datenmodell (Artikel)

```json
{
  "id": "sha256-hash-der-url",
  "title": "Kritische Sicherheitslücke in Windows 11 entdeckt",
  "summary": "...",
  "url": "https://heise.de/...",
  "source": "Heise Online",
  "published_at": "2026-05-27T10:30:00Z",
  "fetched_at": "2026-05-27T10:35:00Z",
  "category": "KRITISCH",
  "confidence": 0.94,
  "classification_reason": "Sicherheitslücke + Patch-Dringlichkeit erkannt",
  "tags": ["security", "windows", "patch"]
}
```

---

## 8. GEMA Farbschema

```css
/* GEMA Corporate Colors */
--gema-navy:      #003366;   /* Primär dunkelblau */
--gema-blue:      #0052A5;   /* Primär blau */
--gema-cyan:      #4DA6E0;   /* Akzent hellblau */
--gema-bg:        #F0F4F8;   /* Hintergrund */
--gema-surface:   #FFFFFF;   /* Karten/Panels */
--gema-text:      #1A1A2E;   /* Primärtext */
--gema-muted:     #4A5568;   /* Sekundärtext */

/* Klassifizierungs-Farben */
--cat-critical:   #CC2200;   /* KRITISCH – Rot */
--cat-normal:     #0052A5;   /* NORMAL – Blau */
--cat-dump:       #A0AEC0;   /* DUMP – Grau */
```

---

## 9. Sicherheit

- API-Keys ausschließlich in Azure Key Vault, nie im Code
- CORS nur für eigene Domains konfiguriert
- Rate-Limiting auf dem `/api/refresh` Endpunkt
- Input-Validierung via Pydantic-Schemas
- HTTPS erzwungen (Azure App Service + HSTS)

---

## 10. CI/CD Pipeline

```
GitHub Push (main)
       │
       ▼
GitHub Actions
  ├── Backend: pytest + ruff lint
  ├── Frontend: npm test + build
  └── Deploy → Azure (App Service + Static Web Apps)
```
