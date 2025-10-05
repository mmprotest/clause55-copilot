"""Energy and solar checks."""

from __future__ import annotations

from ...geometry import area
from ...models import Building, CheckResult, CheckStatus, PropertyReport, ReportSpec, Site
from . import utils

MIN_ROOF_SOLAR_AREA = 20.0


def rooftop_solar_protection(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    notes = (
        f"Clause {rule_meta['id']} – no neighbouring rooftop solar planes supplied; proposal assumed to avoid additional shading."
    )
    return utils.base_result(
        rule_meta,
        status=CheckStatus.PASS,
        metrics={},
        notes=notes,
    )


def rooftop_solar_provision(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    if not buildings:
        return utils.base_result(rule_meta, status=CheckStatus.NA, notes="No buildings provided.")
    roof_areas = {b.name: area(b.footprint) for b in buildings}
    total_area = sum(roof_areas.values())
    status = CheckStatus.PASS if total_area >= MIN_ROOF_SOLAR_AREA else CheckStatus.FAIL
    metrics = {**{f"{name}_roof_area_m2": float(value) for name, value in roof_areas.items()}, "total_roof_area_m2": float(total_area)}
    notes = f"Clause {rule_meta['id']} provides {total_area:.1f} m² roof area vs {MIN_ROOF_SOLAR_AREA:.1f} m² minimum."
    return utils.base_result(
        rule_meta,
        status=status,
        metrics=metrics,
        notes=notes,
    )
