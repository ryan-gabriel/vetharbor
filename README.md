# Vetharbor

Document screening with AI guardrails, event-driven ingestion, and a pragmatic zero-trust layer —
built to run at $0. *Vet* (screen carefully) + *harbor* (untrusted documents are inspected before they come ashore).

**Status: M0 foundations, documentation complete, code not started.** This repository currently contains the
governing documents; there is no running application yet. When the demo exists it will be linked here, with a
3-minute recording and a `make dev` offline path (SPEC.md §5).

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

MIT-licensed (license file arrives with the public repo in M0).
