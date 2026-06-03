from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""          # Leer = Groq deaktiviert, Artikel werden als NORMAL eingestuft

    # B4: Zwei Modelle — schnelles für Klassifizierung, starkes für TL;DR
    GROQ_MODEL_CLASSIFY: str = "llama-3.1-8b-instant"   # schnell, günstig, reicht für 3 Klassen
    GROQ_MODEL_SUMMARY:  str = "openai/gpt-oss-120b"    # stark, nur für KRITISCH TL;DR
    # Alias für Abwärtskompatibilität
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    AZURE_COSMOS_ENDPOINT: str = ""  # Leer = In-Memory-Speicher (Dev-Modus)
    AZURE_COSMOS_KEY: str = ""
    AZURE_COSMOS_DB: str = "newsdb"
    AZURE_COSMOS_CONTAINER: str = "articles"
    # B2: eigener Container für Team-Gelesen-Status
    AZURE_COSMOS_READS_CONTAINER: str = "reads"
    # B6: eigener Container für Benachrichtigungs-Tracking
    AZURE_COSMOS_NOTIFIED_CONTAINER: str = "notified"

    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change_me"
    FEED_REFRESH_INTERVAL_MINUTES: int = 30
    MAX_ARTICLES_PER_FEED: int = 50
    ARTICLE_RETENTION_DAYS: int = 7
    ARTICLE_CLEANUP_INTERVAL_HOURS: int = 6

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Shared-Secret für POST /api/refresh; leer = Dev-Modus (kein Auth-Check)
    REFRESH_SECRET: str = ""
    # Optionaler Base-URL für "Ticket erstellen"-Hook im Frontend
    HALO_TICKET_BASE_URL: str = ""
    # Fallback-Plattform wenn weder LLM noch Regelschicht einen Wert liefern
    DEFAULT_PLATFORM: str = "cross"

    # Prompt-Versionierung — bei jeder relevanten Prompt-Änderung hochzählen
    PROMPT_VERSION: str = "2026-06-03"
    # Zeitfenster für Dedup/Clustering in Stunden
    DEDUP_WINDOW_HOURS: int = 72
    # Teams-Webhook für KRITISCH-Push; leer = Push deaktiviert (No-op)
    TEAMS_WEBHOOK_URL: str = ""
    # B5: TL;DR für KRITISCH-Artikel — jetzt standardmäßig AN
    ENABLE_CRITICAL_TLDR: bool = True

    # B7: Scheduler-Guard — bei Scale-out nur eine Instanz mit True
    RUN_SCHEDULER: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
