# apps/api — FastAPI modular monolith [T1]

Async FastAPI service (ADR-001) implementing SPEC.md flows. Module map and
dependency direction: docs/ARCHITECTURE.md §3. Conventions: AGENTS.md §8.
Schema: docs/DATA_MODEL.md.

## Run (local)

```bash
uv sync                                  # installs Python 3.12 per .python-version
cp .env.example .env                     # local defaults only; no secrets
uv run uvicorn app.main:app --reload     # http://localhost:8000/healthz, /docs
uv run pytest                            # unit + security guards, fake providers only
uv run ruff check . && uv run mypy       # lint + strict types
```

Postgres comes up with `docker compose -f ../../infra/compose/dev.yaml up -d`.
The engine is lazy: no connection is opened at import time, so the unit and
guard suites need no database (TESTING.md §1). The first migration arrives in
M1 and will use the URL above.

## Status (M0 task 2)

- [x] app factory, correlation middleware, typed error envelope (all codes of ARCHITECTURE.md §11)
- [x] provider interfaces + `FakeLLM`/`FakeEmbeddings` (ADR-005 boundary assertions)
- [x] module stubs: auth, upload, nlp, scoring, rag, outbox, persistence
- [x] async SQLAlchemy + Alembic wiring (first real migration: M1)
- [x] guards: `test_guard_no_pollers.py`, `test_guard_no_secrets.py`
- [ ] real adapters (Gemini/fastembed/MPNet/Ollama): M4
- [ ] OIDC verification, `org_memberships` resolution: M3
