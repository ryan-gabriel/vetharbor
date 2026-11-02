"""Provider contracts for embeddings and LLM calls (ARCHITECTURE.md §5)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

#: Single dimension standard across every profile and adapter (ADR-005).
EMBEDDING_DIMENSIONS = 768


class ProviderError(Exception):
    """Base for provider failures."""


class ProviderDimensionError(ProviderError):
    """An adapter produced a vector that is not 768-dimensional.

    This is a schema-breaking bug, not a runtime hiccup (ADR-005): fail loudly,
    before anything is persisted.
    """


@runtime_checkable
class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input text, each exactly EMBEDDING_DIMENSIONS long."""
        ...


@dataclass(frozen=True)
class LLMResult:
    answer: str
    refusal_reason: str | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)


@runtime_checkable
class LLMProvider(Protocol):
    """Complete a prompt with structured output support.

    Hard rule (AGENTS.md §8): implementations never expose tools or function
    calling. There is deliberately no ``tools`` parameter; adding one is a
    review-blocking change. Document content is data, never instructions
    (SPEC.md FR-504).
    """

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult: ...


def ensure_dimensions(vector: Sequence[float]) -> list[float]:
    """Validate one embedding at the adapter boundary (ADR-005)."""
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ProviderDimensionError(
            f"embedding has {len(vector)} dimensions, expected {EMBEDDING_DIMENSIONS}"
        )
    return list(vector)
