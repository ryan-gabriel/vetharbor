# AGENTS.md — Vetharbor

Instructions for AI agents working in this repository. Portable across agents; opencode-specific notes are in §14.

## 1. What this project is

Vetharbor is a document-screening platform (synthetic CVs, proposals, papers) with AI guardrails, event-driven ingestion and a pragmatic zero-trust layer. It is a **solo-built portfolio milestone that must cost $0 to run**.

**North star: a senior reviewer must be able to verify every claim you make.** A screenshot, a passing test or an ADR beats any paragraph. When quality and feature count compete, choose the artefact that survives an interview question.

## 2. Read order before any work

1. `docs/CONTEXT.md` — current state, locked decisions, next tasks. Always first.
2. `SPEC.md` — what is in scope and what "done" means.
3. The doc that owns the area you are touching (§6).
4. `docs/ARCHITECTURE.md` before moving code between modules.

Do not re-read all seven documents per session. `CONTEXT.md` exists so you do not have to.

## 3. Non-negotiable rules

These are hard constraints, not preferences. Violating one is a bug even if the code works.

1. **Cost stays $0.** No service requiring a credit card for `[T1]` or `[T2]` work. If a step seems to need one, stop and raise it.
2. **Synthetic data only.** Never wire real CVs, real candidate names, real contact details or real employer data into code, fixtures, seeds, snapshots, tests or docs (`ADR-010`). Real candidate data must never reach a third-party LLM.
3. **No automated adverse decision.** Never add a code path, UI string, enum value or flag that rejects, disqualifies, filters-out or auto-ranks candidates for exclusion. Every output is advisory with human review. `red`/danger styling marks system failure, never a person.
4. **No secrets in the repo.** The repository is public. Credentials live in environment stores and `.env` files that are git-ignored. Never paste a token into a file, a commit message, a log line, a test fixture or a report.
5. **CI never spends quota or talks to third-party AI.** Use `FakeLLM`/`FakeEmbeddings`. No Gemini, Auth0, Neon, Render or Atlas credentials in any workflow. A test that calls a paid or metered API is a broken test.
6. **Do not poll free tiers.** No `while True`, no sleep loops, no keep-alive pings, no cron that touches Neon — they defeat scale-to-zero and burn the 100 CU-hour budget. `TESTING.md` §5 has a guard test that enforces this.
7. **Respect the Render envelope.** One service, 512 MB RAM, 0.1 CPU, ephemeral disk, no torch, no sentence-transformers import, no file persistence, assume ~60 s cold start.
8. **Embeddings are 768 dimensions** in every profile and adapter. A 384- or 3072-d vector is a schema-breaking bug (`ADR-005`).
9. **Tenant and role are resolved from `org_memberships`, never from the client or a JWT claim** (`ADR-006`). Any new query path must pass through the RLS-aware persistence layer.
10. **Never weaken a threshold to make a check pass.** Lowering a gate is a documented change in `docs/TESTING.md`, in a pull request, with a reason.
11. **Do not commit, amend, push or open PRs unless explicitly asked.**

## 4. Truth and evidence discipline

- **If you cannot link it, do not claim it.** Every course-coverage row in `docs/course-evidence.md` points to a commit, test name, ADR id or screenshot path. A row with no link is removed, not worded more cleverly.
- **No invented numbers.** Never write a metric the CI does not measure. Report thresholds as goals, and results only as measured output.
- **Preserve `[verify]` flags.** Free-tier facts marked `[verify]` in `SPEC.md` §16 and elsewhere are unconfirmed. Do not restate them as settled; re-check them in the vendor console first, then remove the flag.
- **State what the demo does not prove.** The public demo is a lite profile without Keycloak, Spring, Kubernetes or Ollama. Say so in README and docs rather than implying they are deployed.
- **Bad news is a result.** The fairness audit and the injection false-positive rate are published whatever they show. Do not trim an inconvenient number.

## 5. Scope control

Tiers are `[T1]` must ship, `[T2]` should ship, `[T3]` document only.

- Work the current milestone in `docs/CONTEXT.md`. Do not build ahead of it.
- Do not start `[T2]` or `[T3]` work without explicit approval. `[T3]` is documentation, not code.
- If a task needs a new component, a new store or a new external service, that is a scope change: propose it and wait.
- **Cut order if behind:** `[T3]` → Quarto in CI (render locally) → Atlas experiment → Playwright (keep contract tests) → Helm (keep plain manifests). Test coverage is never traded for features.
- Never revive a cut item: no PHP/MySQL strangler story, no Qdrant, no second API service, no OCR of scanned images, no Indonesian NLP pipeline in v1.

## 6. Source-of-truth map

Each decision lives in exactly one file. Reference it; never fork it into a second copy that can drift.

| Decision area | Owner file |
| --- | --- |
| Scope, personas, flows, FR/NFR, thresholds, milestones | `SPEC.md` |
| Modules, boundaries, trust layers, profiles, ADRs, repo layout | `docs/ARCHITECTURE.md` |
| Tables, columns, types, enums, RLS, seeds | `docs/DATA_MODEL.md` |
| Colour, type, spacing, components, states, a11y | `docs/DESIGN.md` |
| Test tools, layers, CI jobs, gates | `docs/TESTING.md` |
| Current state, locked decisions, next tasks | `docs/CONTEXT.md` |
| Agent rules, commands, conventions | this file |

A change that crosses files updates the owner first and the references second. If you find the same rule stated in two places, consolidate and note it in `CONTEXT.md`.

## 7. Commands

Use these instead of inventing equivalents. All are root-`Makefile` targets.

| Task | Command |
| --- | --- |
| Full offline stack, zero keys | `make dev` |
| Seed two synthetic tenants + corpus | `make seed` |
| Reset local database | `make db-reset` |
| Deploy the public lite profile | `make demo-lite` |
| Local enterprise profile | `make demo-full` |
| kind + Calico cluster + proof tests | `make k8s-demo` `[T2]` |
| One bounded outbox drain | `make drain` |
| Everything below | `make test` = lint + typecheck + unit + integration + security + ml |
| Lint / format | `make lint` (ruff + eslint), `make format` |
| Type checks | `make typecheck` (mypy `--strict` + `tsc --noEmit`) |

Faster loops:

```bash
pytest -m unit                                   # python unit only
pytest -m integration -k "rls"                   # RLS integration subset
pytest -m security -k "injection"                # injection subset
pytest -m ml -k "drift"                          # drift gate
cd apps/web && npx vitest run -t "ScoreGauge"     # frontend subset
cd apps/web && npm run dev                        # Vite, port 5173
cd apps/api && uvicorn app.main:app --reload       # API, port 8000
```

Dependencies: `uv` (or `pip-tools`) for Python, `npm` for web, `docker` + `docker compose` for infra, JDK 21 and Maven/Gradle for the orchestrator `[T2]`, `.NET 8` SDK for `tests-e2e` `[T2]`. Python 3.12, Node 20+.

## 8. Code conventions — Python

- Layout: `apps/api/app/modules/<module>/{router,service,repository,schemas}.py`. A module imports another module's **public service**, never its models or repositories (`ARCHITECTURE.md` §3).
- FastAPI with dependency injection for auth, tenant context and DB session. No global singletons holding request state.
- Pydantic v2 schemas at every boundary. `response_model` set on every route. No `dict` passthrough.
- `SQLAlchemy` 2.0 typed style; Alembic migrations; `persistence` is the only place that opens a connection or sets `vetharbor.*` session variables.
- `ruff` for lint and format, `mypy --strict`. No untyped public functions.
- Exceptions: raise typed domain errors; the gateway maps them to the error union (`unauthenticated | waking_up | forbidden | not_found | rate_limited | server`). Never let a raw `ProgrammingError` reach a client.
- Logging: one JSON line per request with `correlation_id`, `tenant_id`, `user_sub`. **Never log document text, questions, answers, emails or names.**
- Subprocess isolation for text extraction with CPU, memory and wall-clock limits. Never render active content, never execute macros, never extract archives.
- Providers behind `EmbeddingProvider` / `LLMProvider`. Assert dimension at construction. No provider import outside `app/providers/`.
- The LLM client is constructed with **no tools and no function calling**, ever. If a library defaults to a tools field, send it empty explicitly.

## 9. Code conventions — TypeScript / React

- Vite + React + TypeScript `strict` with `noUncheckedIndexedAccess`. No `any` without a `// rationale:` comment.
- Feature folders (`features/auth`, `features/documents`, …) — not type folders.
- Server state in TanStack Query keyed with `['tenant', orgId, …]` so switching tenants cannot show the previous org's cache.
- All HTTP through `lib/api`; no `fetch` in components.
- Tailwind with **semantic tokens only** (`bg-accent`, `text-ink-muted`). Arbitrary values `bg-[#1C4ED8]` or `p-[13px]` fail review (`DESIGN.md` §10).
- shadcn/ui primitives copied into `components/ui`; composites in `components/`.
- Functional components and hooks only. One exported component per file, colocated `*.test.tsx`.
- Icons: `lucide-react`, stroke 1.5, always labelled in primary actions.
- Every interactive component ships the keyboard-path a11y test in the same PR.

## 10. Code conventions — SQL and migrations

- Alembic, one logical change per revision, `NNNN_description.py`.
- Every tenant-scoped table: `org_id uuid not null`, `ENABLE` **and** `FORCE ROW LEVEL SECURITY`, plus the standard policy from `DATA_MODEL.md` §4.2.
- Embedding columns are `vector(768)` and are covered by the CI dimension-invariant test.
- Enums are Postgres enum types; add values before code uses them; never rename or reuse a value.
- `scores` and `audit_log` stay append-only; revoke `update`/`delete` from `vetharbor_app`.
- Never run migrations against Neon from the Render service on boot; run them from CI or a developer machine with a scoped credential.

## 11. Git and pull requests

- Conventional Commits: `feat(scoring): add role-match band mapping`, `fix(outbox): bound drain pass to 20 events`, `docs(adr): add ADR-005 768-dimension standard`, `test(rls): prove cross-tenant read returns no rows`.
- Branch: `<type>/<milestone>-<slug>`, e.g. `feat/m1-upload-extraction`.
- Small commits, each building and passing the affected subset.
- PR body template: what changed → which FR/NFR it satisfies → tests added and how to run them → tier → any `SPEC.md`/`TESTING.md` threshold touched (call these out loudly).
- One report or doc job per artefact: update an existing file rather than creating a near-duplicate.
- Never commit `node_modules`, `.venv`, `dist`, `*.env`, `ml/registry/**/*.bin`, generated corpora or Playwright traces. Verify `.gitignore` before staging.

## 12. Definition of Done

A change is done when **all** of these hold:

1. Implementation matches the owning document, or that document was updated first.
2. Unit + integration tests pass; coverage gate still green.
3. Any security-relevant path has a named test; `pytest -m security` is green.
4. Any touched view passes the a11y suite.
5. `ruff`, `mypy --strict`, `eslint`, `tsc --noEmit` clean.
6. `docs/course-evidence.md` row updated with a link, if the change carries course credit.
7. `docs/CONTEXT.md` updated: state, decisions, next tasks.
8. No new dependency without a stated reason; no new service without an ADR.
9. Nothing secret committed; no `[T2]`/`[T3]` scope smuggled in.

## 13. Context management and session protocol

`docs/CONTEXT.md` is your memory across prompts. Treat it as the stateful part of the system.

- **Session start:** read `CONTEXT.md`. Note the milestone, the locked decisions and the next three tasks. Do not re-derive settled choices.
- **During:** if you make a decision that constrains future work (a library, a threshold, a schema shape), record it immediately in the decisions log with a one-line rationale. Do not let a decision live only in this chat.
- **Session end:** update the milestone status, the next-three-tasks list, and the running log with a dated entry of what changed and what is still broken. Note any `[verify]` item you confirmed and remove the flag.
- **Memory-loss rule:** if you find yourself re-asking something already in `CONTEXT.md`, or duplicating a decision, fix the file so it is discoverable. A lost decision gets re-litigated and costs hours.
- **Re-verification rule:** free-tier facts age. If you are about to design against a number marked `[verify]`, confirm it in the console before building on it.
- **Never** silently expand scope to make a test pass, and never mark a course row "done" without a link.

When blocked or when a rule above conflicts with the request, **stop and ask** rather than guessing. The three most common traps: needing a paid service, needing real data, and weakening a threshold.

## 14. opencode-specific notes

- Plan first for anything non-trivial: run the plan/proposal flow and get approval before editing seven-file-scale docs or moving module boundaries.
- Use `docs/` file authority (§6): open only the owning doc plus `CONTEXT.md` before an edit; batch reads in parallel.
- Prefer the `Makefile` targets in §7 over raw commands so behaviour matches CI.
- Run the narrowest test subset first (§7 faster loops); full `make test` before declaring done.
- Skills available for SEO/AI-visibility work are unrelated to this repository; do not invoke them for Vetharbor tasks.
- After a doc change, do the consistency pass in `docs/CONTEXT.md` §7 (the five locked decisions) so the seven files cannot drift.
- OpenCode is on **V2** (`opencode2` CLI, V2 config schema). Use the native `plugins` array in `.opencode/opencode.json` and the `@opencode/plugin` (V2) SDK — never the V1 `plugin` key or the `@opencode-ai/plugin` pin. V1 plugin implementations do not run in V2; ECC `ecc-universal@2.2.3` still ships the V1 implementation, so the plugin currently fails to load under V2 and needs an upstream ECC port before the toolchain loads cleanly. Project skills stay in `.agents/skills/`, which V2 still discovers as a supported compatibility source; no move is required while V2 keeps that source.
