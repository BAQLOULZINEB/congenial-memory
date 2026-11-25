import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Vercel sets VERCEL=1. Its filesystem is read-only except /tmp, and an instance may start on any
# request, so the database lives in /tmp (a demo that resets on cold start) and startup is lazy.
SERVERLESS = bool(os.environ.get("VERCEL"))
if SERVERLESS:  # Model weights are downloaded once per instance into the writable /tmp.
    os.environ.setdefault("HF_HOME", "/tmp/huggingface")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Any OpenAI-compatible endpoint: hosted (Groq, OpenRouter, Mistral...) or local (Ollama).
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str = ""
    llm_timeout_s: float = 45
    database_path: str = "/tmp/talentmatch.sqlite3" if SERVERLESS else "data/talentmatch.sqlite3"
    # Shared JWT signing secret. Required when several instances serve the app (Vercel); locally a
    # random key is generated next to the database instead.
    jwt_secret: str = ""
    # Creates the demo account and its example report on startup when they are missing.
    demo_seed: bool = True
    max_file_bytes: int = 5 * 1024 * 1024
    max_text_chars: int = 30000


@lru_cache
def settings() -> Settings:
    return Settings()
