"""Minimal FastAPI-compatible stubs for offline execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class FileInfo:
    default: Any


@dataclass
class FormInfo:
    default: Any


def File(default: Any) -> FileInfo:
    return FileInfo(default=default)


def Form(default: Any) -> FormInfo:
    return FormInfo(default=default)


class UploadFile:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


@dataclass
class Route:
    method: str
    path: str
    handler: Callable[..., Awaitable[Any] | Any]


class APIRouter:
    def __init__(self) -> None:
        self.routes: List[Route] = []

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("GET", path)

    def post(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("POST", path)

    def _register(self, method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(Route(method=method, path=path, handler=func))
            return func

        return decorator


class FastAPI:
    def __init__(self, title: str, version: str) -> None:
        self.title = title
        self.version = version
        self.routes: List[Route] = []
        self.middleware = []

    def include_router(self, router: APIRouter) -> None:
        self.routes.extend(router.routes)

    def add_middleware(self, middleware_class: Any, **kwargs: Any) -> None:  # pragma: no cover
        self.middleware.append((middleware_class, kwargs))


__all__ = [
    "APIRouter",
    "FastAPI",
    "File",
    "FileInfo",
    "Form",
    "FormInfo",
    "HTTPException",
    "Route",
    "UploadFile",
]

