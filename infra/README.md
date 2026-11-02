# infra — compose, helm, kind [T1 + T2]

`compose/dev.yaml`: M0 task 2 — Postgres 16 + pgvector on port 55432, matching
`Settings.database_url` in `apps/api`. Ollama and Keycloak join in M4 and M3
when their code paths exist, so the zero-key start stays small.

`helm/` + `kind/`: [T2] (M3 NetworkPolicy proofs with Calico, M6 chart). Plain
manifests are the cut-order fallback for Helm (SPEC.md §13).
