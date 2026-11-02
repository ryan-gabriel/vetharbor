# Threat model v0 — Vetharbor

Status: v0, M0. Living document; revisited at M3 (identity/zero-trust) and M4 (guardrails).

## Scope

Synthetic-document screening platform: upload → extraction → NLP entities → role-match
score → (M4) retrieval Q&A. Public demo is seeded and read-only (ADR-009, ADR-010).
No real candidate data ever reaches a third-party LLM.

## Trust boundaries

1. Browser ↔ API (HTTPS, OIDC bearer token, public demo is unauthenticated read-only).
2. API ↔ Postgres (SQL over TLS, RLS session variables set per transaction).
3. API ↔ LLM/embedding provider (synthetic text only, behind provider interfaces).
4. API ↔ Spring orchestrator [T2] (token exchange, network policy).
5. Outbox events stay inside Postgres; no external broker.

## STRIDE summary

| Threat | Mitigation | Status |
| --- | --- | --- |
| Spoofing (identity) | OIDC JWKS verification, `sub`-only tokens, `org_memberships` resolution (ADR-006) | M3 |
| Tampering (tenant data) | RLS `FORCE` on every tenant table; tenant resolved server-side | M1 |
| Repudiation | Append-only `audit_log`, correlation ids end to end | M1/M2 |
| Information disclosure (cross-tenant) | F7 integration test; transaction-local `set_config(..., true)` | M1 |
| Information disclosure (LLM leakage) | Canary in prompts, PII output filter, synthetic-only input | M4 |
| Denial of service (Render free) | One service, no pollers, on-demand drain, no keep-alive pings | M0 |
| Elevation of privilege | RBAC via memberships, no client-supplied `org_id` | M3 |

## OWASP LLM Top 10 mapping (M4 deliverable, v0 stub)

| OWASP LLM | Risk in Vetharbor | Control |
| --- | --- | --- |
| LLM01 Prompt injection | Document text treated as instructions | Injection filter, canary, refusal state `blocked_injection`, CI block rate ≥ 95 % |
| LLM02 Insecure output handling | PII or secrets in answers | PII output filter, redacted chips in UI |
| LLM06 Sensitive info disclosure | Real CV data sent to Gemini | Synthetic-only, provider interfaces, no real data (ADR-010) |
| LLM08 Excessive agency | Auto-decisions on candidates | Advisory only, no reject/disqualify path (AGENTS.md §3.3) |

## Out of scope for v0

- Kubernetes NetworkPolicy proofs ([T2], M3/M6).
- Fairness audit and drift (M5).
- Full STRIDE per-component diagrams (deferred to the runbook).