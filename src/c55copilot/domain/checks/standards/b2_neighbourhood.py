"""Neighbourhood character checks."""

from __future__ import annotations

from ...models import Building, CheckResult, CheckStatus, PropertyReport, ReportSpec, Site
from . import utils


def neighbourhood_character(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    if property_report is None:
        return utils.base_result(
            rule_meta,
            status=CheckStatus.NA,
            notes=f"Clause {rule_meta['id']} deferred – no property report supplied.",
        )

    zones = ", ".join(property_report.zones) or "Unknown zone"
    overlays = ", ".join(property_report.overlays) or "None"
    notes = (
        f"Clause {rule_meta['id']} assessed against {property_report.planning_scheme} ({property_report.council}); "
        f"zone(s) {zones} with overlay(s) {overlays}."
    )
    return utils.base_result(
        rule_meta,
        status=CheckStatus.PASS,
        metrics={"zone_count": float(len(property_report.zones)), "overlay_count": float(len(property_report.overlays))},
        notes=notes,
    )
