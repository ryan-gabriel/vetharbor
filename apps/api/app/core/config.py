"""Settings from the environment (pydantic-settings). No secrets have defaults."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Profile = Literal["dev", "lite", "full"]

#: Model ids are configuration, not code: Google retires model names on a
#: schedule, and redeploying to rename one is cheaper than a migration.
#: Verified 2026-11-05 against a real free-tier key:
#:   - ``gemini-2.5-flash``  -> 404 for new accounts
#:   - ``gemini-3.8-flash``  -> 503 on every attempt
#:   - ``gemini-3.1-flash-lite`` -> answered, honoured ``response_json_schema``
#:   - ``gemini-3.5-flash-lite`` -> available and working
#: Both ``gemini-embedding-2`` and ``gemini-embedding-001`` returned 768-d
#: unit vectors. Re-check before changing these (CONTEXT.md §6).
GEMINI_DEFAULT_EMBEDDING_MODEL = "gemini-embedding-2"
GEMINI_DEFAULT_LLM_MODEL = "gemini-3.5-flash-lite"


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
        populate_by_name=True,
    )

    profile: Profile = "dev"
    environment: Literal["test", "dev", "prod"] = "dev"

    # Local default points at infra/compose/dev.yaml. Nothing here is a
    # credential: AGENTS.md §3.4 keeps real credentials in the environment.
    database_url: str = "postgresql+psycopg://vetharbor:vetharbor@localhost:55432/vetharbor"

    llm_provider: str = "fake"
    embedding_provider: str = "fake"

    # Accepted as both ``GEMINI_API_KEY`` and ``VETHARBOR_GEMINI_API_KEY`` so
    # .env stays portable with the vendor's own docs. SecretStr keeps it out of
    # reprs and logs; there is no default, so a missing key fails loudly only
    # when a Gemini adapter is actually selected (AGENTS.md §3.4).
    gemini_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "VETHARBOR_GEMINI_API_KEY"),
    )

    # Model ids are configuration, not code: Google retires model names on a
    # schedule, and re-deploying to rename one is cheaper than a migration.
    gemini_embedding_model: str = GEMINI_DEFAULT_EMBEDDING_MODEL
    gemini_llm_model: str = GEMINI_DEFAULT_LLM_MODEL

    # OIDC wiring arrives in M3 (ADR-009); fields exist so config shape is stable.
    auth_issuer: str | None = None
    auth_audience: str | None = None

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
