# PROGRESS — Vetharbor

Living log of completed work and next steps. Updated at the end of every session.
For current state, locked decisions and the verification register, see `CONTEXT.md`.

---

## M0 Foundations — done (4 Nov 2026)

### Code
- FastAPI scaffold: app factory, `/healthz`, correlation middleware, typed error envelope (7 codes), provider protocols + fakes, RLS session helpers, Alembic wiring, module stubs, guard tests
- Web scaffold: Vite + React + TS + Tailwind v4 token layer, app shell, typed API client, tenant-scoped query keys, `WakingUp`/`ErrorNotice`
- Design tokens mapped from `DESIGN.md` §3 into `apps/web/src/styles/tokens.css`
- `infra/compose/dev.yaml` — Postgres 16 + pgvector on `:55432`
- `.env.example` files for both apps
- Root `Makefile` runs real gates (lint, typecheck, test)
- CI has `quality` job (install + `make test`, no secrets)
- Synthetic corpus generator (`scripts/generate_synthetic_corpus.py`) — 200 CVs, 2 tenants, ground truth
- `scripts/seed.py` — validates corpus (dry-run)
- `scripts/banned_words.txt` + guard test
- `security/threat-model.md` v0 (STRIDE + OWASP LLM Top 10)
- MIT LICENSE

### Gates (all green)
- ruff check + format: pass
- mypy --strict: pass (24 files)
- eslint: pass
- tsc -b: pass
- pytest: 37 passed
- vitest: 17 passed
- npm run build: pass

### Free-tier verification (closed)
- Neon: 1 GB storage, 100 CU-h, scale-to-zero on (5-min idle timeout)
- Auth0: 25,000 MAU, namespaced claims via Actions, no card required
- Gemini: gemini-embedding-2, 768-dim supported, 100 RPM / 1k RPD / 30k TPD free
- Name availability: GitHub/npm/PyPI/Docker Hub free; `.dev`/`.app` unregistered; `.com` taken

### Repo
- Pushed to https://github.com/ryan-gabriel/vetharbor.git
- Working tree clean

### Still open [verify] (non-blocking, [T2]/[T3])
- Atlas M0 vector-search index (row 2)
- Keycloak token exchange + DPoP (row 4)
- kind default CNI NetworkPolicy enforcement (row 5)
- Public resume dataset licence/size/PII (row 6)
- Oracle Always Free signup + card (row 8)
- Indonesian PDP Law + employer rules (row 10)

---

## In progress

- M1-1 — Schema + RLS: Alembic migrations 0001–0005 committed; schema/RLS/integration tests added; CI integration job added. Not yet: local CI-style integration run against real Postgres (Docker unavailable on this host right now), `docs/schema.sql` snapshot.

## What to do next (M1 Core MVP)

### Task 1 — Schema + RLS (blocks everything else)
- Alembic migration: `org_id uuid not null` on every tenant-scoped table
- `ENABLE` + `FORCE ROW LEVEL SECURITY` on every tenant table
- Standard policy from `DATA_MODEL.md` §4.2
- `scores` and `audit_log` append-only (revoke update/delete from `vetharbor_app`)
- Enums as Postgres enum types
- `vector(768)` embedding columns

### Task 2 — Upload → extraction → NLP → store
- MIME + magic bytes validation, size/page limits (5 MB, 60 pages)
- Sandboxed text extraction (subprocess with CPU/mem/wall limits)
- spaCy Matcher/EntityRuler + skills gazetteer
- Entity highlights with char offsets

### Task 3 — React upload/list/detail + F7 cross-tenant test
- UploadDropzone (disabled server-side in read-only demo)
- DocumentSheet + EvidenceRail two-pane spread
- Tenant-scoped TanStack Query keys
- `test_cross_tenant_read_returns_no_rows` proving isolation
- Deploy lite profile to Vercel+Render+Neon at end of M1

### Not in M1
RAG, Spring orchestrator, Helm, Mongo, Quarto — [T1]-later or [T2]