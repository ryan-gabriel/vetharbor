"""Guard: the synthetic corpus must never contain real-data markers
(AGENTS.md §3.2; scripts/banned_words.txt)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.security, pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[3]
BANNED_PATH = REPO_ROOT / "scripts" / "banned_words.txt"
CORPUS_PATH = REPO_ROOT / "scripts" / "generated" / "corpus.jsonl"


def _banned_terms() -> list[str]:
    terms: list[str] = []
    for line in BANNED_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        terms.append(line)
    return terms


def test_banned_words_file_exists_and_nonempty() -> None:
    assert BANNED_PATH.is_file()
    assert len(_banned_terms()) >= 5


def test_corpus_contains_no_banned_terms() -> None:
    if not CORPUS_PATH.exists():
        pytest.skip("corpus not generated yet; run scripts/generate_synthetic_corpus.py")
    terms = _banned_terms()
    lowered_terms = [t.lower() for t in terms]
    hits: list[str] = []
    for line_no, line in enumerate(CORPUS_PATH.read_text(encoding="utf-8").splitlines(), 1):
        low = line.lower()
        for term in lowered_terms:
            if term in low:
                hits.append(f"line {line_no}: {term!r}")
    assert not hits, f"banned terms found in corpus: {hits}"