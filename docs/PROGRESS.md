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

## M1 Core MVP — code complete (5 Nov 2026), deployment pending

### Code
- **M1-1 Schema + RLS** — Alembic `0001`–`0005` (extensions/enums, core tables, documents/chunks/entities, scoring/outbox/rag/audit, RLS+roles+grants). `ENABLE` + `FORCE ROW LEVEL SECURITY` on every tenant table except the `org_memberships` bootstrap read and `idempotency_keys` (no `org_id`). `docs/schema.sql` snapshot committed.
- **M1-2 Upload → extraction → NLP → store** — MIME magic-byte allow-list, 5 MB / 60-page limits, sandboxed subprocess extraction (PDF, DOCX, TXT), SHA-256, warning flags, typed errors, list/detail endpoints. spaCy + gazetteer entity extraction persisted in the same transaction.
- **M1-4 Outbox** — bounded drain with `SKIP LOCKED`, idempotency check, 3-attempt DLQ, `POST /api/v1/outbox/drain`.
- **M1-5 Isolation** — 4 cross-tenant tests, including a direct-SQL zero-row proof under the `vetharbor_app` role.
- **M1-6 React UI** — document list/detail, `UploadDropzone`, `EvidenceRail`, tenant-scoped query keys, bounded status polling that stops on a terminal state, a11y tests for the new components.
- **Gemini adapter** — real `GeminiEmbeddings`/`GeminiLLM` behind the existing provider interfaces; `tools=[]` always, 768-d validated and normalised, model ids and key read from `Settings`. Fake providers remain the CI default.

### Gates (all green)
- ruff check + ruff format --check: pass (53 files)
- mypy --strict: pass (38 files)
- eslint + prettier --check: pass
- tsc -b: pass
- pytest: **72 passed**
- vitest: **28 passed**
- npm run build: pass

### Gemini verification (live free-tier key, 5 Nov 2026)
- `gemini-embedding-2` → 768-d unit vector; `gemini-embedding-001` → 768-d unit vector
- `gemini-2.5-flash` → 404 for new accounts; `gemini-3.8-flash` / `gemini-flash-latest` → 503
- `gemini-3.1-flash-lite` → answered, honoured `response_json_schema`

### Still to do for M1 to close
- **M1-7 deployment** — Neon + Render + Vercel + Auth0 (needs the owner's cloud consoles), then seed and flip `demo_state.is_readonly_mode`.
- **`scripts/seed.py` insert path** — still dry-run only, so a deployed demo would have no documents.
- Reconcile `docs/TASKS.md` with the completed M1 rows.

---

## What to do next

### M1-7 — Lite deployment
1. Neon project; run `alembic upgrade head` from a developer machine.
2. Render web service: `PROFILE=lite`, `ENVIRONMENT=prod`, `VETHARBOR_DATABASE_URL`, `GEMINI_API_KEY`.
3. Vercel project pointing at the Render URL via `VITE_API_URL`.
4. Auth0 SPA + API; issuer/audience onto Render.
5. Seed the synthetic corpus, set `demo_state.is_readonly_mode = true`.
6. Prove upload is refused server-side on the deployed URL; screenshot the 403.

### Not in M1
RAG, Spring orchestrator, Helm, Mongo, Quarto — [T1]-later or [T2]