# Manifest — IT News Hub

> Version: 0.1.0 · Stand: Mai 2026 · Autor: Projektteam

---

## 1. Projektziel

Ein zentrales Dashboard für IT-Administratoren, das Nachrichten aus führenden Quellen für
**Windows/Microsoft**, **Apple (macOS/iOS)** und **Android Enterprise** aggregiert und via
Groq KI in drei Prioritätsstufen vorklassifiziert — damit das Wichtigste auf jeder Plattform
sofort sichtbar ist.

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
│                          │  │  (gpt-oss-120b)     │  │   │
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

### Windows / Microsoft (`platform=windows`)

| Quelle | RSS URL | Priorität |
|---|---|---|
| M365 Message Center | `https://mc.merill.net/rss.xml` | Hoch |
| Azure Blog | `https://azure.microsoft.com/en-us/blog/feed/` | Hoch |
| Microsoft Security Blog | `https://www.microsoft.com/en-us/security/blog/feed/` | Hoch |
| Microsoft Tech Community | `https://techcommunity.microsoft.com/...` | Hoch |
| Windows Blog | `https://blogs.windows.com/feed/` | Mittel |
| Microsoft 365 Blog | `https://www.microsoft.com/en-us/microsoft-365/blog/feed/` | Mittel |
| MSRC | `https://msrc.microsoft.com/blog/feed/` | Hoch |

### Cross-Platform Security & IT (`platform=cross`)

| Quelle | RSS URL | Priorität |
|---|---|---|
| BleepingComputer | `https://www.bleepingcomputer.com/feed/` | Hoch |
| Krebs on Security | `https://krebsonsecurity.com/feed/` | Hoch |
| The Hacker News | `https://feeds.feedburner.com/TheHackersNews` | Hoch |
| Heise Security | `https://www.heise.de/security/rss/news-atom.xml` | Hoch |
| BSI Warnungen | `https://wid.cert-bund.de/content/public/securityAdvisory/rss` | Hoch |
| CISA Advisories | `https://www.cisa.gov/cybersecurity-advisories/all.xml` | Hoch |
| Heise Developer | `https://www.heise.de/developer/rss/news-atom.xml` | Mittel |
| iX | `https://www.heise.de/ix/news.rdf` | Mittel |
| Google Workspace Updates | `https://workspaceupdates.googleblog.com/feeds/posts/default` | Mittel |

### Apple / macOS / iOS (`platform=apple`)

| Quelle | RSS URL | Priorität |
|---|---|---|
| Jamf Blog | `https://www.jamf.com/blog/rss` | Hoch |
| Apple Developer Releases | `https://developer.apple.com/news/releases/rss/releases.rss` | Mittel |
| Intego Mac Security | `https://www.intego.com/mac-security-blog/feed/` | Mittel |
| Mr. Macintosh | `https://mrmacintosh.com/feed/` | Mittel |
| Eclectic Light | `https://eclecticlight.co/feed/` | Niedrig |

### Android / Mobile-MDM (`platform=android`)

| Quelle | RSS URL | Priorität |
|---|---|---|
| Android Developers | `https://android-developers.googleblog.com/feeds/posts/default` | Mittel |
| NowSecure | `https://www.nowsecure.com/feed/` | Niedrig |
| Android Security Bulletin | *(kein RSS — monatlicher Scraper via `android_scraper.py`)* | Hoch |
| Samsung SMR | *(kein RSS — monatlicher Scraper via `android_scraper.py`)* | Hoch |

---

## 5. Tech-Stack

### Backend

| Komponente | Technologie | Begründung |
|---|---|---|
| Framework | FastAPI 0.111+ | Async, schnell, OpenAPI-Docs automatisch |
| RSS-Parsing | feedparser 6.x | Bewährt, unterstützt Atom + RSS |
| Scheduler | APScheduler 3.x | Feed-Refresh alle 30 Minuten |
| KI-Klassifizierung | Groq Python SDK | Schnell, kostengünstig, `openai/gpt-oss-120b` |
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
| `GET` | `/api/news` | Alle Artikel (filter: `category`, `platform`, `topic`) |
| `GET` | `/api/news/{id}` | Einzelner Artikel |
| `POST` | `/api/refresh` | Manuelle Feed-Aktualisierung (`X-Refresh-Secret` Header) |
| `GET` | `/api/health` | Health-Check Endpunkt |
| `GET` | `/api/topics` | Klassifizierungsthemen als `{key, label}`-Liste |
| `GET` | `/api/platforms` | Plattformen als `{key, label}`-Liste |

---

## 7. Datenmodell (Artikel)

```json
{
  "id": "sha256-hash-der-url",
  "title": "Kritische Sicherheitslücke in Windows 11 entdeckt",
  "summary": "...",
  "url": "https://heise.de/...",
  "source": "Heise Security",
  "published_at": "2026-06-03T10:30:00Z",
  "fetched_at": "2026-06-03T10:35:00Z",
  "category": "KRITISCH",
  "platform": "windows",
  "confidence": 0.9,
  "classification_reason": "CVE + aktive Exploitierung erkannt",
  "tags": ["security", "windows", "cve", "patch"]
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
