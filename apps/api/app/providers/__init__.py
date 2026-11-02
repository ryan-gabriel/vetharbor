"""Provider interfaces and adapters (ARCHITECTURE.md §5).

No provider import may happen outside this package (AGENTS.md §8).
Every embedding adapter satisfies the 768-dimension invariant of ADR-005:
the assertion lives at the boundary, before anything reaches SQL.
"""
