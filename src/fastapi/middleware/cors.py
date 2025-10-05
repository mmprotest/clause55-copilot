"""Stub CORS middleware."""

from __future__ import annotations


class CORSMiddleware:  # pragma: no cover - placeholder
    def __init__(self, app, **kwargs):
        self.app = app
        self.kwargs = kwargs

