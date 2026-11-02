"""Generate the synthetic CV corpus used by `make seed` and the M1 demo.

Deterministic: same seed -> identical output, so the ground truth is reproducible
and the corpus never leaks real candidate data (AGENTS.md §3.2, ADR-010).

Output layout:
  scripts/generated/
    corpus.jsonl          # one synthetic CV per line, with tenant + ground truth
    ground_truth.json     # role -> list of document ids ranked by match band

Run:  python scripts/generate_synthetic_corpus.py [--count 200] [--seed 42]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from faker import Faker

# Two seeded tenants mirror the rest of the system (docs/CONTEXT.md decision).
TENANTS = ("tenant-harbor", "tenant-northwind")

# Roles are first-class (docs/CONTEXT.md decision). Each carries the skills a
# strong match would show, so the generator can label match bands honestly.
ROLES = {
    "backend-engineer": {
        "title": "Backend Engineer",
        "skills": ["python", "fastapi", "postgres", "docker", "redis", "aws"],
    },
    "data-scientist": {
        "title": "Data Scientist",
        "skills": ["python", "pandas", "scikit-learn", "sql", "mlflow", "pytorch"],
    },
    "frontend-engineer": {
        "title": "Frontend Engineer",
        "skills": ["typescript", "react", "vite", "tailwind", "accessibility", "vitest"],
    },
}

BANDS = ("strong", "moderate", "weak", "insufficient")

# Synthetic-only names: Faker generates plausible but invented people. We never
# reuse real candidate names (AGENTS.md §3.2).
FIRST_NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Riley", "Casey", "Jamie"]
LAST_NAMES = ["Rivera", "Chen", "Okafor", "Patel", "Muller", "Sato", "Lopez", "Kim"]
CITIES = ["Amsterdam", "Berlin", "Lisbon", "Singapore", "Toronto", "Wellington", "Austin", "Oslo"]


@dataclass
class SyntheticDocument:
    id: str
    tenant_id: str
    role_id: str
    candidate_name: str
    location: str
    years_experience: int
    skills: list[str]
    match_band: str
    extracted_text: str
    ground_truth_relevant: bool


@dataclass
class GroundTruth:
    role_id: str
    relevant_document_ids: list[str] = field(default_factory=list)
    band_counts: dict[str, int] = field(default_factory=dict)


def _make_faker(seed: int) -> Faker:
    fake = Faker()
    fake.seed_instance(seed)
    return fake


def _candidate_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def _build_text(name: str, city: str, years: int, skills: list[str], rng: random.Random) -> str:
    skill_line = ", ".join(skills)
    extras = rng.sample(
        ["open source contributions", "mentoring", "conference talks", "patents filed"],
        k=rng.randint(0, 2),
    )
    extra_line = " " + "; ".join(extras) + "." if extras else "."
    return (
        f"{name}\n{city}\n\n"
        f"Summary: {years} years building software. Core skills: {skill_line}.\n"
        f"Experience: shipped production systems across multiple teams{extra_line}\n"
        f"Education: BSc Computer Science (synthetic institution).\n"
    )


def generate(count: int, seed: int) -> tuple[list[SyntheticDocument], dict[str, GroundTruth]]:
    rng = random.Random(seed)
    faker = _make_faker(seed)
    documents: list[SyntheticDocument] = []
    ground_truth: dict[str, GroundTruth] = {role: GroundTruth(role_id=role) for role in ROLES}

    for i in range(count):
        tenant_id = rng.choice(TENANTS)
        role_id = rng.choice(list(ROLES))
        role = ROLES[role_id]
        name = _candidate_name(rng)
        city = rng.choice(CITIES)
        years = rng.randint(1, 12)

        # Match band: strong candidates hold most of the role's skills.
        roll = rng.random()
        if roll < 0.25:
            band = "strong"
        elif roll < 0.55:
            band = "moderate"
        elif roll < 0.80:
            band = "weak"
        else:
            band = "insufficient"

        if band == "strong":
            skills = list(role["skills"])[: rng.randint(4, len(role["skills"]))]
        elif band == "moderate":
            skills = rng.sample(role["skills"], k=rng.randint(2, 4))
        elif band == "weak":
            skills = rng.sample(role["skills"], k=rng.randint(1, 2)) + rng.sample(
                ["excel", "word", "email"], k=1
            )
        else:
            skills = rng.sample(["excel", "word", "email", "typing"], k=3)

        relevant = band in ("strong", "moderate")
        doc_id = f"doc-{i:04d}-{hashlib.sha256(f'{tenant_id}{i}{seed}'.encode()).hexdigest()[:8]}"

        doc = SyntheticDocument(
            id=doc_id,
            tenant_id=tenant_id,
            role_id=role_id,
            candidate_name=name,
            location=city,
            years_experience=years,
            skills=skills,
            match_band=band,
            extracted_text=_build_text(name, city, years, skills, rng),
            ground_truth_relevant=relevant,
        )
        documents.append(doc)

        gt = ground_truth[role_id]
        if relevant:
            gt.relevant_document_ids.append(doc_id)
        gt.band_counts[band] = gt.band_counts.get(band, 0) + 1

    # Sort relevant ids so ground truth is deterministic and rankable.
    for gt in ground_truth.values():
        gt.relevant_document_ids.sort()

    return documents, ground_truth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "generated",
    )
    args = parser.parse_args()

    documents, ground_truth = generate(args.count, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    corpus_path = args.out / "corpus.jsonl"
    with corpus_path.open("w", encoding="utf-8") as fh:
        for doc in documents:
            fh.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")

    gt_path = args.out / "ground_truth.json"
    gt_path.write_text(
        json.dumps({k: asdict(v) for k, v in ground_truth.items()}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Wrote {len(documents)} synthetic CVs to {corpus_path}")
    print(f"Wrote ground truth for {len(ground_truth)} roles to {gt_path}")
    for role, gt in ground_truth.items():
        print(f"  {role}: {len(gt.relevant_document_ids)} relevant, bands={gt.band_counts}")


if __name__ == "__main__":
    main()
