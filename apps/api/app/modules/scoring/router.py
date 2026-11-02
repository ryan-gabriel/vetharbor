"""Public HTTP surface for the scoring module (routes arrive with their milestone)."""

from fastapi import APIRouter

router = APIRouter(prefix="/scores", tags=["scores"])
