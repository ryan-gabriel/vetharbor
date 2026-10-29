# Vetharbor — root Makefile

# Targets are defined in AGENTS.md §7. Placeholder targets that would run code
# which does not exist yet fail loudly; only the check targets pass empty,
# because the M0 done-criterion is "CI green on an empty pipeline" (SPEC.md §13).

SHELL := /bin/bash

.PHONY: help dev seed db-reset demo-lite demo-full k8s-demo drain test lint typecheck

help: ## list targets
	@grep -hE '^[a-z0-9-]+:.*?## ' Makefile | awk -F':.*?## ' '{printf "  %-12s %s\n", $$1, $$2}'

# ---- run profiles (SPEC.md §5) — implemented per milestone, not before ----

dev: ## zero-key offline stack: Postgres+pgvector, FastAPI, React, Keycloak, Ollama [M0-task2]
	@echo "ERROR: not implemented yet — M0 task 2 (infra/compose/dev.yaml). See docs/CONTEXT.md §4." >&2; exit 1

seed: ## seed two synthetic tenants + 200 generated CVs [M0-task3 / M1]
	@echo "ERROR: not implemented yet — M0 task 3 (scripts/generate_synthetic_corpus.py)." >&2; exit 1

db-reset: ## drop and recreate the local dev database [M1]
	@echo "ERROR: not implemented yet." >&2; exit 1

demo-lite: ## deploy the public profile: Vercel + Render + Neon + Auth0 + Gemini [M1]
	@echo "ERROR: not implemented yet — requires the SPEC.md §16 [verify] items cleared." >&2; exit 1

demo-full: ## local enterprise profile: Keycloak, Spring worker, Mongo [M2]
	@echo "ERROR: not implemented yet." >&2; exit 1

k8s-demo: ## kind + Calico + helm + NetworkPolicy proof tests [T2, M6]
	@echo "ERROR: not implemented yet — [T2]." >&2; exit 1

drain: ## one bounded outbox drain pass (ARCHITECTURE.md §6) [M2]
	@echo "ERROR: not implemented yet." >&2; exit 1

# ---- quality gates (TESTING.md §14) ----

lint: ## ruff + eslint (placeholders until sources exist)
	@echo "lint: no sources yet — empty pipeline passes (M0 criterion)."

typecheck: ## mypy --strict + tsc --noEmit (placeholders until sources exist)
	@echo "typecheck: no sources yet — empty pipeline passes (M0 criterion)."

test: lint typecheck ## make test = lint + typecheck + unit + integration + security + ml
	@echo "unit/integration/security/ml: no tests yet — empty pipeline passes (M0 criterion)."
	@echo "WARNING: the first real milestone must add tests before this target means anything (AGENTS.md §12)."
