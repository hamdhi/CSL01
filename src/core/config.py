from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = Field(default=...)
    JWT_SECRET_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 14
    ALLOWED_ORIGINS: str = ""

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        for origin in origins:
            parsed = urlsplit(origin)
            try:
                port = parsed.port
            except ValueError as error:
                raise ValueError(
                    f"Invalid port in allowed origin: {origin!r}."
                ) from error
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or (port is not None and not 1 <= port <= 65535)
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                raise ValueError(
                    "ALLOWED_ORIGINS must be comma-separated HTTP(S) origins "
                    "without paths, queries, fragments, or wildcards."
                )
        return ",".join(origins)

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin for origin in self.ALLOWED_ORIGINS.split(",") if origin
        ]

@lru_cache
def get_settings() -> Settings:
    """
    Instantiates Settings once and caches it in memory.
    Prevents repeated disk I/O on every request or dependency injection.
    """
    return Settings()


# Exported singleton instance for global imports
settings = get_settings()