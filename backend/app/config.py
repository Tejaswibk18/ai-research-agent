from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "AI Research Agent"
    APP_VERSION: str = "1.0.0"

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # Frontend
    FRONTEND_URL: str = "http://localhost:5500"

    # Upload
    MAX_UPLOAD_SIZE_MB: int = 10

    # Chunking
    CHUNK_SIZE: int = 3500
    CHUNK_OVERLAP: int = 500

    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.35

    # Agent
    AGENT_MAX_ITERATIONS: int = 6
    AGENT_TEMPERATURE: float = 0.2

    # Storage
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    INDEX_DIR: Path = BASE_DIR / "data" / "index"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()