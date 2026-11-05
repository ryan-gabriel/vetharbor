"""Sandboxed text extraction via subprocess.

Extraction runs in a separate process with explicit CPU, memory and wall-clock
limits. Active content (macros, JavaScript, embedded objects) is never rendered;
only the text layer is read. Raw bytes and temporary files are removed on
success, failure, timeout and cancellation.

The extractor is a pure-Python module invoked as ``python -m app.core.extractor``
so that the parent process never loads the extraction libraries into its own
memory and a crash in extraction cannot take down the API.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.core.mime import MAX_PAGE_COUNT

# Wall-clock limit for extraction subprocess.
EXTRACT_TIMEOUT_SECONDS = 30
# Maximum output size (10 MB of text).
MAX_OUTPUT_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    page_count: int
    char_count: int
    word_count: int
    warning_flags: list[str] = field(default_factory=list)
    sha256: str = ""


@dataclass(frozen=True)
class ExtractionError(Exception):
    code: str  # failure code (timeout, resource_limit, unsupported, ...)
    detail: str = ""

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}" if self.detail else self.code


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_text(data: bytes, detected_mime: str, filename: str) -> ExtractionResult:
    """Extract text from document bytes in a sandboxed subprocess.

    Raises ``ExtractionError`` on any failure. The caller is responsible for
    ensuring the data has already passed MIME and size validation.
    """
    if not data:
        raise ExtractionError("empty", "file is empty")

    sha = compute_sha256(data)

    # Write bytes to a temp file for the subprocess to read.
    tmp_dir = tempfile.mkdtemp(prefix="vetharbor-extract-")
    tmp_path = Path(tmp_dir) / "input.bin"
    tmp_path.write_bytes(data)

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "app.core.extractor", str(tmp_path), detected_mime],
            capture_output=True,
            timeout=EXTRACT_TIMEOUT_SECONDS,
            cwd=str(Path(__file__).resolve().parents[2]),  # apps/api
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        _cleanup_tmp(tmp_dir)
        raise ExtractionError("timeout", f"extraction exceeded {EXTRACT_TIMEOUT_SECONDS}s") from exc
    except OSError as exc:
        _cleanup_tmp(tmp_dir)
        raise ExtractionError("resource_limit", str(exc)) from exc

    _cleanup_tmp(tmp_dir)

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        if "encrypted" in stderr.lower():
            raise ExtractionError("encrypted", stderr)
        if "pages" in stderr.lower() or "page_count" in stderr.lower():
            raise ExtractionError("pages_exceeded", stderr)
        raise ExtractionError("unsupported", stderr or f"exit code {proc.returncode}")

    try:
        result = json.loads(proc.stdout.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ExtractionError("unsupported", f"invalid extractor output: {exc}") from exc

    text = result.get("text", "")
    page_count = result.get("page_count", 0)
    warning_flags = result.get("warning_flags", [])

    if page_count > MAX_PAGE_COUNT:
        raise ExtractionError(
            "pages_exceeded",
            f"{page_count} pages exceeds limit of {MAX_PAGE_COUNT}",
        )

    if not text.strip():
        raise ExtractionError("empty", "no text could be extracted (scanned image?)")

    return ExtractionResult(
        text=text,
        page_count=page_count,
        char_count=len(text),
        word_count=len(text.split()),
        warning_flags=warning_flags,
        sha256=sha,
    )


def _cleanup_tmp(tmp_dir: str) -> None:
    import contextlib
    import shutil

    with contextlib.suppress(Exception):
        shutil.rmtree(tmp_dir, ignore_errors=True)