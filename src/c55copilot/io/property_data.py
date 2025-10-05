"""Property data adapters."""

from __future__ import annotations

import json
from pathlib import Path

from ..domain.models import PropertyReport


def fetch_vicplan(address: str) -> PropertyReport:
    """Stubbed VicPlan adapter returning a minimal property report."""

    return PropertyReport(
        address=address,
        planning_scheme="Victorian Planning Provisions",
        council="City of Example",
        zones=["GRZ1"],
        overlays=["DDO1"],
        citations=["VicPlan mock dataset"],
    )


def load_property_report_mock(path: Path | str) -> PropertyReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return PropertyReport.model_validate(data)
