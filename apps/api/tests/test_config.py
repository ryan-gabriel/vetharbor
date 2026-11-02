"""Settings parse and profile switch (SPEC.md §5)."""

from __future__ import annotations

import pytest

from app.core.config import Settings

pytestmark = pytest.mark.unit


def test_defaults_are_the_dev_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VETHARBOR_PROFILE", raising=False)
    settings = Settings(_env_file=None)
    assert settings.profile == "dev"
    assert settings.llm_provider == "fake"
    assert settings.embedding_provider == "fake"


def test_profile_comes_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VETHARBOR_PROFILE", "lite")
    assert Settings(_env_file=None).profile == "lite"


def test_unknown_profile_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VETHARBOR_PROFILE", "staging")
    with pytest.raises(ValueError, match="profile"):
        Settings(_env_file=None)


def test_database_url_default_points_at_compose() -> None:
    assert ":55432/" in Settings(_env_file=None).database_url
