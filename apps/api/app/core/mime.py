"""MIME detection from magic bytes and the upload allow-list.

The declared MIME from the client is never trusted; the detected MIME from
magic bytes is the authority. A mismatch is a rejection event, not a warning.
"""

from __future__ import annotations

import filetype  # type: ignore[import-untyped]

# Allowed MIME types and their document kinds.
ALLOWED_MIMES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}

# Maps MIME type to the document_kind enum value.
MIME_TO_KIND: dict[str, str] = {
    "application/pdf": "cv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "cv",
    "text/plain": "cv",
}

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PAGE_COUNT = 60


def detect_mime(data: bytes) -> str | None:
    """Detect MIME type from magic bytes. Returns None if unknown."""
    kind = filetype.guess(data)
    if kind is None:
        # filetype doesn't detect plain text; check manually.
        try:
            data.decode("utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            return None
    mime: str = kind.mime
    return mime


def is_allowed_mime(mime: str) -> bool:
    return mime in ALLOWED_MIMES


def is_archive_or_macro(mime: str, filename: str) -> bool:
    """Detect archives and macro-enabled formats by extension and MIME."""
    lower = filename.lower()
    archive_exts = {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".tgz"}
    macro_exts = {".docm", ".xlsm", ".pptm", ".dotm"}
    if any(lower.endswith(ext) for ext in archive_exts | macro_exts):
        return True
    archive_mimes = {
        "application/zip",
        "application/x-tar",
        "application/gzip",
        "application/x-7z-compressed",
        "application/x-rar-compressed",
    }
    return mime in archive_mimes
