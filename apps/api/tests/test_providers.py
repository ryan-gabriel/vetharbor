"""Provider contracts: determinism, the 768-dimension invariant, and the
tools-prohibition guard (ADR-005; TESTING.md §7.6).

Gemini is exercised with a stub SDK module, never the network: CI must not
spend quota (AGENTS.md §3.5).
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from app.core.config import Settings
from app.providers import gemini as gemini_module
from app.providers.base import (
    EMBEDDING_DIMENSIONS,
    LLMProvider,
    ProviderDimensionError,
    ensure_dimensions,
)
from app.providers.fakes import FakeEmbeddings, FakeLLM
from app.providers.gemini import GeminiEmbeddings, GeminiLLM, GeminiProviderError
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
    for provider in (FakeLLM, GeminiLLM, LLMProvider):
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


def test_registry_resolves_fake_by_default() -> None:
    settings = Settings(_env_file=None)
    assert isinstance(get_embedding_provider(settings), FakeEmbeddings)
    assert isinstance(get_llm_provider(settings), FakeLLM)


def test_registry_defers_unbuilt_providers() -> None:
    for name in ("ollama", "fastembed", "sentence-transformers"):
        with pytest.raises(ProviderNotAvailableError, match="M4"):
            get_embedding_provider(Settings(_env_file=None, embedding_provider=name))
        with pytest.raises(ProviderNotAvailableError, match="M4"):
            get_llm_provider(Settings(_env_file=None, llm_provider=name))


def test_registry_refuses_gemini_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # Safe by default: selecting a paid provider without a credential is a
    # configuration error, not a half-working client (AGENTS.md §3.5).
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    for factory, field in (
        (get_embedding_provider, "embedding_provider"),
        (get_llm_provider, "llm_provider"),
    ):
        with pytest.raises(GeminiProviderError, match="GEMINI_API_KEY"):
            factory(Settings(_env_file=None, **{field: "gemini"}))


class _StubEmbedding:
    def __init__(self, values: list[float]) -> None:
        self.values = values


class _StubEmbedResponse:
    def __init__(self, count: int, width: int) -> None:
        self.embeddings = [_StubEmbedding([0.3] * width) for _ in range(count)]


class _StubModels:
    def __init__(self) -> None:
        self.embed_kwargs: dict[str, Any] = {}
        self.generate_kwargs: dict[str, Any] = {}
        self.embed_width = EMBEDDING_DIMENSIONS

    def embed_content(self, **kwargs: Any) -> _StubEmbedResponse:
        self.embed_kwargs = kwargs
        return _StubEmbedResponse(len(kwargs["contents"]), self.embed_width)

    def generate_content(self, **kwargs: Any) -> Any:
        self.generate_kwargs = kwargs

        class _Response:
            text = '{"ok": true}'

        return _Response()


class _StubClient:
    def __init__(self, models: _StubModels) -> None:
        self.models = models


class _StubGenai:
    def __init__(self, models: _StubModels) -> None:
        self._models = models

    def Client(self, api_key: str) -> _StubClient:
        assert api_key == "test-key"
        return _StubClient(self._models)


@pytest.fixture
def stub_sdk(monkeypatch: pytest.MonkeyPatch) -> _StubModels:
    models = _StubModels()
    monkeypatch.setattr(gemini_module, "_genai", lambda: _StubGenai(models))
    return models


def test_gemini_embedding_requests_768_dimensions(stub_sdk: _StubModels) -> None:
    vectors = GeminiEmbeddings(api_key="test-key").embed(["synthetic cv a", "synthetic cv b"])
    assert len(vectors) == 2
    assert all(len(v) == EMBEDDING_DIMENSIONS for v in vectors)
    assert stub_sdk.embed_kwargs["config"].output_dimensionality == EMBEDDING_DIMENSIONS
    assert stub_sdk.embed_kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"


def test_gemini_embeddings_are_unit_length(stub_sdk: _StubModels) -> None:
    # Reduced-dimension Gemini vectors are not normalised by the API.
    vector = GeminiEmbeddings(api_key="test-key").embed(["x"])[0]
    norm = sum(v * v for v in vector) ** 0.5
    assert norm == pytest.approx(1.0)


def test_gemini_embedding_rejects_wrong_width(stub_sdk: _StubModels) -> None:
    stub_sdk.embed_width = 384
    with pytest.raises(ProviderDimensionError, match="expected 768"):
        GeminiEmbeddings(api_key="test-key").embed(["x"])


def test_gemini_llm_sends_no_tools(stub_sdk: _StubModels) -> None:
    result = GeminiLLM(api_key="test-key").complete(system="s", prompt="p")
    config = stub_sdk.generate_kwargs["config"]
    assert config.tools == []
    assert config.tool_config is None
    assert config.system_instruction == "s"
    assert result.answer == '{"ok": true}'


def test_gemini_llm_uses_json_mode_for_structured_output(stub_sdk: _StubModels) -> None:
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    GeminiLLM(api_key="test-key").complete(system="s", prompt="p", response_schema=schema)
    config = stub_sdk.generate_kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == schema
