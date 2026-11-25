"""Vercel entry point: the same FastAPI application as `python run.py`, run as a Python function.

The React build is served by Vercel's CDN; /api, /health and /docs are rewritten here (vercel.json).
"""
from backend.main import app

__all__ = ["app"]
