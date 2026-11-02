"""Public HTTP surface for the auth module (routes arrive with their milestone)."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
