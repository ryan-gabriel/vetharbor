"""Vetharbor API package.

Module map and dependency direction are fixed by docs/ARCHITECTURE.md §3:
``gateway/auth -> feature modules -> persistence``. A module may import another
module's public service interface only - never its models or repositories.
"""
