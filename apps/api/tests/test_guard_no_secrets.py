"""Guard: the repository is public; credential shapes must never be committed
(AGENTS.md §3.4; TESTING.md §12 free-tier guard jobs). This is the cheap
in-repo pre-flight; gitleaks in CI is the belt to this braces (M6)."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.security, pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[3]

PATTERNS: dict[str, re.Pattern[str]] = {
    "aws access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github token": re.compile(r"(ghp|github_pat)_[A-Za-z0-9_]{20,}"),
    "openai-style key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "google api key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
}

SKIP_DIRS = {".git", "node_modules", ".venv", "dist", "build", ".agents", "__pycache__"}
SKIP_FILES = {"uv.lock", "package-lock.json", "yarn.lock", "PROJECT_PLAN_AUDIT.md"}
MAX_BYTES = 400_000


def _tracked_text_files() -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name in SKIP_FILES:
                continue
            path = Path(dirpath) / name
            try:
                if path.stat().st_size > MAX_BYTES:
                    continue
                path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            files.append(path)
    return files


def test_guard_scans_a_real_repository() -> None:
    files = _tracked_text_files()
    assert len(files) >= 30, "secret guard found almost nothing to scan - path drift?"


@pytest.mark.parametrize("label", list(PATTERNS))
def test_no_credential_shapes_in_repo(label: str) -> None:
    pattern = PATTERNS[label]
    hits: list[str] = []
    for path in _tracked_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if pattern.search(text):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert not hits, f"{label} found in {hits}"
