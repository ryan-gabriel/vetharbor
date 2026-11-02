"""Public HTTP surface for the upload module (routes arrive with their milestone)."""

from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])
