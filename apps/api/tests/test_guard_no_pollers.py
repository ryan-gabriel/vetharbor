"""Guard: nothing in ``app/`` may poll free tiers (AGENTS.md §3.6/3.7;
TESTING.md §5.13). The scale-to-zero rule must be enforced by a build, not a
code-review comment."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.security, pytest.mark.unit]

APP_ROOT = Path(__file__).resolve().parents[1] / "app"

FORBIDDEN: dict[str, re.Pattern[str]] = {
    "busy loop": re.compile(r"while\s+True"),
    "async sleep": re.compile(r"asyncio\.sleep\("),
    "time sleep": re.compile(r"time\.sleep\("),
    "cron library": re.compile(r"APScheduler|apscheduler", re.IGNORECASE),
    "broker": re.compile(r"import\s+(celery|dramatiq)", re.IGNORECASE),
}


def test_guard_is_scanning_a_real_tree() -> None:
    files = list(APP_ROOT.rglob("*.py"))
    assert len(files) >= 10, "guard found almost nothing to scan - path drift?"


@pytest.mark.parametrize("label", list(FORBIDDEN))
def test_no_polling_or_keepalive_pattern_in_app(label: str) -> None:
    hits = [
        f"{path.relative_to(APP_ROOT)}:{line_no}"
        for path in APP_ROOT.rglob("*.py")
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if FORBIDDEN[label].search(line)
    ]
    assert not hits, f"{label} found at {hits} - pollers defeat Neon scale-to-zero"
