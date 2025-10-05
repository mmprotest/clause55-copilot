"""High level orchestration for Clause 55 assessments."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .config import settings, telemetry
from .domain.checks.clause55 import run_clause55_checks
from .domain.models import Building, CheckResult, PropertyReport, ReportSpec, Site
from .domain.overshadowing import compute_overshadowing
from .io.exporters import export_report_pack


def run_analysis(
    *,
    site: Site,
    buildings: Iterable[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    output_dir: Path | None = None,
    license_key: str | None = None,
) -> Dict[str, object]:
    building_list = list(buildings)
    results: List[CheckResult] = run_clause55_checks(
        site=site,
        buildings=building_list,
        property_report=property_report,
        spec=spec,
    )
    slices = compute_overshadowing(site, building_list, spec)

    target_dir = output_dir or (settings.storage_dir / site.name.replace(" ", "_"))
    target_dir.mkdir(parents=True, exist_ok=True)

    pack_paths = export_report_pack(
        site=site,
        buildings=building_list,
        property_report=property_report,
        results=results,
        slices=slices,
        spec=spec,
        output_dir=target_dir,
        license_key=license_key or settings.license_key,
    )

    if telemetry:
        telemetry.increment("runs")

    summary = {
        "results": [result.model_dump() for result in results],
        "outputs": {
            key: str(value) if not isinstance(value, list) else [str(item) for item in value]
            for key, value in pack_paths.items()
        },
    }
    return summary

