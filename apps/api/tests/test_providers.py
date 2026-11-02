"""Provider contracts: determinism, the 768-dimension invariant, and the
tools-prohibition guard (ADR-005; TESTING.md §7.6)."""

from __future__ import annotations

import inspect

import pytest

from app.core.config import Settings
from app.providers.base import (
    EMBEDDING_DIMENSIONS,
    LLMProvider,
    ProviderDimensionError,
    ensure_dimensions,
)
from app.providers.fakes import FakeEmbeddings, FakeLLM
from app.providers.registry import (
    ProviderNotAvailableError,
    get_embedding_provider,
    get_llm_provider,
)

pytestmark = pytest.mark.unit


def test_fake_embeddings_are_deterministic_and_768d() -> None:
    provider = FakeEmbeddings()
    first = provider.embed(["Synthetic CV text."])
    second = provider.embed(["Synthetic CV text."])
    assert first == second
    assert all(len(v) == EMBEDDING_DIMENSIONS for v in first)


def test_fake_embeddings_differ_for_different_text() -> None:
    provider = FakeEmbeddings()
    a, b = provider.embed(["python, kubernetes", "marketing, canvassing"])
    assert a != b


@pytest.mark.parametrize("bad_len", [384, 3072, 0])
def test_ensure_dimensions_rejects_wrong_vector(bad_len: int) -> None:
    with pytest.raises(ProviderDimensionError, match="expected 768"):
        ensure_dimensions([0.0] * bad_len)


def test_llm_surface_has_no_tools_parameter() -> None:
    # The guard from TESTING.md §7.6: adding a tools param must fail CI.
    for provider in (FakeLLM, LLMProvider):
        params = inspect.signature(provider.complete).parameters
        assert "tools" not in params
        assert set(params) <= {"self", "system", "prompt", "response_schema"}


def test_fake_llm_is_deterministic_and_records_calls() -> None:
    provider = FakeLLM()
    r1 = provider.complete(system="s", prompt="hello")
    r2 = provider.complete(system="s", prompt="hello")
    assert r1.answer == r2.answer
    assert provider.calls[-1]["prompt"] == "hello"
    assert provider.calls[-1]["schema"] is None


def test_registry_resolves_fake_and_defers_real_providers() -> None:
    settings = Settings(_env_file=None)
    assert isinstance(get_embedding_provider(settings), FakeEmbeddings)
    assert isinstance(get_llm_provider(settings), FakeLLM)

    for name in ("gemini", "ollama", "fastembed", "sentence-transformers"):
        with pytest.raises(ProviderNotAvailableError, match="M4"):
            get_embedding_provider(Settings(_env_file=None, embedding_provider=name))
        with pytest.raises(ProviderNotAvailableError, match="M4"):
            get_llm_provider(Settings(_env_file=None, llm_provider=name))
