"""NLP service — spaCy Matcher + EntityRuler + gazetteer.

Extracts entities (skills, roles, organisations, education, dates, years,
contact) from extracted text with character offsets into the exact text.
All rules are deterministic and versioned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import spacy
from spacy.matcher import Matcher, PhraseMatcher

from app.modules.nlp.gazetteer import GAZETTEER_VERSION, lookup

NLP_VERSION = f"spacy-en_core_web_sm-3.8+gazetteer-{GAZETTEER_VERSION}"

# Labels used in document_entities.label.
LABEL_SKILL = "SKILL"
LABEL_ROLE = "ROLE"
LABEL_ORG = "ORG"
LABEL_EDU = "EDU"
LABEL_DATE = "DATE"
LABEL_YEARS = "YEARS"
LABEL_CONTACT = "CONTACT"


@dataclass(frozen=True)
class Entity:
    label: str
    text: str
    normalised: str | None
    taxonomy: str | None
    confidence: float | None
    char_start: int
    char_end: int
    rule_id: str | None
    source: str  # ner, rule, regex, gazetteer
    is_pii: bool = False


@dataclass
class NLPResult:
    entities: list[Entity] = field(default_factory=list)
    pipeline_version: str = NLP_VERSION


# Regex patterns for structured extraction.
_YEARS_RE = re.compile(r"(\d+)\s*years?", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")
_DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
    re.IGNORECASE,
)

# Common role titles (rule-based, not NER).
_ROLE_TITLES = {
    "backend engineer",
    "frontend engineer",
    "data scientist",
    "software engineer",
    "devops engineer",
    "product manager",
    "engineering manager",
    "tech lead",
    "architect",
}

# Education keywords.
_EDU_KEYWORDS = {
    "bsc",
    "msc",
    "phd",
    "bachelor",
    "master",
    "doctorate",
    "degree",
    "university",
    "college",
}


def _load_nlp() -> spacy.language.Language:
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # Fall back to blank English pipeline (no NER model).
        nlp = spacy.blank("en")
        return nlp


class NLPService:
    def __init__(self) -> None:
        self._nlp = _load_nlp()
        self._matcher = Matcher(self._nlp.vocab)
        self._phrase_matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
        self._build_matchers()

    def _build_matchers(self) -> None:
        # Skill phrase matcher from gazetteer.
        patterns = [self._nlp.make_doc(skill) for skill in _all_skill_phrases()]
        self._phrase_matcher.add("SKILL", patterns)

    def process(self, text: str) -> NLPResult:
        doc = self._nlp(text)
        entities: list[Entity] = []

        # 1. spaCy NER (ORG, PERSON, DATE, etc.) — map to our labels.
        for ent in doc.ents:
            if ent.label_ in ("ORG", "GPE"):
                entities.append(
                    Entity(
                        label=LABEL_ORG,
                        text=ent.text,
                        normalised=None,
                        taxonomy=None,
                        confidence=None,
                        char_start=ent.start_char,
                        char_end=ent.end_char,
                        rule_id="spacy_ner",
                        source="ner",
                        is_pii=False,
                    )
                )
            elif ent.label_ == "DATE":
                entities.append(
                    Entity(
                        label=LABEL_DATE,
                        text=ent.text,
                        normalised=None,
                        taxonomy=None,
                        confidence=None,
                        char_start=ent.start_char,
                        char_end=ent.end_char,
                        rule_id="spacy_ner",
                        source="ner",
                        is_pii=False,
                    )
                )

        # 2. PhraseMatcher for skills (gazetteer).
        matches = self._phrase_matcher(doc)
        for _match_id, start, end in matches:
            span = doc[start:end]
            skill_text = span.text
            result = lookup(skill_text)
            normalised, taxonomy = result if result else (skill_text.lower(), "local")
            entities.append(
                Entity(
                    label=LABEL_SKILL,
                    text=skill_text,
                    normalised=normalised,
                    taxonomy=taxonomy,
                    confidence=0.9,
                    char_start=span.start_char,
                    char_end=span.end_char,
                    rule_id=f"gazetteer:{GAZETTEER_VERSION}",
                    source="gazetteer",
                    is_pii=False,
                )
            )

        # 3. Role titles (rule-based).
        text_lower = text.lower()
        for role in _ROLE_TITLES:
            for m in re.finditer(re.escape(role), text_lower):
                entities.append(
                    Entity(
                        label=LABEL_ROLE,
                        text=text[m.start() : m.end()],
                        normalised=role.replace(" ", "_"),
                        taxonomy="local",
                        confidence=0.8,
                        char_start=m.start(),
                        char_end=m.end(),
                        rule_id="role_title_rule",
                        source="rule",
                        is_pii=False,
                    )
                )

        # 4. Education keywords.
        for kw in _EDU_KEYWORDS:
            for m in re.finditer(r"\b" + re.escape(kw) + r"\b", text_lower):
                entities.append(
                    Entity(
                        label=LABEL_EDU,
                        text=text[m.start() : m.end()],
                        normalised=kw,
                        taxonomy="local",
                        confidence=0.7,
                        char_start=m.start(),
                        char_end=m.end(),
                        rule_id="edu_keyword_rule",
                        source="rule",
                        is_pii=False,
                    )
                )

        # 5. Years of experience.
        for m in _YEARS_RE.finditer(text):
            entities.append(
                Entity(
                    label=LABEL_YEARS,
                    text=m.group(0),
                    normalised=m.group(1),
                    taxonomy=None,
                    confidence=0.9,
                    char_start=m.start(),
                    char_end=m.end(),
                    rule_id="years_regex",
                    source="regex",
                    is_pii=False,
                )
            )

        # 6. Contact info (PII).
        for m in _EMAIL_RE.finditer(text):
            entities.append(
                Entity(
                    label=LABEL_CONTACT,
                    text=m.group(0),
                    normalised="email",
                    taxonomy=None,
                    confidence=1.0,
                    char_start=m.start(),
                    char_end=m.end(),
                    rule_id="email_regex",
                    source="regex",
                    is_pii=True,
                )
            )
        for m in _PHONE_RE.finditer(text):
            entities.append(
                Entity(
                    label=LABEL_CONTACT,
                    text=m.group(0),
                    normalised="phone",
                    taxonomy=None,
                    confidence=1.0,
                    char_start=m.start(),
                    char_end=m.end(),
                    rule_id="phone_regex",
                    source="regex",
                    is_pii=True,
                )
            )

        # 7. Dates.
        for m in _DATE_RE.finditer(text):
            entities.append(
                Entity(
                    label=LABEL_DATE,
                    text=m.group(0),
                    normalised=None,
                    taxonomy=None,
                    confidence=0.8,
                    char_start=m.start(),
                    char_end=m.end(),
                    rule_id="date_regex",
                    source="regex",
                    is_pii=False,
                )
            )

        # Deduplicate overlapping entities (keep highest confidence, then longest).
        entities = _deduplicate(entities)

        # Validate offsets.
        for e in entities:
            assert 0 <= e.char_start < e.char_end <= len(text), (
                f"invalid offset: {e.char_start}-{e.char_end} for text len {len(text)}"
            )
            assert text[e.char_start : e.char_end] == e.text, (
                f"offset mismatch: expected {e.text!r}, got {text[e.char_start:e.char_end]!r}"
            )

        return NLPResult(entities=entities)


def _all_skill_phrases() -> list[str]:
    from app.modules.nlp.gazetteer import SKILL_ENTRIES

    phrases: set[str] = set()
    for raw, _, _ in SKILL_ENTRIES:
        phrases.add(raw)
    return sorted(phrases)


def _deduplicate(entities: list[Entity]) -> list[Entity]:
    """Remove overlapping entities, keeping highest confidence then longest span."""
    if not entities:
        return entities
    # Sort by start, then by length descending.
    sorted_ents = sorted(entities, key=lambda e: (e.char_start, -(e.char_end - e.char_start)))
    result: list[Entity] = []
    for ent in sorted_ents:
        # Check overlap with already-kept entities.
        overlaps = False
        for kept in result:
            if ent.char_start < kept.char_end and ent.char_end > kept.char_start:
                # Overlap: keep the one with higher confidence, then longer span.
                ent_conf = ent.confidence or 0
                kept_conf = kept.confidence or 0
                ent_len = ent.char_end - ent.char_start
                kept_len = kept.char_end - kept.char_start
                if ent_conf > kept_conf or (ent_conf == kept_conf and ent_len > kept_len):
                    result.remove(kept)
                    result.append(ent)
                overlaps = True
                break
        if not overlaps:
            result.append(ent)
    return result