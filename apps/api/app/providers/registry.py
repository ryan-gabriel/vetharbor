"""Provider selection by profile (ARCHITECTURE.md §2, §5).

``fake`` is the default everywhere; CI pins it so no test can spend quota
(AGENTS.md §3.5). ``GeminiEmbeddings``/``GeminiLLM`` (lite) are available and
fail fast when ``GEMINI_API_KEY`` is absent - selection never constructs a
client at import time. ``FastembedONNX`` (dev) and
``SentenceTransformersMPNet``/``OllamaLLM`` (full) land in M4.
"""

from __future__ import annotations

from app.core.config import Settings
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.fakes import FakeEmbeddings, FakeLLM
from app.providers.gemini import GeminiEmbeddings, GeminiLLM


class ProviderNotAvailableError(RuntimeError):
    def __init__(self, name: str, milestone: str) -> None:
        super().__init__(
            f"provider '{name}' is not implemented until {milestone}; "
            "use 'fake' in dev and CI (AGENTS.md §3.5)"
        )


def _gemini_key(settings: Settings) -> str | None:
    """Read the key from Settings so it can also come from ``.env``; the
    adapter still fails fast if it is missing (AGENTS.md §3.4)."""
    secret = settings.gemini_api_key
    return secret.get_secret_value() if secret is not None else None


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    match settings.embedding_provider:
        case "fake":
            return FakeEmbeddings()
        case "gemini":
            return GeminiEmbeddings(
                api_key=_gemini_key(settings),
                model=settings.gemini_embedding_model,
            )
        case name:
            raise ProviderNotAvailableError(name, "M4")


def get_llm_provider(settings: Settings) -> LLMProvider:
    match settings.llm_provider:
        case "fake":
            return FakeLLM()
        case "gemini":
            return GeminiLLM(
                api_key=_gemini_key(settings),
                model=settings.gemini_llm_model,
            )
        case name:
            raise ProviderNotAvailableError(name, "M4")
