# ml — spaCy rules, gazetteer, features, training, registry, drift [T1]

Layout (SPEC.md §7 FR-3xx/6xx, docs/ARCHITECTURE.md §14):
rules/ (EntityRuler + Matcher patterns), gazetteer/ (ESCO/O*NET subset),
features/, training/, registry/ (file-based; .bin artifacts git-ignored), drift/ (PSI fixtures).
Embeddings in every profile are 768-dimensional (ADR-005). Synthetic data only (ADR-010).
