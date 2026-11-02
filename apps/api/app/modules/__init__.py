"""Feature modules (docs/ARCHITECTURE.md §3).

A module owns router/service/schemas; it imports its own repositories and
another module's public service interface - never another module's models.
"""
