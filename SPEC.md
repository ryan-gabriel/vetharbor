# SPEC — Vetharbor

| | |
| --- | --- |
| **Purpose** | Defines scope, personas, user flows and core requirements. The contract for what "done" means. |
| **Primary reader** | Product owner and AI agent. |
| **Status** | v1.0 — approved for build. Greenfield: no code exists yet. |
| **Owner** | ryan_gabriel_s |
| **Last updated** | 29 Oct 2026 |
| **Related** | `docs/ARCHITECTURE.md` (system), `docs/DATA_MODEL.md` (schema), `docs/TESTING.md` (quality gates), `docs/DESIGN.md` (UI), `docs/CONTEXT.md` (progress) |

**Evidence discipline.** Every requirement in this file is either implemented and linked in `docs/course-evidence.md`, or it is explicitly tagged `[T2]`/`[T3]` as not-yet-shipped. If a claim cannot be linked to a commit, test, ADR or screenshot, it is removed from the README, not defended in prose. This file never states a metric the CI does not measure.

---

## 1. Problem and product

Document screening (CVs, proposals, papers) is done by hand, is inconsistent, and is increasingly automated in ways that are legally and ethically careless: opaque "fit scores", real candidate data uploaded to third-party AI, and automated rejection with no human review.

**Vetharbor** ingests **synthetic or anonymised** documents, extracts entities, computes a transparent **role-match score** against a stored job role, and lets a recruiter ask a guarded retrieval-augmented question across their own documents. Every output is **advisory**: the UI shows the evidence snippet behind each claim and there is no path that auto-rejects a candidate.

The name: *vet* (to screen carefully) + *harbor* (a safe port where untrusted documents are inspected before they come ashore). No product, repository or company was found using it; treat it as provisional until the checklist in §16 is cleared.

**The real product, however, is the engineering story.** Vetharbor is a portfolio milestone: the deliverable a senior reviewer reads is the decision trail (ADRs, tests, threat model, model card) as much as the running app.

## 2. Goals and non-goals

**Goals**

1. Ship a working, deployed, $0-to-run lite demo with a real OIDC auth path and Postgres row-level security proven by tests.
2. Cover all 19 course topics with a linkable artefact (§12), tiered so the claim is honest.
3. Treat hiring-AI risk as engineering: injection corpus, PII filtering, bias audit, model card, human-in-the-loop.
4. Keep the entire critical path reproducible offline so a reviewer can run it themselves (`make dev`).

**Non-goals (out of scope for v1, stated so nobody "improves" them in)**

- Real candidate data. Never. Synthetic or owner-anonymised only (§11).
- Automated rejection, ranking-based shortlisting, or any decision language ("rejected", "disqualified") in the UI.
- Indonesian-language CV processing. spaCy has no trained Indonesian pipeline; the MVP is English documents plus a multilingual embedding model. Indonesian is future work.
- Qdrant or any second vector store. pgvector is the vector store (`ADR-004`).
- A mobile app, billing, teams marketplace, or multi-region deployment.
- A PHP/MySQL "legacy strangler" narrative. Cut: it consumes time and proves nothing Python does not.
- Distributed tracing, service mesh, or a separate API gateway process. One modular monolith (`ADR-001`).

## 3. Personas

| Persona | Wants | Consequence for scope |
| --- | --- | --- |
| **Priya — Recruiter** | Faster shortlist with visible evidence; must be able to disagree with the score | Upload, list, detail, score-vs-role, guarded Q&A. Read and write within her org. |
| **Daniel — Admin** | Control who sees what; audit trail; know when the model is drifting | Org membership, job-role registry, audit log, model version list, DLQ inspection. |
| **Sam — Senior reviewer/interviewer** *(the primary audience)* | Can they be trusted? Do they understand trade-offs? Can I run it? | Honest README, ADRs, failing tests as proof, `make dev` offline path, recorded demo for what is not public. |
| **Regulator-shaped reader** | Is this legal? Is there human review? | AI-Act high-risk framing, PDP-law data policy, model card, fairness audit published including bad news. |

## 4. Roles and permissions

| Capability | `admin` | `recruiter` | `demo_reader` (public) |
| --- | --- | --- | --- |
| Browse documents, entities, scores | yes | yes (own tenant) | yes, seeded synthetic tenants only |
| Ask guarded RAG questions | yes | yes (own tenant) | yes, own tenant only, rate-limited |
| Upload documents | yes | yes | **no** — returns a notice pointing at `make dev` and the recording |
| Create/edit job roles | yes | read-only | read-only |
| Invite/remove members | yes | no | no |
| View audit log, model versions, DLQ | yes | no | no |
| Switch active tenant | members of >1 org | same | single seeded org |

Role lives in `org_memberships` (`ADR-006`). The OIDC token carries identity (`sub`) only — never a tenant or a role.

## 5. Runtime profiles — what each one proves

| Profile | Command | Proves | What it does *not* prove |
| --- | --- | --- | --- |
| **dev** | `make dev` | A reviewer can run the whole thing offline: FastAPI + Postgres/pgvector + React + Keycloak + Ollama, embeddings via local ONNX. Zero keys, zero cloud, zero cost. | Free-tier production constraints. |
| **demo-lite** | `make demo-lite` | Public URL: React on Vercel, one FastAPI service on Render free, Neon Postgres + pgvector, Auth0 OIDC, Gemini embeddings/LLM behind interfaces. Real deployed auth + RLS. | Enterprise parts (Keycloak, Spring, Kubernetes, Ollama) are not in this profile. |
| **demo-full** | `make demo-full` | The enterprise-shaped stack on the laptop: Keycloak, Spring Boot orchestrator with Resilience4j, Postgres queue consumers, Mongo, kind + Calico NetworkPolicy. | Production hosting. Runs locally and in CI only. |

Same code, same event schema, same `vector(768)` column. The profile is an environment switch — a provider registry, not a fork. This is what makes the 768-dimension standardisation non-negotiable (`ADR-005`).

## 6. Core user flows

**F1 — Enter the public demo (happy path, GWT).**
- Given a visitor opens the Vercel URL and clicks **Enter demo**
- When they complete Auth0 login as the seeded `demo_reader` account whose credentials are printed in the README
- Then the API validates the JWT (issuer, audience, expiry, signature), resolves the tenant from `org_memberships`, sets the RLS session variable, and shows a document list from two seeded tenants with only the visitor's own tenant visible
- And an upload attempt returns a read-only notice with a link to `make dev` and the 3-minute recording
- And the response arrives after a "waking up" screen when Render has spun down (about 60 s), never as a blank page

**F2 — Upload and extract (local, `make dev`).**
- Given a recruiter with a valid OIDC session
- When they drag a 2 MB PDF CV into the dropzone
- Then the API enforces allow-listed MIME *and* magic bytes, size and page limits, rejects archives and macro-enabled formats, extracts text in a subprocess with CPU/memory/time caps, flags hidden white-on-white or off-page text, and inserts `documents` + `outbox_events` in **one transaction**
- And the UI polls job status via an `aria-live` region until entities appear
- And no raw file is stored anywhere: only extracted text and metadata (`ADR-008`)

**F3 — Score against a job role.**
- Given an admin has created a `job_roles` record with a description that is embedded at ingest
- When a recruiter selects a document and a role
- Then the scoring module returns skill-overlap, years-of-experience and embedding-similarity components, a `role_match_score` in 0–1, a calibration band, and for each contributing signal a clickable evidence snippet from the document
- And excluded features (name, gender proxy, age, photo, institution prestige) are listed on the result card, not hidden
- And the score is stored against the active `model_versions` row so it is reproducible

**F4 — Guarded cross-document Q&A.**
- Given a tenant with ≥1 processed document
- When the recruiter asks "which candidates have Kubernetes experience?"
- Then retrieval is tenant-scoped by RLS, chunks are wrapped in delimiters and marked as data, an injection classifier screens the combined prompt, the LLM runs with **no tools**, output passes a PII redaction filter for the caller's role, and a canary token check runs
- And the answer lists citation snippets; refusal is a valid, non-error outcome and is displayed as such

**F5 — Poison message to dead letter.**
- Given a consumer fails 3 times on one event
- When the retry budget is exhausted
- Then the row moves to `dead_letter_events` with the reason, an admin-visible entry is created, and reprocessing the same `event_id` after a fix is a no-op because `idempotency_keys` already holds it

**F6 — Admin invites a member across tenants.**
- Given a `sub` that is already a member of tenant A
- When tenant B's admin invites that identity
- Then a second `org_memberships` row is created, the user's tenant switcher gains tenant B, and RLS continues to deny any cross-tenant read in the same session — proven by a test that asserts an empty result set, not an exception

**F7 — Tenant isolation attack attempt (the money flow).**
- Given an authenticated session in tenant A
- When the client asks for a document whose id belongs to tenant B
- Then the API returns not-found, and an integration test proves the SQL under RLS returns zero rows even when the id is guessed

## 7. Functional requirements

Tiers: `[T1]` must ship · `[T2]` should ship · `[T3]` document only.

**Auth (`apps/api` auth module)**
- FR-101 `[T1]` Verify OIDC access tokens: issuer, audience, expiry, signature; reject wrong-audience/expired/replayed tokens.
- FR-102 `[T1]` Resolve tenant and role from `org_memberships` server-side; set the RLS session variable per request.
- FR-103 `[T1]` Active-tenant switching for members of multiple orgs, with an audit-log entry.
- FR-104 `[T2]` Token exchange (RFC 8693) minting an audience-bound, short-lived token for the gateway→worker hop. Confirm Keycloak support level; otherwise implement in the API.
- FR-105 `[T3]` DPoP sender-constrained tokens, with an ADR stating DPoP in a browser does not stop XSS-driven token abuse.

**Upload and extraction**
- FR-201 `[T1]` MIME allow-list plus magic-byte verification; reject on disagreement.
- FR-202 `[T1]` Max size, max page count, reject archives and macro-enabled formats.
- FR-203 `[T1]` Extraction in a subprocess with CPU, memory and wall-clock limits; never render active content.
- FR-204 `[T1]` Hidden-text detection (zero-size, off-page, white-on-white) raising a document warning flag.
- FR-205 `[T1]` Persist extracted text plus metadata only; store the SHA-256 for dedupe and audit.

**NLP**
- FR-301 `[T1]` spaCy `Matcher` + `EntityRuler` with a skills gazetteer (ESCO or O\*NET subset). Off-the-shelf NER does not recognise skills; say so in the docs.
- FR-302 `[T1]` Persist entities with character offsets and rule id so every entity is clickable back to source text.
- FR-303 `[T1]` NER/rule evaluation report (precision/recall on a labelled synthetic set) checked in CI.

**Queue and reliability**
- FR-401 `[T1]` Transactional outbox: `documents` and `outbox_events` in one INSERT transaction.
- FR-402 `[T1]` Consumers claim rows with `SELECT … FOR UPDATE SKIP LOCKED`; no polling loop that defeats Neon scale-to-zero.
- FR-403 `[T1]` Idempotency keyed on `event_id`; duplicate delivery is a no-op.
- FR-404 `[T1]` Three failures → `dead_letter_events` plus an admin-visible alert.
- FR-405 `[T1]` Event schema carries a `version`; consumers accept current plus one prior.
- FR-406 `[T2]` Spring Boot orchestrator applying Resilience4j circuit breakers, bulkheads, jittered backoff and time limiters around the Python NLP/LLM dependency.
- FR-407 `[T2]` Chaos test: kill the NLP service, observe the breaker open and recover.
- FR-408 `[T3]` QStash adapter for a push-based queue where the consumer is a public HTTPS endpoint.

**RAG and guardrails**
- FR-501 `[T1]` pgvector retrieval, tenant-scoped by RLS, `vector(768)`.
- FR-502 `[T1]` LLM provider interface: Gemini (lite), Ollama (dev/full). CI uses a deterministic fake provider and never calls a paid or quota-limited service.
- FR-503 `[T1]` Embedding provider interface, all adapters pinned to 768 dimensions.
- FR-504 `[T1]` Document content treated as data: delimiters, explicit system prompt, zero tools.
- FR-505 `[T1]` Injection classifier plus canary token; canary appearing in output alerts and fails the test suite.
- FR-506 `[T1]` PII output filter (spaCy NER + regex for emails, phone numbers, national ids) with role-based redaction.
- FR-507 `[T1]` Structured JSON-schema output for scoring; free text permitted only in Q&A answers.

**Scoring / ML**
- FR-601 `[T1]` Role-match score as ranking, reported with precision@k and NDCG on a held-out synthetic set, plus a calibration check.
- FR-602 `[T1]` Feature set: skill overlap with the job role, years of experience, embedding similarity. Name, gender proxy, age, photo and institution prestige are absent from the code, not merely unused.
- FR-603 `[T1]` Logistic-regression baseline versus gradient boosting, compared on the same split.
- FR-604 `[T1]` Model card checked into `ml/`, listing data, features, exclusions with reasons, limits and evaluation results.
- FR-605 `[T1]` Shadow evaluation: the candidate model scores in parallel and deltas are logged.
- FR-606 `[T1]` PSI drift check in CI with a failing threshold of 0.25.
- FR-607 `[T1]` Fairness audit notebook measuring score disparity across synthetic demographic variants of otherwise identical CVs. The result is published whatever it says.

**Administration**
- FR-701 `[T1]` Audit log of auth events, uploads, score requests, RAG questions, membership changes.
- FR-702 `[T1]` Job-role registry CRUD for admins.
- FR-703 `[T2]` Mongo document store holding the normalised candidate profile, with an ADR justifying the second store or removing it.

**Web**
- FR-801 `[T1]` Accessible upload, list, detail, score and Q&A views; semantic HTML; client-side validation.
- FR-802 `[T1]` "Waking up" screen for cold starts with expected wait time and automatic retry.
- FR-803 `[T1]` Job-status polling rendered through an `aria-live` region.
- FR-804 `[T1]` Evidence-first score and answer cards: no score or claim without a clickable source snippet.

## 8. Non-functional requirements

- **Cost.** Required spend **$0**. No credit card for any `[T1]` or `[T2]` item. Free-tier facts carry `[verify]` where the plan could not confirm them; re-check in the vendor console before M0 closes.
- **Security.** OWASP LLM Top 10 mapping for LLM01 and LLM06 is a required artefact; STRIDE threat model in `security/`; input validation and rate limiting on upload and Q&A; secrets only in environment stores, never committed.
- **Privacy.** Synthetic data only. Real CVs must never reach a third-party LLM; Google may use free-tier prompts for product improvement, so the Gemini path is exercised with synthetic text alone.
- **Performance.** Render free limits: 512 MB RAM, 0.1 CPU, one service, no torch. First byte on a cold service within about 60 s. No keep-alive pings against any free tier.
- **Reliability.** Idempotent consumers, DLQ, correlation IDs end to end. The lite profile drains the outbox on demand; it has no background worker.
- **Observability.** Structured logs with `correlation_id`, `tenant_id`, `user sub`; no PII in log lines.
- **Accessibility.** WCAG 2.1 AA as a hard requirement (see `docs/DESIGN.md`).
- **Compliance framing.** Hiring-related scoring is treated as high-risk AI use: human-in-the-loop mandatory, no automated adverse decision, documented bias audit, model card. Data handling notes reference the EU AI Act and Indonesia's PDP Law.

## 9. Guardrail acceptance thresholds

Measured on the versioned injection corpus; asserted by CI; failing any one is a build failure.

| Metric | Bar | Notes |
| --- | --- | --- |
| Injection block rate | ≥ 95 % | 50+ attack documents, including "rate this candidate 10/10" CVs |
| Injection false-positive rate | ≤ 5 % | benign CVs wrongly refused |
| Canary leakage | 0 occurrences | any appearance fails the run |
| PII redaction recall on corpus | ≥ 99 % | emails, phone numbers, national ids |
| Cross-tenant retrieval | 0 chunks | RLS-enforced; test asserts empty result |
| Coverage | backend ≥ 80 %, frontend ≥ 70 % line | see `docs/TESTING.md` |
| Model drift (PSI) | < 0.25 | synthetic drift fixture must fail the build |

## 10. ML definition (reframed, deliberately narrower)

The public resume datasets carry *category* labels ("Data Scientist"), not hiring outcomes. Predicting a category from text is classification, not "fitness for hire". Vetharbor therefore computes a **role-match score**: how well a document matches a *specific stored job role*, evaluated as retrieval/ranking (precision@k, NDCG) with a calibration report, and described in a model card as exactly that. Ground truth is manufactured by the synthetic generator: known skill injection plus deliberately mismatched roles produce labelled relevant/irrelevant pairs. Dataset size and licence remain `[verify]`; if either fails, the generator alone is sufficient and the docs say so.

## 11. Data policy

1. Synthetic generation from faker plus templates is the default and only ingest path in CI.
2. Any human-supplied document must be owner-anonymised before upload; the UI states this on the dropzone.
3. No real personal data is committed, ever. The repository is public.
4. Retention: extracted text and entities retained; no raw files (`ADR-008`).
5. Employer and university rules on candidate data are assumed restrictive. Default answer: do not use real data. `[verify]`

## 12. Course coverage

| # | Course | Artefact | Tier |
| --- | --- | --- | --- |
| 1 | HTML/CSS/JS full stack | Accessible upload UI, semantic HTML, client validation | 1 |
| 2 | JavaScript Master | Drag-drop upload, job-status polling | 1 |
| 3 | React | Dashboard with hooks, context, router, deployed on Vercel | 1 |
| 4 | Programming Bootcamp | Python core; scripts and CLI tools (PHP/MySQL dropped) | 1 |
| 5 | Python for Data Science | Preprocessing pipeline (pandas, regex) | 1 |
| 6 | Data Analysis with Python | EDA notebook and dashboard charts | 1 |
| 7 | Relational DB & SQL | Schema, constraints, indexes, RLS policies, analytic queries | 1 |
| 8 | MongoDB for AI | Normalised candidate profiles; vector-search experiment ADR | 2 |
| 9 | spaCy | `EntityRuler` + `Matcher`, skills gazetteer, NER evaluation | 1 |
| 10 | ML A-Z + MLOps | Role-match model, registry, shadow eval, PSI gate | 1 |
| 11 | System Design | C4-lite docs, ADRs, idempotency and retry semantics | 1 |
| 12 | SOA / Event-driven | Outbox, idempotent consumers, DLQ, event schema versioning | 1 |
| 13 | Resilience Patterns | Spring Boot orchestrator, Resilience4j, chaos test | 2 |
| 14 | C# Test Automation | xUnit + RestSharp contract tests, Playwright .NET smoke | 2 |
| 15 | AI Security Fundamentals | AI-SDLC checklist, threat model, observability | 1 |
| 16 | Information Security | RLS, input validation, rate limiting, secrets handling | 1 |
| 17 | Applied AI Security | Injection corpus, guardrail metrics, PII filter | 1 |
| 18 | Kubernetes | Helm chart, kind + Calico, NetworkPolicy proof tests | 2 |
| 19 | R Programming | Quarto statistical report | 2 |

Rule: each row in `docs/course-evidence.md` links to a commit, test, ADR or screenshot. No link, no claim.

## 13. Milestones (~10 h/week, 14 weeks)

| Milestone | Weeks | Done when |
| --- | --- | --- |
| **M0 Foundations** | 1 | Public repo named `vetharbor`; CI green on an empty pipeline; compose file brings up Postgres+pgvector; generator emits 200 synthetic CVs; threat model v0; `ADR-001`, `ADR-002`; all `[verify]` items in §16 re-checked in vendor consoles. |
| **M1 Core MVP** | 2–3 | Schema with `tenant_id` + RLS from day one; upload → safe extraction → spaCy → store; React upload/list/detail; lite deployed; public URL shows entities for a synthetic CV; F7 test proves cross-tenant reads fail. |
| **M2 Outbox, idempotency, resilience** | 4–5 | Outbox table, `SKIP LOCKED` consumers, DLQ, event versions; Spring orchestrator with Resilience4j calling NLP; correlation IDs end to end; killing NLP opens the breaker; poison message lands in DLQ; reprocess is a no-op. |
| **M3 Identity and zero-trust** | 6–7 | Auth0 public + Keycloak local, RBAC via memberships, token exchange for the gateway→worker hop, NetworkPolicy on kind with Calico; wrong-audience, expired and replayed tokens rejected in tests; a denied pod cannot reach Postgres. |
| **M4 RAG and guardrails** | 8–9 | pgvector index, LLM/embedding provider interfaces, injection filter, canary, PII output filter, eval harness; cross-document Q&A works; CI reports block rate and fails below the §9 threshold. |
| **M5 ML and statistics** | 10–11 | Trained and evaluated model, model card, shadow mode, PSI gate, fairness audit, Quarto report; CI fails on the synthetic drift fixture; report published. |
| **M6 Quality gate** | 12–13 | C# contract tests (auth negatives) plus one Playwright happy path; Helm chart; `make k8s-demo`; badge green; chart installs on a clean kind cluster. |
| **M7 Ship** | 14 | README with architecture diagram, 3-minute demo video, `docs/course-evidence.md`, runbook, known-limitations page. |

**Cut order if behind:** `[T3]` items → Quarto in CI (render locally) → Atlas experiment → Playwright (keep contract tests) → Helm (keep plain manifests). Coverage is never traded for features.

## 14. Tier 3 appendix — designed, not scheduled

| Item | Design position | Blocking decision |
| --- | --- | --- |
| **DPoP (RFC 9449)** | Sender-constrained tokens for the gateway→worker hop only. ADR states plainly that browser DPoP does not stop XSS abuse; WebCrypto non-extractable keys plus CSP are the actual browser mitigations. | Keycloak DPoP support level `[verify]`. |
| **QStash adapter** | Optional push transport where the consumer is the FastAPI HTTP endpoint. Free tier 1,000 msg/day, retries may count as deliveries. Never on the critical path. | Consumer must be publicly reachable; therefore not the default. |
| **Atlas M0 vector experiment** | One vector-search index on a normalised profile, benchmarked against pgvector in an ADR. M0 is 512 MB shared and vector-search availability is `[verify]` in the console. | Licence/feature level. |
| **Oracle Always Free VM (k3s)** | 24/7 full-profile host. Needs a card at signup plus capacity and idle-reclaim issues `[verify]`. Stretch goal only; never a dependency of any test or demo. | Regional signup acceptance. |
| **AWS mapping doc** | Table translating each component to a managed service, with a note on what the free-tier design would break in production. | None — pure documentation. |

## 15. Known limitations the README must carry

1. The public demo is a **lite** profile. Keycloak, Spring Boot, Kubernetes and Ollama run in Docker/kind locally and in CI, evidenced by tests and a recording.
2. Visitors cannot upload. Upload is proven locally via `make dev` and on video.
3. Gemini free-tier quotas drift and Google may use free-tier prompts; the LLM path is therefore synthetic-only and behind an interface.
4. A "fit score" would be over-claiming; this is a role-match ranking with manufactured ground truth.
5. Free-tier cold starts make first interaction slow; the UI says so instead of pinging the service awake.
6. English-only NLP; Indonesian is future work.

## 16. Verify before building (owner: product, before M0 closes)

1. Neon: storage (0.5 vs 1 GB) and the 100 CU-hour cap in your own console.
2. Atlas M0: can a vector-search index be created, and how many are allowed?
3. Auth0 free tier: MAU limit, custom claims, no card required. `[verify]`
4. Keycloak: token-exchange and DPoP support level in the pinned version.
5. kind: default CNI versus NetworkPolicy enforcement — install Calico regardless and prove it.
6. Public resume dataset: licence, size, PII. The plan's "96k CVs" figure is unverified.
7. Gemini: model ids and free quotas on the day of integration; pin by id, assume change.
8. Oracle Always Free: card acceptance in your region.
9. Name availability: GitHub org/user, `vetharbor.dev`/`.app`, npm, PyPI, Docker Hub, regional trademark register. Runner-up if blocked: **Quillward**.
10. Indonesian PDP Law plus employer/university rules on candidate data. Default: do not use real data.
