"""Public HTTP surface for the rag module (routes arrive with their milestone)."""

from fastapi import APIRouter

router = APIRouter(prefix="/rag", tags=["rag"])
