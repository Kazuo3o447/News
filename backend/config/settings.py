from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""          # Leer = Groq deaktiviert, Artikel werden als NORMAL eingestuft
    GROQ_MODEL: str = "llama-3.1-8b-instant"

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

    class Config:
        env_file = ".env"


settings = Settings()
