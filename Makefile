# Vetharbor — root Makefile
#
# Targets are defined in AGENTS.md §7. `make test` is the real gate: it runs
# ruff, mypy --strict, ESLint, tsc and both test suites against real sources.
# Run profile targets that need application code still fail loudly until the
# milestone that implements them.

SHELL := /bin/bash

.PHONY: help dev seed db-reset demo-lite demo-full k8s-demo drain test lint format typecheck

help: ## list targets
	@grep -hE '^[a-z0-9-]+:.*?## ' Makefile | awk -F':.*?## ' '{printf "  %-12s %s\n", $$1, $$2}'

# ---- run profiles (SPEC.md §5) — implemented per milestone, not before ----

dev: ## zero-key offline infrastructure: Postgres 16 + pgvector on :55432
	docker compose -f infra/compose/dev.yaml up -d
	@echo "Postgres ready on localhost:55432. Start the API and web apps with the commands in apps/*/README.md."

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

lint: ## ruff + ruff format check + eslint + prettier check
	cd apps/api && uv run ruff check .
	cd apps/api && uv run ruff format --check .
	cd apps/web && npm run lint
	cd apps/web && npm run format

format: ## auto-format both apps
	cd apps/api && uv run ruff format .
	cd apps/web && npm run format:write

typecheck: ## mypy --strict + tsc --noEmit
	cd apps/api && uv run mypy
	cd apps/web && npm run typecheck

test: lint typecheck ## lint + typecheck + unit/security suites
	cd apps/api && uv run pytest
	cd apps/web && npm test
