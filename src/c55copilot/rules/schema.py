"""Schema utilities for rules definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Rule:
    id: str
    title: str
    handler: str
    citations: List[str]
