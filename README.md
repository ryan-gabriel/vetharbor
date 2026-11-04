# Vetharbor

Document screening with AI guardrails, event-driven ingestion, and a pragmatic zero-trust layer —
built to run at $0. *Vet* (screen carefully) + *harbor* (untrusted documents are inspected before they come ashore).

**Status: M0 foundations complete.** The API scaffold (health route, typed errors, provider
fakes, RLS helpers, guard tests) and the web shell are in place and covered by 54 tests;
the database schema, upload pipeline and public demo arrive in M1. Nothing is deployed yet.

`make test` runs the real gates: `ruff`, `mypy --strict`, ESLint, `tsc` and both test suites. The
offline Postgres+pgvector stack comes up with `make dev`; run the apps with the commands in
`apps/api/README.md` and `apps/web/README.md`.

## Read this first

| Question | Document |
| --- | --- |
| What is in scope, for whom, and what "done" means | [SPEC.md](SPEC.md) |
| How the system is shaped, and why (10 ADRs) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Tables, tenancy, RLS, `vector(768)` | [docs/DATA_MODEL.md](docs/DATA_MODEL.md) |
| Visual system and UI rules | [docs/DESIGN.md](docs/DESIGN.md) |
| Tests, gates, and what CI actually measures | [docs/TESTING.md](docs/TESTING.md) |
| Current state and locked decisions | [docs/CONTEXT.md](docs/CONTEXT.md) |
| How the plan was audited before being written down | [docs/PROJECT_PLAN_AUDIT.md](docs/PROJECT_PLAN_AUDIT.md) |

## Ground rules

- **Synthetic data only.** No real CVs, no real candidate data, ever (ADR-010).
- **Advisory scoring.** Every score and answer is evidence-linked and human-reviewed; there is no
  auto-rejection path in this system, by design.
- **$0 to run.** Free tiers with their real limits, enforced by guard tests, not by optimism
  (ADR-002; SPEC.md §10).
- **If it can't be linked, it isn't claimed.** Every course and architecture claim points at a commit,
  test, ADR, or recording.

MIT-licensed — see [LICENSE](LICENSE).
