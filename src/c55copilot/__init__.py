"""Clause55 Copilot package."""

from importlib.metadata import version, PackageNotFoundError

try:  # pragma: no cover - metadata query
    __version__ = version("clause55-copilot")
except PackageNotFoundError:  # pragma: no cover - local dev
    __version__ = "0.1.0"

__all__ = ["__version__"]
