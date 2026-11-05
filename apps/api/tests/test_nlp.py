"""NLP entity extraction tests (M1-3)."""

from __future__ import annotations

import pytest

from app.modules.nlp.service import NLPService

pytestmark = pytest.mark.unit


def test_nlp_extracts_skills() -> None:
    text = "Python, FastAPI, Postgres, Docker, and Kubernetes experience."
    result = NLPService().process(text)
    skills = [e for e in result.entities if e.label == "SKILL"]
    normalised = {e.normalised for e in skills}
    assert "python" in normalised
    assert "fastapi" in normalised
    assert "postgres" in normalised
    assert "docker" in normalised
    assert "kubernetes" in normalised


def test_nlp_extracts_years() -> None:
    text = "5 years of experience building software."
    result = NLPService().process(text)
    years = [e for e in result.entities if e.label == "YEARS"]
    assert len(years) >= 1
    assert years[0].normalised == "5"


def test_nlp_extracts_email_as_pii() -> None:
    text = "Contact: test@example.com"
    result = NLPService().process(text)
    contacts = [e for e in result.entities if e.label == "CONTACT"]
    assert len(contacts) >= 1
    assert contacts[0].is_pii is True


def test_nlp_offsets_valid() -> None:
    text = "Python developer with 3 years experience. Skills: React, TypeScript."
    result = NLPService().process(text)
    for e in result.entities:
        assert 0 <= e.char_start < e.char_end <= len(text)
        assert text[e.char_start : e.char_end] == e.text


def test_nlp_deduplicates_overlapping() -> None:
    text = "Python"
    result = NLPService().process(text)
    skills = [e for e in result.entities if e.label == "SKILL"]
    # Should have exactly one skill entity for "Python".
    assert len(skills) == 1


def test_nlp_extracts_role_title() -> None:
    text = "Backend Engineer with 5 years experience."
    result = NLPService().process(text)
    roles = [e for e in result.entities if e.label == "ROLE"]
    assert len(roles) >= 1


def test_nlp_pipeline_version() -> None:
    result = NLPService().process("test")
    assert "spacy" in result.pipeline_version
    assert "gazetteer" in result.pipeline_version