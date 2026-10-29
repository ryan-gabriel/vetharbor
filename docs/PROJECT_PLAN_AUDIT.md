# Vetharbor — Verified & Revised Project Plan

*Document-screening platform with AI guardrails, event-driven ingestion and a pragmatic zero-trust layer. Portfolio milestone, solo-buildable, $0 to run.*

Review date: 28 Oct 2026. Free-tier facts were checked against vendor docs and recent third-party trackers; items I could not confirm are marked **\[verify\]** and listed in section 13.

---

## 1. Executive verdict

**Is the original plan feasible?** The *idea* is good and the architecture vocabulary is credible. As written, it is **not feasible** for four reasons:

1. **Time.** 19 course topics in 6–8 weeks at 8–10 h/week is \~70 hours. This stack (React, FastAPI, Spring Boot, Keycloak, Postgres, Mongo, queue, K8s, ML, R, C# tests) is realistically 150–250 hours. Revised plan: 14 weeks, tiered scope.
2. **Hosting assumptions are stale or wrong.** Render free is 512 MB RAM / 0.1 CPU (torch + spaCy + embeddings will OOM), Qdrant free clusters are suspended after 1 week idle and deleted after 4, Neon free is 100 CU-hours (not 190), and a push-based queue (QStash) cannot deliver to a worker running on your laptop.
3. **Some designs contradict each other.** Public demo has no identity provider (Keycloak is local only); the outbox poller would keep Neon awake and burn the compute quota; "zero-trust token exchange" is applied between components that sit in the same process.
4. **The ML and data plan has a legal and ethical hole.** Hiring-related scoring is a high-risk AI use; real CVs are personal data; a "fit score" trained on role-category labels is circular.

**After the fixes below, the project is feasible at $0**, with one honest caveat: the *public* demo is a "lite" profile; the enterprise-style parts (Keycloak, Spring worker, Kubernetes, Ollama) run in Docker/kind on your laptop and in CI, documented with recordings and tests.

---

## 2. Feasibility audit (component by component)

| Component | Your assumption | What I found | Verdict | Fix |
| --- | --- | --- | --- | --- |
| Vercel Hobby | Free SPA hosting | Free for personal, non-commercial use | OK | Keep; portfolio use is fine |
| Render free web service | 750 h, \~30 s cold start | 750 h/workspace shared across services; spins down after 15 min idle; wake takes **about 1 minute**; 512 MB RAM / 0.1 CPU; ephemeral disk; no background workers on free | **Partly wrong** | One service only; no torch; no local files; "waking up" UX |
| API Gateway + FastAPI Core as 2 Render services | Two services | Both draw on the same 750 h pool; two always-on services exhaust it in \~15 days | **Flaw** | One modular-monolith FastAPI service; gateway = a module |
| Neon Postgres | 0.5 GB, 190 CU-h | **100 CU-h and 0.5 GB per project**, scale-to-zero after 5 min idle; Oct 2026 digest reports free storage doubled to 1 GB **\[verify\]**; pgvector supported | **Numbers wrong** | Budget for 100 CU-h; never poll the DB |
| Outbox relay poller | Poll Postgres continuously | A poller prevents scale-to-zero; 100 CU-h is \~400 h at 0.25 CU (\~17 days) | **Flaw** | On-demand relay (triggered by writes) + optional cron |
| Upstash QStash | \~5–10k msg/month | Free: **1,000 messages/day**, 1 MB max, DLQ available; retries may count as deliveries | OK (better than assumed) | But it is **push (HTTP)**: it needs a public HTTPS consumer |
| Spring Boot worker "local" consuming QStash | Local worker receives events | Impossible without a tunnel; laptop is not publicly reachable | **Flaw** | Postgres-native queue (`SKIP LOCKED`) as default; QStash as optional adapter |
| Qdrant Cloud free | Always-on vector store | 1 GB RAM / 0.5 vCPU / 4 GB disk; **suspended after 1 week unused, deleted after 4 weeks** | **Risky** | Drop from the critical path; pgvector is the vector store |
| MongoDB Atlas M0 | "No Atlas Search / vector search" | 512 MB shared; several 2026 sources say M0 **includes** Atlas Vector Search (with index limits) **\[verify in console\]** | **Claim likely outdated** | Keep as a small, justified document store; optional vector experiment |
| Hugging Face Spaces (my first idea for ML hosting) | — | Free CPU is 2 vCPU/16 GB, **but creating Docker/Gradio Spaces now needs a paid plan**; only static Spaces are free | **Not an option** | Do not use for the API |
| Gemini free tier (LLM fallback) | Free demo LLM | Free tier exists but limits changed several times; sources disagree on RPM/RPD; Google may use free-tier prompts to improve products; model retirements happen | **Privacy risk** | Synthetic data only; provider interface; expect quota drift |
| Keycloak | Local IdP | Needs roughly 1 GB RAM; cannot run on Render free | OK locally | Public demo uses a hosted OIDC provider with a free tier **\[verify\]** |
| GitHub Actions | 2,000 min/month | 2,000 min applies to **private** repos; **public repos are unlimited** | OK | Make the repo public (no real data or secrets in it) |
| kind + NetworkPolicy | Zero-trust between pods | Network policies only work if the CNI enforces them; kind's default CNI may not **\[verify\]** | **Gap** | Install Calico or Cilium; prove it with a failing-curl test |
| Oracle Always Free VM | Optional k3s 24/7 | Generous ARM VM, but needs a card at signup and capacity/idle-reclaim issues **\[verify\]** | Optional | Stretch goal only; never a dependency |
| Embeddings on Render | `all-MiniLM-L6-v2` via sentence-transformers | Pulls in torch (hundreds of MB); will not fit in 512 MB with spaCy | **Flaw** | ONNX runtime (e.g. fastembed) or a hosted embedding API behind an interface |

---

## 3. Design flaws, ranked

**Critical**

1. **Scope vs time** (see section 1).
2. **Hiring AI without a compliance frame.** Scoring candidates is treated as high-risk in many jurisdictions (EU AI Act, and Indonesia's PDP Law applies to personal data). Real CVs must never be uploaded to a free-tier third-party LLM. *Fix:* synthetic/anonymised data only, human-in-the-loop, no automated rejection, documented bias audit.
3. **Circular ML target.** The public resume datasets carry *category* labels (e.g. "Data Scientist"), not hiring outcomes. Predicting category from text is a classification task, not a "fit score". *Fix:* rename it a **role-match score** (document vs job description), evaluate it as retrieval/ranking, and say so in a model card. The "96k CVs" dataset size in the plan is unverified; commonly used public resume sets are much smaller **\[verify license and size\]**.
4. **Queue topology.** Push queue + laptop consumer cannot work; see audit.

**Major**

5. **Zero-trust over-engineering.** Token exchange + DPoP + 60 s tokens between modules in one process adds ceremony without a trust boundary. *Fix:* apply it where a real boundary exists (gateway → ingestion worker) and say so in an ADR.
6. **Public demo has no auth story.** Fix with an IdP-agnostic OIDC layer: Keycloak locally, hosted OIDC publicly.
7. **File upload is the real attack surface** and is under-specified: malicious PDFs, zip bombs, MIME confusion, hidden white-text prompt injection inside CVs.
8. **Language.** spaCy has no trained Indonesian pipeline. Scope the MVP to English CVs and a multilingual embedding model; list Indonesian as future work.
9. **Too many data stores** (Postgres + pgvector + Qdrant + Mongo + folder). Each needs an ADR-level justification. Keep Postgres as system of record, Mongo as a deliberate document-store experiment, drop Qdrant.

**Minor**

10. `legacy-php` strangler story is contrived and consumes time. Cut it; course 4 is covered by Python.
11. "RASA" is not a spaCy feature; you mean spaCy `Matcher`/`EntityRuler`. Off-the-shelf NER does not recognise skills; you need a skills gazetteer (an open taxonomy such as ESCO or O\*NET).
12. Keep-alive pings against free tiers burn quota. Prefer a "warming up" UI plus a recorded demo.

---

## 4. Project name

**Vetharbor** — *vet* (to screen candidates carefully) + *harbor* (a safe port where untrusted documents are inspected before they come ashore).

I searched the web for exact matches and found no product, repository or company using it. Search engines cannot prove absence, so before committing, check: the GitHub org/user, the domain (`vetharbor.dev` / `.app`), npm, PyPI, Docker Hub, and the trademark register for your region. Runner-up: **Quillward**.

---

## 5. Revised product scope

Vetharbor ingests **synthetic or anonymised** CVs, proposals and papers, extracts entities, computes a **role-match score**, and lets a recruiter ask a guarded RAG assistant questions across documents. Two roles: **Admin** and **Recruiter**. Every decision is advisory; the UI shows evidence snippets and never auto-rejects.

**Tiering (this is how you stay honest about the course matrix)**

- **Tier 1 (must ship):** React, FastAPI, Postgres (RLS), spaCy, outbox + idempotent worker, OIDC auth, RAG with guardrails, ML scoring with drift check, CI.
- **Tier 2 (should ship):** Spring Boot orchestrator with Resilience4j, C# test suite, Quarto/R report, Helm + kind with enforced NetworkPolicy.
- **Tier 3 (document only unless time remains):** DPoP-bound tokens, Atlas vector experiment, QStash adapter, Oracle VM, AWS mapping doc.

---

## 6. Revised architecture

### Two runtime profiles

|  | **Lite (public demo)** | **Full (laptop + CI)** |
| --- | --- | --- |
| Web | React on Vercel | same |
| API | One FastAPI service on Render free (spaCy small model, no torch) | FastAPI in Docker/kind |
| Auth | Hosted OIDC provider (free tier) **\[verify\]** | Keycloak |
| DB | Neon Postgres + pgvector | Postgres + pgvector |
| Async | Outbox drained on demand by the API | Outbox drained by Spring Boot worker |
| LLM | Provider interface: Gemini free (synthetic data only) | Ollama (e.g. a 3B instruct model) |
| Embeddings | ONNX model or hosted API behind an interface | sentence-transformers |
| Docs store | — | Mongo (local) or Atlas M0 |

The **same code and the same event schema** run in both. The profile is an environment switch (`make demo-lite`, `make demo-full`).

### Request and event flow

```
Browser (React/Vercel)
   │ HTTPS + OIDC access token
   ▼
FastAPI modular monolith (Render free)
   ├─ auth module  : verify JWT, RBAC, tenant context → Postgres RLS
   ├─ upload module: size/type checks, sandboxed text extraction
   ├─ NLP module   : spaCy EntityRuler + Matcher
   ├─ rag module   : retrieval → guardrails → LLM → output filter
   └─ outbox       : INSERT documents + outbox_events in ONE transaction
                        │
        Lite: on-demand drain        Full: Spring Boot worker
                        ▼
   consumers claim rows with SELECT … FOR UPDATE SKIP LOCKED
   idempotency key = event_id; 3 failures → dead_letter table + alert
```

**Why a Postgres-native queue by default:** it keeps the transactional outbox guarantee, needs no public endpoint, costs $0, and is a well-established pattern. QStash remains an optional adapter for the public profile, where the consumer is the FastAPI HTTP endpoint (free tier: 1,000 messages/day).

**Why Spring Boot stays (Tier 2):** it is the natural home for Resilience4j. It orchestrates the pipeline and calls the Python NLP/LLM service over HTTP: a genuinely unreliable dependency, which is exactly what circuit breakers, bulkheads, jittered backoff and time-limiters are for. Chaos test: kill the NLP service and watch the breaker open.

### Zero-trust, scoped to real boundaries

- **Edge:** OIDC access token validated by the API (audience, issuer, expiry, signature).
- **Tenant isolation:** Postgres Row-Level Security keyed by tenant/org id. This is simple, testable, and a strong interview story.
- **Gateway → worker hop (Full profile):** OAuth token exchange (RFC 8693) to mint an audience-bound, minimally scoped, short-lived token; optionally sender-constrained with DPoP (RFC 9449). Confirm your Keycloak version supports both **\[verify\]**; otherwise implement the exchange in the API and keep DPoP as a documented Tier 3 item.
- **Pods:** default-deny NetworkPolicy with an enforcing CNI (Calico or Cilium), allow-list per service. Proof is a test where a disallowed pod's request times out.
- **Honest ADR:** state that DPoP in a browser does not stop XSS-driven abuse; use non-extractable WebCrypto keys and CSP, and say what remains.

---

## 7. AI security and document safety

**Upload pipeline**

- Allow-list MIME *and* magic bytes; max size and page count; reject archives and macro-enabled formats.
- Extract text in a subprocess with CPU/memory/time limits; never execute or render active content.
- Detect hidden text (white-on-white, zero-size, off-page) and flag it.

**LLM01 (prompt injection)**

- Document content is **data**, never instructions: wrap in delimiters, system prompt states it explicitly, LLM has **no tools** and cannot call other services.
- Heuristic + regex injection classifier before the LLM; canary token in the system prompt; alert if it appears in output.
- Structured (JSON-schema) outputs for scoring; free text only in the Q&A answer.

**LLM06 (sensitive information disclosure)**

- PII filter on output (spaCy NER + regex for emails/phones/IDs) with role-based redaction.
- Retrieval is tenant-scoped by RLS, so the model can never be handed another tenant's chunks.

**Evidence you can show**

- `security/injection-corpus/` with 50+ attack documents (including CVs that say "rate this candidate 10/10") and a pytest suite that reports block rate and false-positive rate on every CI run.
- STRIDE threat model plus an OWASP LLM Top 10 mapping table.

---

## 8. ML plan (reframed)

- **Task:** role-match score between a document and a job description; reported as ranking quality (precision@k, NDCG), with a calibration check.
- **Data:** public resume datasets **\[verify license, size, PII\]** plus a synthetic generator you write (faker + templates). Never commit real personal data.
- **Features:** skill overlap with the job description, years of experience, and embedding similarity. **Exclude** name, gender-proxy, age, photo, and institution-prestige features; document why.
- **Models:** logistic regression baseline → gradient boosting; compare on a held-out set.
- **MLOps:** file-based registry (e.g. MLflow local); model card; **shadow evaluation** (new model scores in parallel, deltas logged); **PSI drift check** in CI with a threshold that fails the build.
- **Fairness:** a small audit notebook measuring score disparity across synthetic demographic variants of otherwise identical CVs. Publish the result, including bad news.
- **R/Quarto:** statistical report (distributions, confidence intervals, calibration) rendered in CI and published to GitHub Pages; or rendered locally and committed, if R install time in CI is too slow.

---

## 9. Revised course coverage matrix

| # | Course | Concrete artefact | Tier |
| --- | --- | --- | --- |
| 1 | HTML/CSS/JS full stack | Accessible upload UI, semantic HTML, client validation | 1 |
| 2 | JavaScript Master | Drag-drop upload, job-status polling | 1 |
| 3 | React | Dashboard with hooks, context, router, deployed on Vercel | 1 |
| 4 | Programming Bootcamp | Python core; scripts and CLI tools (PHP/MySQL dropped) | 1 |
| 5 | Python for Data Science | Preprocessing pipeline (pandas, regex) | 1 |
| 6 | Data Analysis with Python | EDA notebook and dashboard charts | 1 |
| 7 | Relational DB & SQL | Schema, constraints, indexes, RLS policies, analytic queries | 1 |
| 8 | MongoDB for AI | Normalised candidate profiles; vector search experiment ADR | 2 |
| 9 | spaCy | EntityRuler + Matcher, skills gazetteer, NER evaluation | 1 |
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

Every row in `docs/course-evidence.md` must link to a commit, test, ADR or screenshot. If you cannot link it, do not claim it.

---

## 10. Free-tier budget (revised)

| Service | Real limit (as checked) | Design rule |
| --- | --- | --- |
| Vercel Hobby | Personal, non-commercial | Static SPA only |
| Render free | 512 MB / 0.1 CPU, 750 h shared, idle after 15 min, \~1 min wake | One service; no torch; no local files; "waking up" screen |
| Neon free | 100 CU-h, 0.5 GB (maybe 1 GB now), scale-to-zero | No pollers; pooled connections; store extracted text, not raw files |
| QStash free | 1,000 msg/day | Optional adapter only |
| Qdrant free | Suspended after 1 week idle, deleted after 4 | Not used |
| Atlas M0 | 512 MB shared | Small profile store; verify search features in console |
| GitHub Actions | Unlimited on public repos; 2,000 min on private | Public repo, no secrets in code |
| Gemini free | Volatile quotas; prompts may be used by Google | Synthetic data only; fallback to Ollama locally |
| Keycloak / Ollama / kind | Local | Needs \~16 GB RAM for the full stack; `demo-lite` for smaller machines |

Total required spend: **$0**. No credit card should be needed for any Tier 1 or Tier 2 item.

---

## 11. Repository layout

```
vetharbor/
├── apps/
│   ├── web/            # React + Vite (Vercel)
│   └── api/            # FastAPI modular monolith (Render)
├── services/
│   └── orchestrator/   # Spring Boot + Resilience4j (Full profile)
├── ml/                 # spaCy rules, features, training, registry, drift
├── reports/            # Quarto/R statistics
├── tests-e2e/          # C#: xUnit, RestSharp, Playwright .NET
├── security/           # threat model, injection corpus, AI-SDLC checklist
├── infra/              # docker-compose, helm, kind + Calico
├── docs/               # architecture, ADRs, course-evidence, runbook
└── .github/workflows/  # lint → unit → integration → e2e → drift → deploy
```

---

## 12. Milestones (14 weeks, \~10 h/week)

**M0 — Foundations (week 1)** Public repo, CI skeleton, compose file, synthetic data generator, threat model v0, ADR-001 (modular monolith), ADR-002 (free-tier constraints). *Done:* CI green on an empty pipeline; synthetic generator produces 200 CVs.

**M1 — Core MVP (weeks 2–3)** Schema with `tenant_id` + RLS from day one; upload → safe extraction → spaCy → store; React upload/list/detail; deploy lite profile. *Done:* public URL shows entities for a synthetic CV; RLS test proves cross-tenant reads fail.

**M2 — Outbox, idempotency, resilience (weeks 4–5)** Outbox table, `SKIP LOCKED` consumers, DLQ, event schema versions; Spring orchestrator with Resilience4j calling the NLP service; correlation IDs end to end. *Done:* killing the NLP service opens the breaker; poison message lands in DLQ; reprocessing the same event is a no-op.

**M3 — Identity and zero-trust (weeks 6–7)** OIDC (Keycloak local, hosted IdP public), RBAC, token exchange for the gateway → worker hop, NetworkPolicy on kind with Calico. *Done:* wrong-audience, expired and replayed tokens are rejected in tests; a denied pod cannot reach Postgres.

**M4 — RAG and guardrails (weeks 8–9)** pgvector index, provider interfaces for LLM and embeddings, injection filter, canary, PII output filter, eval harness. *Done:* cross-document Q&A works; CI reports injection block rate and fails below your threshold.

**M5 — ML and statistics (weeks 10–11)** Train and evaluate; model card; shadow mode; PSI gate; fairness audit; Quarto report. *Done:* CI fails on synthetic drift; report published.

**M6 — Quality gate (weeks 12–13)** C# contract tests (auth negatives) and one Playwright happy path; Helm chart; `make k8s-demo`. *Done:* badge green; chart installs on a clean kind cluster.

**M7 — Ship (week 14)** README with architecture diagram, 3-minute demo video, `docs/course-evidence.md`, runbook, known-limitations page.

**Cut order if you fall behind:** Tier 3 items → R report in CI (render locally) → Atlas experiment → Playwright (keep contract tests) → Helm (keep plain manifests).

---

## 13. Verify before you build

1. Neon free storage (0.5 vs 1 GB) and CU-hour cap in your console.
2. Atlas M0: can you create a vector search index? How many search indexes are allowed?
3. Hosted OIDC provider free tier (limits, no card, custom claims).
4. Keycloak version: token exchange and DPoP support level.
5. kind default CNI vs NetworkPolicy enforcement; install Calico regardless.
6. Public resume dataset: license, size, PII; or skip it and rely on the synthetic generator.
7. Gemini model IDs and free quotas on the day you integrate; assume they will change.
8. Oracle Always Free signup requirements in your region (card acceptance).
9. Name availability: GitHub, domain, npm, PyPI, Docker Hub, trademark register.
10. Indonesian PDP Law and any employer or university rules on using real candidate data (default answer: do not).

---

## 14. What makes this credible to a senior reviewer

- Every claim is backed by a test or an ADR, not a checkbox.
- The plan states its limits: free-tier trade-offs, the lite/full split, and what the demo does not prove.
- Hiring-AI risks are treated as part of the engineering, not an afterthought.
