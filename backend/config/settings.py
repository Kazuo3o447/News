from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""          # Leer = Groq deaktiviert, Artikel werden als NORMAL eingestuft
    # Starkes Modell für Cross-Platform-Klassifizierung.
    # Sparoption (schwächer): llama-3.1-8b-instant
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    AZURE_COSMOS_ENDPOINT: str = ""  # Leer = In-Memory-Speicher (Dev-Modus)
    AZURE_COSMOS_KEY: str = ""
    AZURE_COSMOS_DB: str = "newsdb"
    AZURE_COSMOS_CONTAINER: str = "articles"

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
    PROMPT_VERSION: str = "2025-06-01"
    # Zeitfenster für Dedup/Clustering in Stunden
    DEDUP_WINDOW_HOURS: int = 72
    # Teams-Webhook für KRITISCH-Push; leer = Push deaktiviert (No-op)
    TEAMS_WEBHOOK_URL: str = ""
    # TL;DR für KRITISCH-Artikel (kostet Tokens); standardmäßig deaktiviert
    ENABLE_CRITICAL_TLDR: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
