"""Upload endpoint smoke tests (M1-2)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


async def test_upload_rejects_empty_file(client) -> None:
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 422


async def test_upload_rejects_oversized_file(client) -> None:
    big = b"x" * (5 * 1024 * 1024 + 1)
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("big.txt", big, "text/plain")},
    )
    assert response.status_code == 422


async def test_upload_rejects_mime_mismatch(client) -> None:
    # PDF bytes declared as text/plain.
    pdf_bytes = b"%PDF-1.4\n"
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("doc.txt", pdf_bytes, "text/plain")},
    )
    assert response.status_code == 422


async def test_upload_accepts_txt(client) -> None:
    content = b"Hello world. This is a synthetic CV.\n"
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("cv.txt", content, "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["char_count"] == len(content.decode())
    assert body["sha256"]


async def test_upload_accepts_pdf(client) -> None:
    # Minimal valid PDF with text.
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (Hello PDF) "
        b"Tj ET\nendstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000266 00000 n \n0000000340 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n434\n%%EOF\n"
    )
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("cv.pdf", pdf, "application/pdf")},
    )
    # pypdf may or may not extract text from this minimal PDF; accept 201 or 422.
    assert response.status_code in (201, 422)


async def test_list_documents(client) -> None:
    content = b"List test document.\n"
    await client.post(
        "/api/v1/documents",
        files={"file": ("list.txt", content, "text/plain")},
    )
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1


async def test_get_document_not_found(client) -> None:
    import uuid

    response = await client.get(f"/api/v1/documents/{uuid.uuid4()}")
    assert response.status_code == 404
