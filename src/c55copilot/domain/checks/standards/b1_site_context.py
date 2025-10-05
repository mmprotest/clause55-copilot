"""Neighbourhood and site description checks."""

from __future__ import annotations

from statistics import mean

from ...geometry import area
from ...models import Building, CheckResult, CheckStatus, PropertyReport, ReportSpec, Site
from . import utils


def site_description(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    lot_area = area(site.boundary)
    footprint_area = sum(area(b.footprint) for b in buildings) if buildings else 0.0
    coverage_ratio = footprint_area / lot_area if lot_area else 0.0
    avg_height = mean([b.height for b in buildings]) if buildings else 0.0
    metrics = {
        "site_area_m2": float(lot_area),
        "building_coverage_ratio": float(coverage_ratio),
        "average_building_height_m": float(avg_height),
    }
    notes = (
        f"Clause {rule_meta['id']} records {lot_area:.1f} m² site area with {coverage_ratio:.0%} coverage and "
        f"average height {avg_height:.1f} m."
    )
    return utils.base_result(
        rule_meta,
        status=CheckStatus.PASS,
        metrics=metrics,
        notes=notes,
    )
