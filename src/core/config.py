from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = Field(default=...)

@lru_cache
def get_settings() -> Settings:
    """
    Instantiates Settings once and caches it in memory.
    Prevents repeated disk I/O on every request or dependency injection.
    """
    return Settings()


# Exported singleton instance for global imports
settings = get_settings()