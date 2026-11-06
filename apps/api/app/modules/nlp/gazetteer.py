"""Skills gazetteer — normalised skill labels with taxonomy references.

Maps raw skill strings to canonical (normalised, taxonomy) pairs. The
gazetteer is versioned as a Python module so changes are diffable in PRs.
"""

from __future__ import annotations

# Canonical skill entries: (raw_lower, normalised, taxonomy)
SKILL_ENTRIES: list[tuple[str, str, str]] = [
    # Programming languages
    ("python", "python", "local"),
    ("typescript", "typescript", "local"),
    ("javascript", "javascript", "local"),
    ("java", "java", "local"),
    ("go", "go", "local"),
    ("rust", "rust", "local"),
    ("c#", "csharp", "local"),
    ("c++", "cpp", "local"),
    # Frameworks
    ("fastapi", "fastapi", "local"),
    ("react", "react", "local"),
    ("vue", "vue", "local"),
    ("angular", "angular", "local"),
    ("django", "django", "local"),
    ("flask", "flask", "local"),
    ("spring", "spring", "local"),
    ("spring boot", "spring_boot", "local"),
    ("node.js", "nodejs", "local"),
    ("nodejs", "nodejs", "local"),
    # Databases
    ("postgres", "postgres", "local"),
    ("postgresql", "postgres", "local"),
    ("mysql", "mysql", "local"),
    ("mongodb", "mongodb", "local"),
    ("redis", "redis", "local"),
    ("sqlite", "sqlite", "local"),
    # Cloud / infra
    ("aws", "aws", "local"),
    ("gcp", "gcp", "local"),
    ("azure", "azure", "local"),
    ("docker", "docker", "local"),
    ("kubernetes", "kubernetes", "local"),
    ("terraform", "terraform", "local"),
    ("ci/cd", "cicd", "local"),
    # ML / data
    ("pandas", "pandas", "local"),
    ("numpy", "numpy", "local"),
    ("scikit-learn", "sklearn", "local"),
    ("pytorch", "pytorch", "local"),
    ("tensorflow", "tensorflow", "local"),
    ("mlflow", "mlflow", "local"),
    ("spark", "spark", "local"),
    # Tools
    ("git", "git", "local"),
    ("linux", "linux", "local"),
    ("vite", "vite", "local"),
    ("tailwind", "tailwind", "local"),
    ("vitest", "vitest", "local"),
    ("accessibility", "accessibility", "local"),
    ("a11y", "accessibility", "local"),
]

GAZETTEER_VERSION = "1.0.0"

# Build lookup dict (lowercase -> (normalised, taxonomy)).
_LOOKUP: dict[str, tuple[str, str]] = {}
for raw, norm, tax in SKILL_ENTRIES:
    _LOOKUP[raw.lower()] = (norm, tax)


def lookup(skill: str) -> tuple[str, str] | None:
    """Return (normalised, taxonomy) for a raw skill string, or None."""
    return _LOOKUP.get(skill.lower().strip())


def all_skills() -> list[str]:
    """Return all canonical skill names."""
    return sorted({norm for _, norm, _ in SKILL_ENTRIES})
