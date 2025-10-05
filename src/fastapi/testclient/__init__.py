"""Test client shim for the local FastAPI stub."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Dict, Optional

from .. import APIRouter, FastAPI, FileInfo, FormInfo, HTTPException, Route, UploadFile


class Response:
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        return self._data


class TestClient:
    __test__ = False

    def __init__(self, app: FastAPI):
        self.app = app

    def get(self, path: str) -> Response:
        return self._call("GET", path, files=None, data=None)

    def post(
        self,
        path: str,
        *,
        files: Optional[Dict[str, tuple]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Response:
        return self._call("POST", path, files=files or {}, data=data or {})

    def _call(
        self,
        method: str,
        path: str,
        *,
        files: Optional[Dict[str, tuple]],
        data: Optional[Dict[str, Any]],
    ) -> Response:
        route = self._find_route(method, path)
        if not route:
            return Response(404, {"detail": "Not found"})
        kwargs: Dict[str, Any] = {}
        sig = inspect.signature(route.handler)
        for name, param in sig.parameters.items():
            default = param.default
            if isinstance(default, FileInfo):
                if not files or name not in files:
                    if default.default is None:
                        kwargs[name] = None
                        continue
                    raise RuntimeError(f"Missing file for parameter {name}")
                filename, content, *_ = files[name]
                content_bytes = content.encode("utf-8") if isinstance(content, str) else content
                kwargs[name] = UploadFile(filename, content_bytes)
            elif isinstance(default, FormInfo):
                value = data.get(name, default.default)
                if isinstance(default.default, bool):
                    value = str(value).lower() in {"true", "1", "yes", "on"}
                kwargs[name] = value
            else:
                if data and name in data:
                    kwargs[name] = data[name]
                elif default is not inspect._empty:
                    kwargs[name] = default
                else:
                    kwargs[name] = None
        try:
            result = route.handler(**kwargs)
            if inspect.iscoroutine(result):
                result = asyncio.run(result)
            status = 200
        except HTTPException as exc:  # pragma: no cover - error path
            result = {"detail": exc.detail}
            status = exc.status_code
        return Response(status, result)

    def _find_route(self, method: str, path: str) -> Optional[Route]:
        for route in self.app.routes:
            if route.method == method and route.path == path:
                return route
        return None


__all__ = ["Response", "TestClient"]

