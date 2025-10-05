"""Solar access and daylight checks."""

from __future__ import annotations

import math
from typing import Dict

from ...geometry import distance_point_to_polygon
from ...models import Building, CheckResult, CheckStatus, PropertyReport, ReportSpec, Site
from ...overshadowing import aggregate_shadow_metrics, compute_overshadowing
from . import utils

MIN_SUN_HOURS = 3.0
MIN_DAYLIGHT_SEPARATION = 3.0


def solar_access(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    if not site.spos:
        return utils.base_result(
            rule_meta,
            status=CheckStatus.NA,
            notes=f"Clause {rule_meta['id']} not assessed – SPOS not defined.",
        )

    slices = compute_overshadowing(site, buildings, spec)
    metrics_by_spos = aggregate_shadow_metrics(slices, site)
    worst = min((data["min_continuous_sun_hours"] for data in metrics_by_spos.values()), default=0.0)
    status = CheckStatus.PASS if worst >= MIN_SUN_HOURS else CheckStatus.FAIL
    metrics: Dict[str, float] = {}
    for name, data in metrics_by_spos.items():
        for key, value in data.items():
            metrics[f"{name}_{key}"] = float(value)
    notes = (
        f"Clause {rule_meta['id']} minimum continuous sunlight {worst:.1f} h on 22 September (9am–3pm)."
        if metrics_by_spos
        else f"Clause {rule_meta['id']} no SPOS available for assessment."
    )
    figure_refs = [f"figures/{slice_.timestamp.strftime('%H')}.png" for slice_ in slices]
    return utils.base_result(
        rule_meta,
        status=status,
        metrics=metrics,
        notes=notes,
        figures=figure_refs,
    )


def daylight_to_habitable_rooms(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    if not buildings:
        return utils.base_result(
            rule_meta,
            status=CheckStatus.NA,
            notes=f"Clause {rule_meta['id']} not assessed – no buildings provided.",
        )
    min_distance = float("inf")
    for building in buildings:
        for opening in building.openings:
            if opening.head_height < 1.8:
                continue
            distance = distance_point_to_polygon(opening.centre, site.boundary)
            min_distance = min(min_distance, distance)
    if math.isinf(min_distance):
        return utils.base_result(
            rule_meta,
            status=CheckStatus.NA,
            notes=f"Clause {rule_meta['id']} no qualifying habitable openings provided.",
        )
    status = CheckStatus.PASS if min_distance >= MIN_DAYLIGHT_SEPARATION else CheckStatus.FAIL
    notes = (
        f"Clause {rule_meta['id']} daylight separation {min_distance:.1f} m vs {MIN_DAYLIGHT_SEPARATION:.1f} m benchmark."
    )
    return utils.base_result(
        rule_meta,
        status=status,
        metrics={"min_separation_m": float(min_distance)},
        notes=notes,
    )
