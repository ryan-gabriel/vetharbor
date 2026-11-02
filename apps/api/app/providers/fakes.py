"""Deterministic fake providers. The only providers allowed in CI (TESTING.md §1)."""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Sequence
from typing import Any

from app.providers.base import EMBEDDING_DIMENSIONS, LLMResult, ensure_dimensions


class FakeEmbeddings:
    """Stable pseudo-embeddings derived from text content.

    Same input -> same 768-d vector on every run and Python version
    (``random.Random`` streams are documented-stable). Not semantically
    meaningful: tests may assert determinism, dimensions and tenant-scoped
    retrieval plumbing - never similarity quality.
    """

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rng = random.Random(seed)
        raw = [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSIONS)]
        norm = math.sqrt(sum(v * v for v in raw)) or 1.0
        return ensure_dimensions([v / norm for v in raw])


class FakeLLM:
    """Canned deterministic completions; records calls for assertions."""

    def __init__(self, fixed_answer: str = "fake answer") -> None:
        self.fixed_answer = fixed_answer
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        self.calls.append({"system": system, "prompt": prompt, "schema": response_schema})
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        return LLMResult(answer=f"{self.fixed_answer}::{digest}")
