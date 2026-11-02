"""Settings from the environment (pydantic-settings). No secrets have defaults."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Profile = Literal["dev", "lite", "full"]


class Settings(BaseSettings):
    """Runtime configuration.

    The three run profiles are defined in SPEC.md §5 and ARCHITECTURE.md §2.
    Providers are selected by name; every adapter satisfies the 768-dimension
    contract of ADR-005. CI pins both provider settings to ``fake``.
    """

    model_config = SettingsConfigDict(
        env_prefix="VETHARBOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    profile: Profile = "dev"
    environment: Literal["test", "dev", "prod"] = "dev"

    # Local default points at infra/compose/dev.yaml. Nothing here is a
    # credential: AGENTS.md §3.4 keeps real credentials in the environment.
    database_url: str = "postgresql+psycopg://vetharbor:vetharbor@localhost:55432/vetharbor"

    llm_provider: str = "fake"
    embedding_provider: str = "fake"

    # OIDC wiring arrives in M3 (ADR-009); fields exist so config shape is stable.
    auth_issuer: str | None = None
    auth_audience: str | None = None

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
