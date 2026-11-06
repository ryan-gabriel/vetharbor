"""Subprocess text extractor. Invoked as ``python -m app.core.extractor <path> <mime>``.

Reads the file at ``path``, extracts the text layer, and prints a JSON object
to stdout. Exit code 0 on success, 1 on failure. Never renders active content.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _extract_pdf(path: Path) -> tuple[str, int, list[str]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ValueError("encrypted PDF")
    pages = reader.pages
    if len(pages) > 60:
        raise ValueError(f"page_count {len(pages)} exceeds limit 60")
    texts: list[str] = []
    warnings: list[str] = []
    for page in pages:
        t = page.extract_text() or ""
        texts.append(t)
        # Detect hidden/zero-size text where pypdf exposes font info.
        # Best-effort: check for very short extraction relative to page size.
        if len(t.strip()) < 10:
            warnings.append("hidden_text")
    return "\n\n".join(texts), len(pages), warnings


def _extract_docx(path: Path) -> tuple[str, int, list[str]]:
    import xml.etree.ElementTree as ET
    import zipfile

    if not zipfile.is_zipfile(path):
        raise ValueError("not a valid DOCX")
    with zipfile.ZipFile(path) as z:
        # Reject macro-enabled documents.
        if any(n.endswith(".bin") or "vbaProject" in n for n in z.namelist()):
            raise ValueError("macro-enabled document rejected")
        try:
            xml = z.read("word/document.xml")
        except KeyError as exc:
            raise ValueError("missing document.xml") from exc
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    tree = ET.fromstring(xml)
    paragraphs: list[str] = []
    for p in tree.iter(f"{ns}p"):
        runs = [t.text or "" for t in p.iter(f"{ns}t")]
        paragraphs.append("".join(runs))
    text = "\n".join(paragraphs)
    return text, 1, []


def _extract_txt(path: Path) -> tuple[str, int, list[str]]:
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    return text, 1, []


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: extractor.py <path> <mime>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    mime = sys.argv[2]

    try:
        if mime == "application/pdf":
            text, pages, warnings = _extract_pdf(path)
        elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text, pages, warnings = _extract_docx(path)
        elif mime == "text/plain":
            text, pages, warnings = _extract_txt(path)
        else:
            print(f"unsupported mime: {mime}", file=sys.stderr)
            return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # Deduplicate warning flags.
    warnings = sorted(set(warnings))
    result = {"text": text, "page_count": pages, "warning_flags": warnings}
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
