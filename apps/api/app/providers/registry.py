"""Provider selection by profile (ARCHITECTURE.md §2, §5).

Real adapters - ``GeminiEmbeddings``/``GeminiLLM`` (lite), ``FastembedONNX``
(dev), ``SentenceTransformersMPNet``/``OllamaLLM`` (full) - land in M4.
Only ``fake`` is available before then, so no code path can accidentally
spend quota or require a credential (AGENTS.md §3.5).
"""

from __future__ import annotations

from app.core.config import Settings
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.fakes import FakeEmbeddings, FakeLLM


class ProviderNotAvailableError(RuntimeError):
    def __init__(self, name: str, milestone: str) -> None:
        super().__init__(
            f"provider '{name}' is not implemented until {milestone}; "
            "use 'fake' in dev and CI (AGENTS.md §3.5)"
        )


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    match settings.embedding_provider:
        case "fake":
            return FakeEmbeddings()
        case name:
            raise ProviderNotAvailableError(name, "M4")


def get_llm_provider(settings: Settings) -> LLMProvider:
    match settings.llm_provider:
        case "fake":
            return FakeLLM()
        case name:
            raise ProviderNotAvailableError(name, "M4")
