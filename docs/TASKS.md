# TASKS — Vetharbor

Actionable implementation backlog from M1 through shipping. Tasks are complete only when the implementation, tests, and required documentation are all present.

## How to use this backlog

- Work from the earliest incomplete milestone. Do not start a later milestone to avoid an unresolved dependency.
- Split a task into smaller tasks if implementation reveals distinct deliverables; keep the original acceptance criteria.
- Update task status and `docs/PROGRESS.md` at the end of each work session.
- Do not mark a task done because code exists. Its tests and acceptance criteria must pass.
- Keep claims in documentation, the README, and course evidence limited to behavior that has working test or demo evidence.
- If a requirement conflicts with a design document, stop and report the conflict instead of silently changing the design.

### Status

- `[ ]` Not started
- `[~]` In progress
- `[x]` Done; acceptance criteria verified
- `[!]` Blocked; document the blocker and the decision or input needed

## Project invariants

These apply to every milestone:

- `SPEC.md` defines product behavior; `docs/ARCHITECTURE.md` defines module boundaries; `docs/DATA_MODEL.md` is authoritative for database design.
- Use `org_id` for tenant ownership, not `tenant_id`. Resolve the active organization from server-side membership data; never trust a tenant or role supplied by the client or token.
- Tenant isolation must be enforced in Postgres with RLS, not just application filters. The persistence layer alone sets transaction-local RLS settings.
- Keep the FastAPI modular-monolith boundaries. Feature modules must not import another feature’s ORM models or repositories.
- Postgres is the system of record. Do not add another database or vector store unless a documented tier explicitly requires it.
- Every embedding is exactly 768 dimensions. Provider adapters and repositories must reject mismatches.
- Use synthetic data only. Do not commit real personal information, document contents, secrets, or provider credentials.
- Never persist raw uploaded files or file paths. Persist extracted text and allowed metadata only.
- All scores and generated answers are advisory. Do not implement automatic rejection or other adverse-action flows.
- Keep `demo-lite` compatible with one low-resource API service: no local-file persistence, heavyweight model runtime, always-running worker, or keep-alive pings.
- Use the existing project Makefile and quality commands. Do not invent a parallel build or test workflow without documenting why it is needed.

## M0 — Foundations

**Status:** Done on 4 November 2026. See `docs/PROGRESS.md`.

Do not reopen M0 work unless a later task exposes a regression or a documented gap.

## M1 — Core MVP

**Goal:** Build the tenant-safe data foundation and the local upload-to-entity flow; provide the document list and detail UI; deploy the read-only lite profile.

**Dependencies:** M0 complete.

### M1-1 — Schema, migrations, and RLS

- [ ] Create Alembic migrations for the M1 tables and Postgres enum types defined in `docs/DATA_MODEL.md`. Keep migrations forward-only and focused on one logical change.
- [ ] Add `org_id` to every tenant-scoped table, with the specified foreign keys, constraints, and indexes. Document any intentional exception in the data model.
- [ ] Enable **and force** RLS on tenant-scoped tables. Apply tenant-scoped `USING` and `WITH CHECK` policies consistently; do not rely on ORM filtering as the security boundary.
- [ ] Add the documented database roles and grants. Runtime application credentials must not be migration credentials and must not have `BYPASSRLS`.
- [ ] Make `scores` and `audit_log` append-only for the application role by revoking update and delete privileges.
- [ ] Add the specified `vector(768)` columns and pgvector extension. Validate vector dimensions in provider adapters and repositories before database writes.
- [ ] Configure persistence to set tenant, user, and admin session values transaction-locally, in the same transaction as tenant-scoped work. Do not accept an RLS tenant value from request input.
- [ ] Add a migration/schema check that verifies every tenant-scoped table has the expected RLS configuration and every embedding column is `vector(768)`.
- [ ] Generate and review the schema snapshot at `docs/schema.sql` if supported by the existing tooling. Include policy and privilege changes in the review.
- [ ] Add migration tests for constraints, indexes, enum values, RLS, and append-only permissions using the application role, not a database superuser.

**Acceptance criteria**

- Migrations apply to a clean local database and produce the schema specified in `docs/DATA_MODEL.md`.
- Tests confirm the application role cannot update or delete scores or audit records.
- Tests confirm missing or incorrect tenant context yields no tenant rows; tests do not use a privileged role that bypasses RLS.
- Schema and vector-dimension checks run in CI.

### M1-2 — Secure upload and text extraction

- [ ] Implement an upload service in the upload module. Keep routing, validation, extraction, persistence, and event creation in their designated module/service boundaries.
- [ ] Enforce the configured MIME allow-list and verify file magic bytes. Reject a declared/detected MIME disagreement.
- [ ] Reject empty files, files over 5 MB, documents over 60 pages, archives, macro-enabled formats, and unsupported or encrypted documents. Return a stable typed error without exposing internal details.
- [ ] Sanitize filenames for display only. Never use a client-provided filename as a storage path, command argument, or trusted content type.
- [ ] Run text extraction in a subprocess with explicit CPU, memory, and wall-clock limits. Terminate and classify a timed-out or over-limit process; do not render active content.
- [ ] Support the agreed English text-layer document formats. Do not add OCR or claim scanned-document support; those are out of scope.
- [ ] Detect and record supported warning conditions such as hidden, zero-size, white-on-white, or off-page text where the extractor exposes sufficient information.
- [ ] Compute SHA-256 while reading the upload. Store extracted text and approved metadata only; verify that raw bytes and temporary files are removed on success, failure, timeout, and cancellation.
- [ ] Apply request-size limits at both the application and server/proxy boundary where configurable. Avoid reading an unbounded multipart body into memory.
- [ ] In read-only demo mode, reject upload server-side regardless of UI state or client-supplied values.
- [ ] Add safe error handling: distinguish rejected input from processing failure, do not return stack traces, and do not log document text or PII.
- [ ] Add upload abuse controls: rate/size limits, bounded concurrency, and limits on extraction work. Keep limits configurable and document the selected values.

**Acceptance criteria**

- Tests cover accepted files, MIME/signature mismatch, malformed files, archives, macro-enabled files, size/page limits, timeouts, resource-limit failures, and cleanup.
- A test verifies the demo’s read-only setting rejects a direct API upload request.
- No raw-file bytes or file paths are persisted. Logs and error responses contain no extracted text.
- An upload that fails validation is not inserted as a successfully processable document.

### M1-3 — NLP, entities, and evidence offsets

- [ ] Implement the NLP service behind the architecture-defined interface. Keep NLP-specific rules and assets in the designated NLP/ML locations.
- [ ] Add spaCy `Matcher` and `EntityRuler` rules plus a versioned, documented skills-gazetteer subset. Do not describe general-purpose NER as a skills recognizer.
- [ ] Persist the required entity fields, including source/rule identifier, label, text, and character offsets into the exact extracted text.
- [ ] Validate every entity offset: `0 <= char_start < char_end <= len(extracted_text)`, and confirm the referenced substring matches the stored entity text under the chosen normalization rules.
- [ ] Ensure normalization preserves the original text and offsets used for UI evidence.
- [ ] Add a versioned synthetic labelled evaluation set and a reproducible precision/recall report for the NLP rules. Keep all test content synthetic.
- [ ] Make NLP processing deterministic where practical; record the pipeline/rules version so results can be reproduced.

**Acceptance criteria**

- Tests verify entities are tenant-scoped, offsets are valid, and evidence points back to the expected source text.
- CI runs the NLP evaluation report and catches invalid offsets or a regression against the documented baseline.
- Seeded entities are produced by the pipeline, not hard-coded into the database.

### M1-4 — Document and outbox transaction

- [ ] Persist the document row and its initial outbox event in one database transaction. A failure must not leave a document without its event or an event without its document.
- [ ] Use the agreed event schema, including `event_id`, `org_id`, aggregate identity, event type, version, occurrence time, and correlation ID.
- [ ] Validate event payloads at write and consume boundaries. Payloads must contain identifiers and required metadata, not unnecessary document text or secrets.
- [ ] Implement an initial bounded drain path appropriate to the active profile. In lite mode, drain on demand; do not add a background polling loop.
- [ ] Make processing updates atomic and safe under duplicate delivery. Do not mark an event complete before its resulting data is committed.
- [ ] Bound the amount of work performed per API request/drain pass so a large backlog cannot monopolize the request or service.

**Acceptance criteria**

- Transaction tests verify both writes commit or neither does.
- Duplicate delivery does not create duplicate entities or other effects.
- The lite profile has no continuously running queue poller.

### M1-5 — Tenant-scoped API and integration tests

- [ ] Implement document list, document detail, and processing-status endpoints with tenant-scoped queries and stable pagination.
- [ ] Return `not_found` for an identifier outside the active tenant rather than confirming that another tenant owns it.
- [ ] Ensure list endpoints have explicit page-size limits, deterministic ordering, and appropriate indexes. Do not load all tenant documents into memory.
- [ ] Add F7 integration coverage: tenant A requests a tenant B document by guessed ID; the API returns not-found and a direct query under tenant A’s RLS context returns zero rows.
- [ ] Add tests that a caller cannot select an organization they do not belong to, even if they submit its ID.
- [ ] Add a pooled-connection reuse test proving transaction-local RLS state does not leak between requests.
- [ ] Add the two-tenant fixture required by `docs/DATA_MODEL.md`, including an overlapping document title with different bodies.
- [ ] Keep error responses consistent with the existing typed error envelope. Do not expose SQL, paths, tokens, or provider errors.

**Acceptance criteria**

- Cross-tenant isolation is proved against Postgres RLS, not only mocked repositories.
- Pagination, ordering, and tenant filtering are covered by tests.
- The test suite includes a direct SQL zero-row assertion under the application role.

### M1-6 — React document experience

- [ ] Build the upload, list, and detail flows using the existing feature-folder structure and shared API client. Do not call `fetch` directly from components.
- [ ] Implement `UploadDropzone`, `DocumentSheet`, and `EvidenceRail` consistent with `docs/DESIGN.md`.
- [ ] Show the upload policy, supported formats, size/page limits, and synthetic/anonymised-data notice before upload.
- [ ] Disable upload in the public demo for usability, but rely on the server-side read-only enforcement for security.
- [ ] Use tenant-aware TanStack Query keys and invalidate the relevant list/detail/status queries after mutations or processing updates.
- [ ] Poll job status with a bounded interval and stop polling on completion, terminal failure, navigation away, or unmount. Avoid unbounded retries.
- [ ] Render processing, ready, rejected, failed, empty, rate-limited, forbidden, not-found, and waking-up states accessibly.
- [ ] Put status updates in an appropriate `aria-live` region. Support keyboard navigation, visible focus, semantic controls, and meaningful error text.
- [ ] Render entity evidence using validated character offsets. Do not trust server-provided HTML or inject document text as markup.
- [ ] Test that changing active tenant cannot reuse another tenant’s cached document data.

**Acceptance criteria**

- Frontend tests cover loading, success, error, empty, polling, and tenant-switch/cache behavior.
- Accessibility checks cover keyboard use and live status updates; do not rely on color alone to convey state.
- Production frontend build passes.

### M1-7 — Lite deployment and demo readiness

- [ ] Deploy the static SPA and single API service using the documented lite profile and a scoped database credential.
- [ ] Run migrations through the documented developer/CI process, not automatically from the Render service at boot.
- [ ] Configure the public demo as read-only in the database-backed demo state and verify upload is blocked by the API.
- [ ] Confirm deployed configuration contains no development secrets, debug mode, local file persistence, or unintended external provider calls.
- [ ] Verify the waking-up flow handles API cold starts without a blank screen or repeated unbounded requests.
- [ ] Seed only the deterministic synthetic corpus using the approved seed process.
- [ ] Record the deployed URL, verification evidence, and known deployment limitations in `docs/PROGRESS.md` and the runbook.

**M1 exit gate**

- [ ] All M1 acceptance criteria pass locally and in CI.
- [ ] `make test`, lint, type-check, and production build pass using the repository’s current commands.
- [ ] F7 isolation tests pass against a real Postgres instance configured with the application role.
- [ ] The public lite demo shows synthetic documents/entities and refuses upload server-side.
- [ ] Update `docs/PROGRESS.md`; do not start M2 with failing M1 security or data-integrity gates.

## M2 — Outbox, idempotency, and resilience

**Goal:** Make event processing safe under concurrent claims, retries, failures, and replay.

### M2-1 — Reliable outbox consumer and DLQ

- [ ] Implement the `SELECT ... FOR UPDATE SKIP LOCKED` claim path using a short transaction and the indexes specified in `docs/DATA_MODEL.md`.
- [ ] Ensure a claimed event cannot be processed concurrently by two consumers. Define and test behavior for abandoned/stale claims.
- [ ] Enforce the retry limit of three attempts and atomically mark exhausted events failed while creating the corresponding dead-letter record.
- [ ] Keep `last_error` sanitized; never put document text, credentials, or raw provider responses into DLQ records.
- [ ] Implement admin-only DLQ inspection and replay according to `docs/DATA_MODEL.md`. Replay creates a new event ID; preserve the original idempotency record.
- [ ] Keep lite draining bounded and on demand. Implement full-profile worker behavior only in its designated profile.

### M2-2 — Idempotency and event compatibility

- [ ] Make each consumer’s side effects and idempotency record part of one transaction.
- [ ] Treat duplicate delivery of an already processed `event_id` as a successful no-op.
- [ ] Validate event versions and support the current and immediately previous version. Reject unsupported versions safely and observably.
- [ ] Add migration/contract tests for event payload evolution.
- [ ] Verify replay behavior against the documented model; do not assume a replay should repeat an already committed effect.

### M2-3 — Correlation, resilience, and failure behavior

- [ ] Propagate a correlation ID through request, outbox event, consumer, and downstream call. Generate one when absent and validate its format/length.
- [ ] Emit structured logs with correlation ID, event ID, route, status, and duration. Never log PII or document content.
- [ ] Add bounded retries with jitter where appropriate; avoid retrying validation, authorization, or other permanent failures.
- [ ] For the full profile, implement the Spring Boot orchestrator with Resilience4j as described in `docs/ARCHITECTURE.md`; keep it out of the lite deployment.
- [ ] Add timeouts and bulkheads around the unreliable downstream NLP call. Document retry ownership so multiple layers do not multiply retries.
- [ ] Add failure-injection tests: concurrent claims, duplicate events, worker termination, poison event, retry exhaustion, DLQ creation, and replay.
- [ ] Add the orchestrator chaos test: stop the NLP dependency, verify requests fail fast after breaker opening, and verify no event is silently lost.

**M2 exit gate**

- [ ] Concurrent consumers never apply the same event twice.
- [ ] Poison events reach the DLQ after the configured retry budget; failure details are sanitized.
- [ ] Replay behavior and event-version compatibility are demonstrated by tests.
- [ ] Correlation IDs can be followed end to end in logs without logging sensitive content.
- [ ] Lite profile remains free of a polling worker.

## M3 — Identity and zero-trust

**Goal:** Validate OIDC identity, resolve authorization from memberships, and prove the planned network boundary.

### M3-1 — OIDC authentication and membership authorization

- [ ] Configure Auth0 for the public profile and Keycloak for local development using provider-neutral OIDC settings.
- [ ] Validate signature, issuer, audience, expiry, and required token claims. Cache JWKS safely and handle key rotation.
- [ ] Fail closed for malformed, expired, wrong-issuer, wrong-audience, and invalid-signature tokens.
- [ ] Resolve user identity from issuer and subject; resolve organizations and roles from active `org_memberships`, never from a tenant or role claim.
- [ ] Enforce the permission matrix in `SPEC.md` on every protected operation, including object-level access.
- [ ] Implement tenant switching only for organizations where the user has active membership; audit the switch.
- [ ] Add negative tests for revoked/invited memberships, wrong roles, cross-tenant IDs, and unauthenticated requests.
- [ ] Ensure auth logs contain no access tokens, email addresses, or other PII.

### M3-2 — Worker identity and token exchange

- [ ] Verify the pinned Keycloak version’s RFC 8693 support and record the result.
- [ ] If supported and appropriate, implement short-lived, audience-bound, minimally scoped tokens for a real gateway-to-worker service boundary.
- [ ] If it is not supported, implement the documented API-side alternative and record the trade-off. Do not add token exchange between modules in the same process.
- [ ] Test wrong-audience, expired, and insufficient-scope service tokens.

### M3-3 — Kubernetes NetworkPolicy proof

- [ ] Build the local kind environment with a CNI that enforces NetworkPolicy; document and verify the selected CNI.
- [ ] Apply default-deny policies before adding explicit required traffic.
- [ ] Allow only the traffic required by the deployed components, following `docs/ARCHITECTURE.md`.
- [ ] Add automated proof tests showing allowed traffic succeeds and a denied pod cannot reach Postgres.
- [ ] Keep Kubernetes networking out of the public lite deployment.

**M3 exit gate**

- [ ] Auth negative tests pass for invalid token and membership cases.
- [ ] Tenant and role decisions are server-side and membership-based.
- [ ] NetworkPolicy tests run against an enforcing CNI and prove a denied connection fails.

## M4 — RAG and guardrails

**Goal:** Add tenant-scoped retrieval and guarded Q&A with measurable security and privacy gates.

### M4-1 — Embedding and retrieval

- [ ] Implement embedding and LLM provider interfaces from `docs/ARCHITECTURE.md`; use deterministic fake providers in CI.
- [ ] Pin provider/model configuration and verify every embedding is exactly 768 dimensions before persistence.
- [ ] Implement chunking with stable ordering, bounded chunk size, and valid offsets into extracted text.
- [ ] Add pgvector indexes and tenant-filtered retrieval according to `docs/DATA_MODEL.md`. Keep RLS as the isolation boundary.
- [ ] Set `ef_search` per request class as specified; do not raise a global setting without measurement.
- [ ] Add retrieval tests for ranking, empty results, embedding mismatch, and zero cross-tenant chunks.
- [ ] Benchmark the seeded corpus and record recall/latency baselines. Avoid claiming a performance improvement without a reproducible comparison.

### M4-2 — Prompt injection and output safeguards

- [ ] Treat retrieved content as untrusted data: delimit it, label it as data, and keep it separate from trusted instructions.
- [ ] Ensure the LLM interface exposes no tools or tool execution path.
- [ ] Add the injection classifier and versioned corpus with at least 50 attack examples and representative benign examples.
- [ ] Add a per-run canary and fail tests if it appears in user-visible output or logs.
- [ ] Add output PII detection/redaction for the specified email, phone, and national-ID cases; apply role-based redaction.
- [ ] Validate answer structure, citations, and output size. Return a safe refusal when evidence is insufficient or a guardrail blocks the request.
- [ ] Ensure prompts and responses sent to external providers contain only allowed synthetic/anonymized data. Keep all external providers disabled in CI.
- [ ] Rate-limit Q&A and bound question length, retrieved context size, provider timeout, and response size.
- [ ] Persist the required audit/evaluation fields without logging sensitive content.

### M4-3 — Evaluation and acceptance gate

- [ ] Build a deterministic evaluation harness that reports injection block rate, false-positive rate, canary leakage, PII recall, and cross-tenant retrieval.
- [ ] Store the corpus version and provider identity with results; CI must use fake providers.
- [ ] Fail CI unless all `SPEC.md` §9 thresholds pass:
  - Injection block rate >= 95%.
  - Injection false-positive rate <= 5%.
  - Canary leakage = 0.
  - PII redaction recall >= 99%.
  - Cross-tenant retrieved chunks = 0.
- [ ] Add tests that ensure a refusal is a valid outcome and is not presented as a server error.
- [ ] Add an end-to-end Q&A test that verifies citations resolve to tenant-visible source evidence.

**M4 exit gate**

- [ ] All security thresholds are computed by tests and enforced in CI, not asserted only in documentation.
- [ ] Cross-tenant retrieval returns zero chunks under the real RLS configuration.
- [ ] CI cannot access Gemini credentials or call external providers.

## M5 — Scoring, ML, and statistics

**Goal:** Produce a transparent, reproducible role-match signal with documented limitations and fairness review.

### M5-1 — Scoring contract and evaluation

- [ ] Implement scoring behind the scoring module interface using only the approved features: skill overlap, years of experience, and embedding similarity.
- [ ] Verify excluded attributes (including name, gender proxy, age, photo, and institution prestige) are absent from feature construction, not merely ignored by a model.
- [ ] Return a structured, schema-validated result with component values, band, model version, and evidence offsets.
- [ ] Use neutral score bands, including `insufficient_evidence`. Do not introduce pass/fail, automatic rejection, or adverse-action language.
- [ ] Store scores as append-only records tied to the job role, document, model version, and evidence.
- [ ] Generate a deterministic synthetic dataset with a recorded seed and held-out split. Do not use unverified public data as a required dependency.
- [ ] Compare the logistic-regression baseline with gradient boosting on the same split; report precision@k, NDCG, and calibration.
- [ ] Add tests for invalid values, missing evidence, feature exclusions, reproducibility, and score persistence.

### M5-2 — Model card, shadow evaluation, and drift

- [ ] Check in a model card listing intended use, synthetic data source, feature definitions, exclusions and reasons, evaluation results, limits, and prohibited interpretations.
- [ ] Implement shadow scoring in a separate storage/query path that cannot leak into user-facing score results.
- [ ] Log shadow deltas against the compared score and test that shadow rows do not appear in normal recruiter queries.
- [ ] Implement PSI calculation with a documented binning method and deterministic fixtures.
- [ ] Fail CI when PSI is >= 0.25 for the required drift fixture; include a passing control fixture.
- [ ] Run a fairness audit on synthetic demographic variants of otherwise identical documents. Publish results, including unfavorable findings, without implying real-world fairness is proven.
- [ ] Produce the required Quarto statistical report and keep its inputs synthetic and reproducible.

**M5 exit gate**

- [ ] Metrics are generated from a held-out synthetic set and are reproducible from the recorded seed/version.
- [ ] CI proves the drift threshold and the fairness report is checked in.
- [ ] The UI explains the score is advisory, shows its evidence and limitations, and provides no automated adverse-action flow.

## M6 — Quality gate and full-profile demo

**Goal:** Exercise the external contracts and demonstrate the local full profile repeatably.

### M6-1 — Contract, browser, and accessibility tests

- [ ] Add C# xUnit/RestSharp contract tests for API behavior and authentication-negative cases, following the project’s testing plan.
- [ ] Add one Playwright .NET happy path for login or the configured test-auth path, document browsing, and evidence display.
- [ ] Verify major error states, including forbidden, not-found, rate-limited, and waking-up behavior.
- [ ] Run accessibility checks for the principal user flows; manually verify keyboard navigation and screen-reader status announcements.
- [ ] Enforce coverage thresholds from `SPEC.md`: backend >= 80% and frontend >= 70%. Do not reduce thresholds to make CI green.

### M6-2 — Helm and reproducible Kubernetes demo

- [ ] Add Helm resources for the components in the documented full profile. Do not include optional components without a documented need.
- [ ] Add resource requests/limits, probes, secret references, and safe defaults. Do not commit secrets in values files.
- [ ] Add NetworkPolicy resources and tests for the enforcing CNI.
- [ ] Implement `make k8s-demo` to create a clean kind cluster, install the required CNI, install the chart, run proof tests, and clean up.
- [ ] Verify installation from a clean cluster and document prerequisites and expected resource use.
- [ ] Keep plain manifests as the documented fallback if Helm becomes a schedule risk; do not drop the security proof.

**M6 exit gate**

- [ ] Contract and browser tests pass in CI.
- [ ] Coverage and accessibility gates pass.
- [ ] A clean kind cluster can install and run the documented demo; NetworkPolicy proof tests pass.

## M7 — Ship

**Goal:** Make the project reproducible, understandable, and honest about its limitations.

### M7-1 — Documentation and release evidence

- [ ] Update the README with setup, architecture diagram, runtime profiles, commands, public demo link, and synthetic-data policy.
- [ ] Document that the public demo is read-only and lite; explain which components are local/full-profile only.
- [ ] Document known limitations, including English-only NLP, synthetic evaluation, model limitations, provider/free-tier constraints, and cold starts.
- [ ] Complete `docs/course-evidence.md`; every claimed course artifact links to a test, commit, report, ADR, or screenshot.
- [ ] Write/update the runbook for local setup, database reset, seed, migrations, deployment, cold start, and common failures.
- [ ] Record unresolved verification items and legal/privacy caveats. Do not represent unresolved checks as completed.
- [ ] Record a concise three-minute demo showing the implemented flow and its evidence; do not imply unimplemented features are live.
- [ ] Run all release gates from a clean checkout and capture the commit, test results, and deployment verification.

**M7 exit gate**

- [ ] A reviewer can follow the documented local path without private credentials or real data.
- [ ] Documentation matches the shipped implementation and explicitly labels unshipped tiered features.
- [ ] The release has green quality/security gates and no committed secrets or personal data.

## Cross-cutting review checklist

Use this checklist before closing any milestone:

- [ ] **Security:** authorization is checked server-side; tenant isolation is enforced by RLS; input and output are bounded; errors do not disclose internals.
- [ ] **Privacy:** no real personal data, raw files, document text in logs, or unnecessary provider disclosure.
- [ ] **Performance:** work is bounded; list/query paths are paginated and indexed; external calls have timeouts; no unbounded polling or retry loops.
- [ ] **Reliability:** database writes are transactional where required; retries are safe; duplicate events are idempotent; failures are observable without sensitive payloads.
- [ ] **Accessibility:** keyboard and semantic interaction work; focus and status updates are visible to assistive technology.
- [ ] **Evidence:** acceptance criteria have named tests or a reproducible artifact; documentation does not claim unmeasured results.
- [ ] **Scope:** no unapproved database, vector store, service, or runtime dependency was added.

## Deferred / not in the critical path

Do not make these prerequisites for M1–M7 completion unless a decision changes in `SPEC.md` or an ADR:

- DPoP.
- QStash adapter.
- Atlas vector-search experiment.
- Oracle Always Free hosting.
- Mongo profile store; it requires the documented justification/degradation test or an ADR removing it.
- Real resume datasets; synthetic generation is sufficient.
- OCR, Indonesian NLP, automated rejection, extra vector databases, or production-scale infrastructure.

## Close-out log

For each milestone, record in `docs/PROGRESS.md`:

- Date and commit.
- Tasks completed and any deferred/blocked items.
- Commands and test gates run, with results.
- Security, performance, and deployment evidence.
- Decisions made and links to updated documentation.