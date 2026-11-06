"""Gemini provider adapters (lite profile).

Implements ``EmbeddingProvider`` and ``LLMProvider`` from ``base.py`` behind the
same interfaces as the fakes, so no module outside ``app/providers/`` imports
``google.genai`` (AGENTS.md §8). Real calls happen only when
``VETHARBOR_LLM_PROVIDER=gemini`` / ``VETHARBOR_EMBEDDING_PROVIDER=gemini`` is
set **and** a key is configured; CI pins both to ``fake`` (AGENTS.md §3.5).

Hard rules enforced here:

- No tools and no function calling, ever. ``tools=[]`` is sent explicitly on
  every generation call (AGENTS.md §8).
- Every embedding is validated to 768 dimensions at the boundary before it can
  be persisted (ADR-005).
- Content is synthetic by policy (ADR-010); this adapter cannot enforce it, so
  the caller must never hand it a real CV.
"""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from typing import Any

from app.core.config import GEMINI_DEFAULT_EMBEDDING_MODEL, GEMINI_DEFAULT_LLM_MODEL
from app.providers.base import (
    EMBEDDING_DIMENSIONS,
    LLMResult,
    ProviderError,
    ensure_dimensions,
)

#: Kept as module aliases so callers can reference the defaults without
#: importing ``app.core.config``.
DEFAULT_EMBEDDING_MODEL = GEMINI_DEFAULT_EMBEDDING_MODEL
DEFAULT_LLM_MODEL = GEMINI_DEFAULT_LLM_MODEL


class GeminiProviderError(ProviderError):
    """Misconfiguration (no key) or a failed Gemini call."""


def _resolve_api_key(api_key: str | None) -> str:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise GeminiProviderError(
            "GEMINI_API_KEY is not set; add it to apps/api/.env (git-ignored) "
            "or the deployment environment (AGENTS.md §3.4)"
        )
    return key


def _genai() -> Any:
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise GeminiProviderError(
            "google-genai is not installed; run `uv sync` in apps/api"
        ) from exc
    return genai


def _unit(vector: list[float]) -> list[float]:
    """Normalise to unit length.

    Reduced-dimension Gemini embeddings are not pre-normalised, and the fakes
    are, so normalising here keeps both adapters on the same footing for any
    metric we add later.
    """
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


class GeminiEmbeddings:
    """Gemini embeddings pinned to 768 dimensions."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        self._client = _genai().Client(api_key=_resolve_api_key(api_key))
        self._model = model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        from google.genai import types

        result = self._client.models.embed_content(
            model=self._model,
            contents=list(texts),
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSIONS,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )
        vectors: list[list[float]] = []
        for embedding in result.embeddings or []:
            vectors.append(_unit(ensure_dimensions(embedding.values or [])))
        if len(vectors) != len(texts):
            raise GeminiProviderError(f"expected {len(texts)} embeddings, received {len(vectors)}")
        return vectors


class GeminiLLM:
    """Gemini for advisory prose only - no tools, no function calling."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_LLM_MODEL,
    ) -> None:
        self._client = _genai().Client(api_key=_resolve_api_key(api_key))
        self._model = model

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            # Hard rule: the client never gets tools or function calling
            # (AGENTS.md §8). Sent explicitly so a library default cannot
            # re-introduce them.
            tools=[],
            temperature=0.2,
        )
        if response_schema is not None:
            config.response_mime_type = "application/json"
            config.response_json_schema = response_schema

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=config,
        )
        return LLMResult(answer=response.text or "")
