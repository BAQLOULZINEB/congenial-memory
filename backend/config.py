from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:3b"
    llm_api_key: str = ""
    max_file_bytes: int = 5 * 1024 * 1024
    max_text_chars: int = 30000


@lru_cache
def settings() -> Settings:
    return Settings()

