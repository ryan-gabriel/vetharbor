# CONTEXT — Vetharbor

| | |
| --- | --- |
| **Purpose** | Tracks progress and prevents context-window memory loss. This file is the agent's state across prompts. |
| **Primary reader** | AI agent (every session), then the product owner. |
| **Status** | Living document. It is stale the moment work happens and it is not updated. |
| **Owner** | ryan_gabriel_s |
| **Last updated** | 4 Nov 2026 |

Tiers: `[T1]` must ship · `[T2]` should ship · `[T3]` documented only.

---

## 1. How to use this file

**Read at session start.** §2 current state, §4 next three tasks, §7 locked decisions. Then go straight to work. Do not re-read the other six documents unless the task touches them; they are the source of truth for their own domains (§8 map) and this file is the source of truth for *where the project is*.

**Write at three moments.**

1. You made a decision that constrains future work → §5 journal, dated, one line of rationale, and if it is structural, add it to §7.
2. You finished or started a milestone task → update §3 and §4.
3. You confirmed or disproved a `[verify]` fact → update §6, remove the flag in the owning document, and mention it in the commit or PR description.

**Never** let a decision exist only inside a chat transcript. If it is not here, it will be re-litigated, and that costs hours.

**Verification rule.** A free-tier number marked `[verify]` is an unconfirmed claim, not a fact. Confirm it in the vendor console before designing against it (§6).

## 2. Current state

| | |
| --- | --- |
| **Milestone** | M1 — Core MVP (weeks 2–3), **in progress**: schema, upload→NLP, outbox drain and the React document UI are done; lite deployment (M1-7) is the only task left and is blocked on cloud account setup |
| **Phase** | M1-6 complete; next is M1-7 (Vercel + Render + Neon + Auth0 + Gemini) |
| **Repository** | `vetharbor` — branch `main`, pushed to https://github.com/ryan-gabriel/vetharbor.git. Exact-match availability measured 29 Oct: GitHub user/org, npm, PyPI, Docker Hub free; `vetharbor.dev`/`.app` domains unregistered (RDAP 404); `.com` registered to someone else. Adjacent `VetHarbor`/`VETHarbor` veterinary projects exist on GitHub — different word, but note the collision when answering "why this name?". Trademark register: not checked. |
| **Code status** | **M1 code complete, undeployed.** API: Alembic migrations `0001`–`0005` (extensions/enums, core tables, documents/chunks/entities, scoring/outbox/rag/audit, RLS+roles+grants); upload → MIME magic-byte allow-list → sandboxed extraction (PDF/DOCX/TXT) → spaCy entity extraction → persistence in one transaction; bounded outbox drain with `SKIP LOCKED`, idempotency keys and a 3-attempt DLQ; tenant resolved from `org_memberships` with RLS forced on every tenant table. Providers: `fake` (CI default) and a real `GeminiEmbeddings`/`GeminiLLM` adapter behind the same interfaces, selectable from `.env` and failing fast without a key. Web: Vite + React + TS + Tailwind v4 tokens, app shell, typed API client, tenant-scoped query keys, `WakingUp`/`ErrorNotice`, `UploadDropzone`, document list/detail pages, `EvidenceRail`, bounded status polling that stops on a terminal state. Gates: `ruff` check + **format**, `mypy --strict`, `eslint`, `prettier --check`, `tsc -b`, build all clean; **72 API tests**, **28 web tests**. `make dev` brings up Postgres 16 + pgvector on `:55432`. `docs/schema.sql` snapshot committed. Synthetic corpus generator emits 200 CVs across 2 tenants. Threat model v0 in `security/threat-model.md` (root `SECURITY.md` not yet written). |
| **Agent toolchain** | ECC scoped to this project: `ecc-universal` npm plugin wired via the V2-native `plugins` array in `.opencode/opencode.json` (migrated off the V1 `plugin` key); local OpenCode plugin SDK context on `@opencode/plugin` (V2, 2.2.2); 45 skills in `.agents/skills/` (37 from `affaan-m/ecc`, 8 ecosystem: shadcn, vercel-react-best-practices, tailwind-design-system, webapp-testing, pgvector-semantic-search, helm-chart-scaffolding, quarto-authoring, github-actions-templates), recorded in `skills-lock.json`. No name collisions with global skills. No ECC home install; no `.cursor/.claude` etc. directories. Custom `spacy-gazetteer` and `injection-corpus` skills deferred to M1/M4. |
| **Docs status** | The seven governing documents exist and are internally consistent as of 5 Nov 2026: `SPEC.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DESIGN.md`, `docs/TESTING.md`, this file. The audited predecessor lives at `docs/PROJECT_PLAN_AUDIT.md` (moved from root 29 Oct; references fixed here). |
| **Not yet created** | `docs/course-evidence.md`, `docs/runbook.md`, `security/injection-corpus/`, `services/` `[T2]` |
| **Deployed status** | Nothing deployed. No Vercel project, no Render service, no Neon database, no Auth0 tenant. `make demo-lite` still fails loudly by design. |
| **Blockers** | None for M0. M1 blockers: Neon storage confirmed at 1 GB (sufficient). |
| **Biggest open risk** | Total scope. 19 topics across four languages at ~10 h/week. Mitigation is the tiering plus the cut order in `SPEC.md` §13; the mitigation only works if `[T2]` is genuinely deferred and not smuggled into `[T1]` "to save time". |

## 3. Milestone tracker

| Milestone | Weeks | Status | Done criteria (from `SPEC.md` §13) | Evidence links |
| --- | --- | --- | --- | --- |
| **M0 Foundations** | 1 | `done` | Public repo; CI green on empty pipeline; compose with Postgres+pgvector; generator emits 200 synthetic CVs; threat model v0; ADR-001 and ADR-002 recorded; all §6 items re-verified | this file; commits `1e48c4a`…`5352268`; CI run on `main` |
| **M1 Core MVP** | 2–3 | `in_progress` | Schema with `tenant_id` + RLS from day one; upload → safe extraction → spaCy → store; React upload/list/detail; lite deployed; entities visible on a public URL; F7 cross-tenant test proves isolation | schema/RLS: `migrations/0001`–`0005` + `tests/test_schema_rls.py` (7); pipeline: `tests/test_upload.py` (7), `tests/test_nlp.py` (7); isolation: `tests/test_cross_tenant.py` (4); outbox: `tests/test_outbox.py`; UI: `apps/web/src/features/documents/`, 28 web tests. **Missing: the deployed URL (M1-7).** |
| **M2 Outbox, idempotency, resilience** | 4–5 | `not_started` | Outbox, `SKIP LOCKED` consumers, DLQ, event versions; Spring orchestrator + Resilience4j calling NLP; correlation IDs; breaker opens on killed NLP; poison → DLQ; replay no-op | — |
| **M3 Identity and zero-trust** | 6–7 | `not_started` | Auth0 public + Keycloak local; RBAC via memberships; token exchange on the gateway→worker hop; NetworkPolicy on kind+Calico; auth-negative tests; denied pod cannot reach Postgres | — |
| **M4 RAG and guardrails** | 8–9 | `not_started` | pgvector index; provider interfaces; injection filter; canary; PII output filter; eval harness; cross-document Q&A; CI reports block rate and fails below 95 % | — |
| **M5 ML and statistics** | 10–11 | `not_started` | Train/evaluate; model card; shadow mode; PSI gate; fairness audit; Quarto report; CI fails on the drift fixture; report published | — |
| **M6 Quality gate** | 12–13 | `not_started` | C# contract tests (auth negatives) + one Playwright happy path; Helm chart; `make k8s-demo`; badge green; chart installs clean | — |
| **M7 Ship** | 14 | `not_started` | README with diagram; 3-minute video; `docs/course-evidence.md`; runbook; known-limitations page | — |

Status vocabulary: `not_started` · `in_progress` · `blocked` (with a named blocker here) · `done` (with a link) · `cut` (with the reason and the date).

## 4. Next three tasks

*Done since last update: M1-1 schema+RLS, M1-2/3 upload→extraction→NLP, M1-4 bounded outbox drain, M1-5 cross-tenant isolation, M1-6 React document UI (UploadDropzone, EvidenceRail, polling, a11y tests). Real Gemini adapter added behind the provider interfaces and verified against a live free-tier key (768-d embeddings, JSON-mode completion). All local gates green: 72 API + 28 web tests.*

1. **M1-7 — lite deployment (blocked on cloud consoles only the owner can open).** Neon project → `alembic upgrade head` from a developer machine → Render web service (`PROFILE=lite`, `ENVIRONMENT=prod`, `VETHARBOR_DATABASE_URL`, `GEMINI_API_KEY`) → Vercel project (`VITE_API_URL`) → Auth0 SPA + API → seed synthetic corpus → set `demo_state.is_readonly_mode = true` → verify upload is refused server-side on the deployed URL. Exit evidence: the public URL plus a screenshot of the 403.
2. **Seed path.** `scripts/seed.py` is still dry-run only, so the deployed demo has no documents. Implement the real insert path (two tenants, 200 synthetic CVs, entities) and record it in `docs/PROGRESS.md` / `docs/runbook.md`.
3. **Docs sync.** `docs/PROGRESS.md` and `docs/TASKS.md` still describe M1-4/M1-6 as open; reconcile them with this file so the next session does not re-derive finished work.

Deliberately *not* in the next three: RAG, the Spring orchestrator, Helm, Mongo, Quarto. They are `[T1]`-later or `[T2]`.

## 5. Decision journal

Newest first. Structural decisions also appear in §7.

| Date | Decision | Rationale | Consequence |
| --- | --- | --- | --- |
| 2026-10-30 | OpenCode **V2 compatibility**: migrated the tracked `.opencode/opencode.json` from the V1 `plugin` key onto the V2-native `plugins` array; moved the local plugin SDK context from `@opencode-ai/plugin@1.18.35` (V1) to `@opencode/plugin@2.2.2` (V2). Verified against the installed V2 binary (`opencode2` v0.0.0-beta-17823): plugin still fails to load — `ecc-universal@2.2.3` ships a V1 plugin implementation whose `@opencode-ai/plugin` import is unresolvable under V2, i.e. an upstream ECC port is pending before the toolchain can load cleanly on V2. Skills remain in `.agents/skills/`, which V2 still discovers as a supported compatibility source. | Decision owner: OpenCode V2 native shapes (`plugins` array, `@opencode/plugin` SDK); ECC owns the plugin implementation port. Consequence: do not reintroduce the V1 `plugin` key or V1 SDK pin while on V2; if the plugin misbehaves on V2, file the upstream compatibility bug before touching local config. spaCy + OWASP-LLM gap-filler skills (`spacy-gazetteer`, `injection-corpus`) authored as custom project skills at M1/M4 |
| 2026-10-29 | Agent toolchain is **project-scoped ECC**: `ecc-universal` npm plugin (hooks: secret-scan, session-context — maps to AGENTS §3.4/§13) + 45 skills installed with `npx skills add … -a opencode -y --copy` into `.agents/skills/`; skill dirs and `skills-lock.json` committed so a clone carries the toolchain | OpenCode discovers project skills only inside a git worktree and from `.agents/`/`.opencode/` paths; the repo sits on a Windows mount where symlinks fail, hence `--copy`; a home-target ECC install would violate "project only" and stack installs | ECC-on-OpenCode is **beta** (no Claude Code parity): if the plugin misbehaves, remove the `plugin` line from `.opencode/opencode.json` — skills keep working. spaCy + OWASP-LLM gap-filler skills (`spacy-gazetteer`, `injection-corpus`) authored as custom project skills at M1/M4 |
| 2026-10-29 | Audit document relocated to `docs/PROJECT_PLAN_AUDIT.md`; all references updated; root now holds only `AGENTS.md`, `SPEC.md`, `README.md` + tooling | History belongs in `docs/`; `Project Plan.md`'s space breaks links; `SPEC.md`/`AGENTS.md` earn root placement, archaeology does not | Audit is a read-only archive — cite it, never edit it (§8) |
| 2026-10-29 | Documentation set approved at seven files: `AGENTS.md`, `SPEC.md`, `docs/{ARCHITECTURE,DESIGN,DATA_MODEL,TESTING,CONTEXT}.md`; `docs/PROJECT_PLAN_AUDIT.md` retained as the audited predecessor (moved from root 29 Oct) | A grilling session settled the open contradictions first, so the docs do not encode the plan's flaws | Docs own their domains; `AGENTS.md` §6 is the authority map |
| 2026-10-29 | Embeddings standardised at **768 dimensions** in all profiles; all-mpnet-base-v2 replaces all-MiniLM-L6-v2 for the local profiles | pgvector columns are fixed-dimension; mixing 768 (Gemini) with 384 (MiniLM) silently breaks the "same schema across profiles" claim | Re-embedding is a migration; `ADR-005`; CI dimension test |
| 2026-10-29 | Tenancy resolved from `org_memberships`; token carries `sub` only | A `tenant_id` claim would pin a user to one org and force re-auth on every invite | One cached membership query per request; `ADR-006` |
| 2026-10-29 | Public demo is **seeded and read-only**; upload proven by `make dev` and a recording | "Read-only demo" and "upload is the centrepiece" cannot both be true; the compromise also keeps visitor text away from Gemini | `demo_state.is_readonly_mode` enforced server-side; `ADR-009`, `ADR-010` |
| 2026-10-29 | `make dev` is a zero-key, fully offline stack (Postgres+pgvector, FastAPI, React, Keycloak, Ollama, fastembed ONNX) | A reviewer cloning a public repo could otherwise run nothing at all | The offline profile is a first-class deliverable and the E2E target |
| 2026-10-29 | Lite auth = **Auth0 free tier**; Keycloak stays local/dev | Keycloak needs ~1 GB RAM and cannot live on Render free | Standard claims + JWKS only, so swapping is configuration |
| 2026-10-29 | Lite embeddings + LLM = **Gemini API behind interfaces**; never in CI | 512 MB on Render excludes torch; synthetic-only bounds the privacy exposure | Fake providers in CI; `ADR-002` |
| 2026-10-29 | Postgres-native queue by default, on-demand bounded drain, **no poller** | A poller defeats Neon scale-to-zero; QStash push cannot reach a laptop | `ADR-003`; `test_no_poller_in_app` |
| 2026-10-29 | `job_roles` is a first-class table, not pasted JD text | Scores must be comparable over time and drift needs a stable denominator | Role CRUD is an admin capability |
| 2026-10-29 | Two seeded tenants in every environment | Proves cross-tenant reads fail, which is the flagship demo moment | F7 test plus GWT flow F6 |
| 2026-10-29 | Quality gates: backend 80 % / frontend 70 % coverage, injection block ≥ 95 % with FP ≤ 5 %, canary leakage 0, PII recall ≥ 99 %, PSI < 0.25, zero critical audit issues | Numeric gates are the only way a claim survives an interview probe | Encoded in `TESTING.md` §14 and as `CHECK` constraints in `security_eval_runs` |
| 2026-10-29 | Frontend: React + Vite + TS + Tailwind + shadcn/ui; aesthetic **editorial security, light with one accent**, self-hosted `@fontsource` fonts | Document-first product; a dashboard look would fight the evidence story | Raw hex in components fails review |
| 2026-10-29 | Tier 2 kept at full documentation depth, deferred in build order | Course matrix needs all 19 rows honest; equal doc detail without equal schedule pressure | `[T2]`/`[T3]` tags on every requirement |
| 2026-10-29 | ADRs live as a register inside `ARCHITECTURE.md` §15 rather than one file each | At this size an ADR that must be opened is an ADR that will not be read | Revisit if the register exceeds ~15 entries |
| 2026-10-28 | Scope, tiering, free-tier corrections, synthetic-data-only and advisory-scoring positions inherited from the audited `docs/PROJECT_PLAN_AUDIT.md` | Those findings were correct and are now encoded as rules in `AGENTS.md` §3 | — |
| 2026-11-04 | M0 Foundations complete. Free-tier verified: Neon (1 GB/100 CU-h/scale-to-zero), Auth0 (25k MAU + namespaced claims via Actions, no card), Gemini (gemini-embedding-2, 768-dim, 100 RPM/1k RPD/30k TPD). Repo pushed to github.com/ryan-gabriel/vetharbor. Generator emits 200 CVs; threat model v0; CI green (37 API + 17 web tests). M0 → done. | M1 (schema + RLS) unblocked. |
| 2026-11-05 | M1-1 started: Alembic migrations 0001-0005 (extensions/enums, core tables, documents/chunks/entities, scoring/outbox/rag/audit, RLS+roles+grants) plus integration tests for RLS enforcement, 768-d vectors and append-only roles, and a GitHub Actions integration job against pgvector/pgvector:pg16. ruff/mypy/pytest green; integration tests skip without Postgres locally and run in CI. | Finish M1-1 (schema snapshot + local/ci integration run), then M1-2. |
| 2026-11-05 | M1-2 upload service: MIME allow-list + magic bytes, 5 MB/60 page limits, sandboxed subprocess extraction (PDF via pypdf, DOCX via zipfile+XML, TXT), SHA-256, warning flags, read-only demo rejection, typed errors, FastAPI endpoints with list/detail. 7 upload tests + 7 integration tests + 39 unit/security tests = 53 total, all green. ruff + mypy clean. | Next: spaCy NLP entity extraction (M1-3), React upload/list/detail UI (M1-6), cross-tenant isolation tests (M1-5). |
| 2026-11-05 | M1-3 NLP entity extraction: spaCy en_core_web_sm (ORG, DATE NER), PhraseMatcher for skills gazetteer (40+ skills), regex for roles/education/years/dates/contact (PII), deduplication, offset validation. 7 NLP tests. Entities persisted in same transaction as document. 60 total tests, all green. ruff + mypy clean (35 files). | Next: M1-5 (cross-tenant isolation tests), M1-6 (React upload/list/detail UI), M1-7 (lite deployment), docs/schema.sql snapshot. |
| 2026-11-05 | M1-5 cross-tenant isolation: 4 integration tests — API returns 404 for cross-tenant document, list excludes other tenant's docs, direct SQL returns zero rows under RLS, unowned org returns empty list. All pass against real Postgres. 64 total tests. | Next: M1-6 (React upload/list/detail UI), M1-7 (lite deployment), docs/schema.sql snapshot. |
| 2026-11-04 | free-tier corrections | Those findings were mostly correct with a little update (embedding model id, free storage neon)| - |
| 2026-11-05 | **Gemini adapter is real, not a stub.** `app/providers/gemini.py` implements `EmbeddingProvider` and `LLMProvider` behind the same interfaces as the fakes: `embed()` requests `output_dimensionality=768`, validates with `ensure_dimensions`, and normalises to unit length (Gemini does not normalise reduced-dimension output); `complete()` sends `tools=[]` explicitly, so no library default can re-introduce function calling. Model ids moved into `Settings` (`gemini_embedding_model`, `gemini_llm_model`) because Google retires them. `GEMINI_API_KEY` is a `SecretStr` read from either `GEMINI_API_KEY` or `VETHARBOR_GEMINI_API_KEY`, with no default. | Verified 2026-11-05 with a live free-tier key: `gemini-embedding-2` and `gemini-embedding-001` both returned 768-d unit vectors; `gemini-2.5-flash` is **404 for new accounts**; `gemini-3.8-flash` and `gemini-flash-latest` returned **503** on every attempt; `gemini-3.1-flash-lite` answered and honoured `response_json_schema`. Defaults set to `gemini-embedding-2` / `gemini-3.1-flash-lite`. The `SPEC.md` §16.7 / `ADR-005` "gemini-embedding-2 768-d" claim now has a measured anchor instead of a console reading. CI still pins both providers to `fake`; the adapter is never constructed in a test without a stub SDK. |
| 2026-11-05 | **CI was red on `main` before this session** and nobody had run the format gate locally: `make lint` runs `ruff format --check .` and `prettier --check .`, and 21 Python files plus 9 web files failed. Fixed by running both formatters. Also made the web test suite hermetic (`test.env.VITE_API_URL = ""` in `vite.config.ts`) because a developer's git-ignored `apps/web/.env.local` was changing the assertion in `api.test.ts` — the test passed on CI and failed on a dev box, which is the wrong way round. | Both gates are now clean locally and the format check will actually hold in CI. Rule for the next session: run `ruff format --check` and `prettier --check` before claiming gates are green; `make test` alone is not the whole story on Windows where `make` is unavailable. |
| 2026-11-05 | `test_guard_no_secrets.py` now scans only **git-tracked** files instead of walking the working tree. A real `GEMINI_API_KEY` in a git-ignored `apps/api/.env` is not a repo leak, but the old guard failed on it, which trains people to ignore the guard. Falls back to the directory walk when `git` is unavailable. | The guard keeps its purpose (nothing reachable in the public repo carries a credential shape) while allowing the documented local `.env` workflow in AGENTS.md §3.4. |
## 6. Verification register (`[verify]`)

| # | Item | Where flagged | Owner | Status |
| --- | --- | --- | --- | --- |
| 1 | Neon free storage 1 GB, 100 CU-h, scale-to-zero on (5-min idle timeout) | `SPEC.md` §16.1, `ARCHITECTURE.md` §12 | product | `closed` — blocks M1 sizing |
| 2 | Atlas M0 vector-search index availability and count | `SPEC.md` §16.2, `DATA_MODEL.md` §8 | product | `open` — `[T2/T3]` only, non-blocking |
| 3 | Auth0 free tier: 25,000 MAU, namespaced access-token claims via Actions, Free plan/no card required | `SPEC.md` §16.3, `ADR-009` | product | `closed` — **blocks M3 design** |
| 4 | Keycloak version: token exchange (RFC 8693) and DPoP support | `SPEC.md` §16.4, `ARCHITECTURE.md` §7 | product | `open` — `[T2/T3]` |
| 5 | kind default CNI `NetworkPolicy` enforcement (install Calico regardless) | `SPEC.md` §16.5, `TESTING.md` §11 | product | `open` — `[T2]` |
| 6 | Public resume dataset licence, size, PII ("96k" figure unverified) | `SPEC.md` §16.6, §10 | product | `open` — fallback is generator-only, which is acceptable |
| 7 | Gemini model gemini-embedding-2, 100 RPM / 1k RPD / 30k TPD Free-tier quota, 768 dimensions supported | `SPEC.md` §16.7, `ADR-005` | product | `closed` — re-verified **2026-11-05** against a live key: `gemini-embedding-2` and `gemini-embedding-001` both return 768-d vectors. Older LLM ids are being retired (`gemini-2.5-flash` → 404 for new accounts, `gemini-3.8-flash` → 503); the LLM id is now a setting, default `gemini-3.1-flash-lite`. |
| 8 | Oracle Always Free signup and card acceptance | `SPEC.md` §16.8 | product | `open` — `[T3]`, never a dependency |
| 9 | Name availability: GitHub, `vetharbor.dev`/`.app`, npm, PyPI, Docker Hub, trademark | `SPEC.md` §16.9, §4 | product | `closed` — GitHub/npm/PyPI/Docker Hub free; `.dev`/`.app` unregistered; `.com` taken; adjacent VetHarbor repos noted |
| 10 | Indonesian PDP Law plus employer/university rules on candidate data | `SPEC.md` §16.10 | product | `open` — default answer is "do not use real data" |

When one closes, remove the `[verify]` marker in the owning file and add a dated line to §5.

## 7. The five locked decisions — consistency pass

These five survived the grilling and are cross-document commitments. After **any** document edit, re-check them; a drift here is the difference between a coherent design and an embarrassing contradiction in review.

| # | Locked decision | Stated in | Check by grepping for | Forbidden variants |
| --- | --- | --- | --- | --- |
| **L1** | Embeddings are **768 dimensions** in every profile (`ADR-005`) | `SPEC.md` §5, `ARCHITECTURE.md` §2/§5/§15, `DATA_MODEL.md` §1.3/§3.7/§5, `AGENTS.md` §3.8 | `384`, `MiniLM`, `3072`, `vector(` | a 384-d MiniLM model; a profile-specific dimension; a configurable dimension at runtime |
| **L2** | Tenant + role resolved from `org_memberships`, never from a JWT claim or client input (`ADR-006`) | `SPEC.md` §4, `ARCHITECTURE.md` §7, `DATA_MODEL.md` §2/§3.3/§4.1, `AGENTS.md` §3.9 | `tenant_id.*claim`, `token.*role`, request-body `org_id` | trusting a client-supplied tenant; putting `org_id` in the token; deriving role from `email` |
| **L3** | Public demo is **seeded, read-only**; uploads are proven locally (`ADR-009`, `ADR-010`) | `SPEC.md` §5/§6/F1, `ARCHITECTURE.md` §2, `DATA_MODEL.md` §3.18, `TESTING.md` §6 | `demo_reader`, `is_readonly_mode`, upload-enabled-on-public | an enabled public upload path; visitor text reaching Gemini; hiding the dropzone instead of refusing server-side |
| **L4** | `make dev` is a **zero-key offline** stack a reviewer can actually run | `SPEC.md` §5, `ARCHITECTURE.md` §2, `TESTING.md` §10/§12, `AGENTS.md` §7 | `make dev`, required cloud secret in a test | a quickstart needing a card, an API key, or a cloud project |
| **L5** | CI uses **fake providers only**, holds no third-party credentials, and runs **no pollers** | `SPEC.md` FR-502, `ARCHITECTURE.md` §5/§6, `TESTING.md` §1/§5.13/§12 | `GEMINI_API_KEY` in a workflow, `while True`, `APScheduler` | a test that spends quota; a background poller against Neon; a keep-alive ping |

Consistency check: `grep -rn -iE "384|MiniLM|APScheduler|while True" AGENTS.md SPEC.md docs/` should return only the places where these are explicitly *forbidden*.

## 8. Document map

| File | Owns | Do not restate its content in |
| --- | --- | --- |
| `AGENTS.md` (root) | Agent rules, commands, conventions, DoD | anywhere |
| `SPEC.md` (root) | Scope, personas, flows, FR/NFR, thresholds, milestones | `ARCHITECTURE.md`, `TESTING.md` |
| `docs/ARCHITECTURE.md` | Modules, boundaries, profiles, trust layers, ADR register, repo layout, free-tier rules | `SPEC.md` |
| `docs/DATA_MODEL.md` | Tables, columns, enums, RLS, seeds, vector rules | `ARCHITECTURE.md` |
| `docs/DESIGN.md` | Tokens, typography, components, states, copy, a11y | code comments, `ARCHITECTURE.md` |
| `docs/TESTING.md` | Tools, layers, gates, CI jobs | `SPEC.md` thresholds (reference them) |
| `docs/CONTEXT.md` (this file) | State, decisions, next tasks, verification register | — |
| `docs/PROJECT_PLAN_AUDIT.md` | Historical audit of the original proposal; superseded by the seven documents | read-only archive — cite it, never edit it |
| *to create* | `docs/course-evidence.md` (19 rows, each linked), `docs/runbook.md`, `security/threat-model.md` | — |

## 9. Known limitations to repeat honestly

1. The public demo is the lite profile: no Keycloak, Spring, Kubernetes or Ollama in the deployed URL.
2. Visitors cannot upload; `make dev` and the recording carry that proof.
3. Gemini free-tier quotas drift and Google may use free-tier prompts, hence synthetic text only and an interface boundary.
4. "Fit score" would be an over-claim. This is a role-match ranking against manufactured ground truth.
5. Cold starts make the first request slow (~60 s); the UI says so instead of pinging.
6. English-only NLP. Indonesian CV processing is future work; the multilingual embedding model is not a substitute for a spaCy pipeline.
7. No OCR of scanned images and no virus-scanning service — stated in the runbook, not discovered by a reviewer.
8. Coverage of the 19 topics is tiered; `[T2]` rows are evidenced by tests and recordings, not by a public deployment.

## 10. Session handover template

Copy into §2/§4 at the end of a working session.

```markdown
### Session YYYY-MM-DD — <milestone> <slug>
- Done:                     (with commit/test links)
- In progress / left broken:
- Next:                     (exactly three tasks, or the one blocker)
- Decisions made:           (added to §5; structural ones also to §7)
- [verify] items closed:    (and where the flag was removed)
- Scope risk seen:          (anything that tried to creep in, and the answer given)
- Do NOT re-derive:         (settled choices the next session must accept)
```

## 11. Running log

| Date | Entry |
| --- | --- |
| 2026-10-29 | **M0 init session.** `git init` (main, uncommitted, no remote). Added `.gitignore`, root `README.md`, `Makefile` (stubs fail loudly; check targets pass empty per the M0 criterion), `.github/workflows/ci.yml` (docs-exist + §7 consistency grep + `make test`), directory tree with scoped READMEs. Installed the ECC toolchain: `ecc-universal` plugin in `.opencode/opencode.json` + 45 project-local skills in `.agents/skills/` (`skills-lock.json` recorded; zero name collisions with globals). Measured name availability: GitHub identity, npm, PyPI, Docker Hub, `.dev`/`.app` all free; `.com` taken; adjacent `VetHarbor` veterinary repos exist. Audit doc moved to `docs/PROJECT_PLAN_AUDIT.md`, references fixed. Still uncreated: app scaffolding, compose, generator, threat model, LICENSE, remote + first commit. |
| 2026-10-29 | Wrote the seven governing documents from the audited `docs/PROJECT_PLAN_AUDIT.md`, after a grilling session resolved five open contradictions: 768-dimension embeddings, memberships-based tenancy, seeded read-only public demo, zero-key `make dev`, and fake providers in CI. Added the ADR register (`ADR-001`…`ADR-010`), the quality gates, the guardrail thresholds and the five-decision consistency checklist (§7). Ran the §7 consistency pass: all cross-references and ADR ids resolve, the only `384`/`MiniLM`/`while True` mentions are explicit prohibitions, two defects fixed (`taxonomy` column typo in `DATA_MODEL.md` §3.8/§8, `AGENTS.md` intro pointed at §13 instead of §14). No code exists yet. M0 tasks and the §6 `[verify]` register are the critical path. |
| 2026-10-28 | `Project Plan.md` (now `docs/PROJECT_PLAN_AUDIT.md`) audited: 19-topic scope re-tiered across 14 weeks, free-tier facts corrected (Render 512 MB/0.1 CPU, Neon 100 CU-h, Qdrant suspended-then-deleted), queue topology fixed, Qdrant dropped, hiring-AI risk framed, name set to Vetharbor with a checklist. |
| 2026-11-04 | **M0 Foundations complete.** Free-tier verified (Neon 1 GB/100 CU-h, Auth0 25k MAU + Actions claims, Gemini gemini-embedding-2 768-dim). Repo pushed to github.com/ryan-gabriel/vetharbor. M0 milestone → done. M1 (schema + RLS) is next. |
| 2026-11-05 | **M1 code complete (`in_progress` pending deployment).** M1-1 migrations `0001`–`0005` + schema/RLS integration tests; M1-2/3 upload → magic-byte MIME allow-list → sandboxed extraction → spaCy entities, one transaction; M1-4 bounded outbox drain with `SKIP LOCKED`, idempotency and a 3-attempt DLQ; M1-5 four cross-tenant tests including a direct-SQL zero-row proof under `vetharbor_app`; M1-6 React list/detail, `UploadDropzone`, `EvidenceRail`, bounded polling that stops on a terminal status, and a11y tests. Gates: `ruff` check + format, `mypy --strict`, `eslint`, `prettier --check`, `tsc -b`, build, **72 API + 28 web tests**. Real Gemini adapter added and verified live. Remaining M1 work: M1-7 deployment (needs the cloud consoles) and the `seed.py` insert path. |
| 2026-11-05 | Repo hygiene: `apps/api/.env.example` now documents the Gemini switch (commented key + model overrides) and `apps/web/.env.local` / `apps/api/.env` exist locally but stay git-ignored. `.gitignore` already covered both via `*.env` / `*.env.*` with `!.env.example` — verified with `git check-ignore`, no change needed. |
