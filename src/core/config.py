from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = Field(default=...)
    JWT_SECRET_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = (
        "http://localhost:8000/auth/google/callback"
    )
    FRONTEND_URL: str = "http://localhost:8000/docs"
    AUTH_COOKIE_SECURE: bool = True
    ACCESS_TOKEN_MINUTES: int = 180
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
                or                 parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or (port is not None and not 1 <= port <= 65535)
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

    @field_validator("FRONTEND_URL")
    @classmethod
    def validate_frontend_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        try:
            port = parsed.port
        except ValueError as error:
            raise ValueError("FRONTEND_URL contains an invalid port.") from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or (port is not None and not 1 <= port <= 65535)
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ValueError(
                "FRONTEND_URL must be an HTTP(S) URL without a query or fragment."
            )
        return value

    @field_validator("GOOGLE_REDIRECT_URI")
    @classmethod
    def validate_google_redirect_uri(cls, value: str) -> str:
        parsed = urlsplit(value)
        try:
            port = parsed.port
        except ValueError as error:
            raise ValueError(
                "GOOGLE_REDIRECT_URI contains an invalid port."
            ) from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or (port is not None and not 1 <= port <= 65535)
            or parsed.path != "/auth/google/callback"
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ValueError(
                "GOOGLE_REDIRECT_URI must end with /auth/google/callback "
                "and cannot contain a query or fragment."
            )
        return value

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