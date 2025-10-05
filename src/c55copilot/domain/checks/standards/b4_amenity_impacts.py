"""Amenity impact checks."""

from __future__ import annotations

import math
from typing import Sequence

from ...geometry import HAS_SHAPELY, line_of_sight, to_polygon
from ...models import Building, CheckResult, CheckStatus, PropertyReport, ReportSpec, Site
from . import utils

SIDE_SETBACK_BASE = 1.0
SIDE_SETBACK_RATE = 0.3
OVERLOOKING_DISTANCE = 9.0
BOUNDARY_MAX_RATIO = 0.33


def side_and_rear_setbacks(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    if not buildings:
        return utils.base_result(rule_meta, status=CheckStatus.NA, notes="No buildings to assess.")

    if HAS_SHAPELY:
        site_poly = to_polygon(site.boundary)
        min_setback = min(site_poly.boundary.distance(to_polygon(b.footprint)) for b in buildings)
    else:
        min_setback = min(_min_setback_manual(site.boundary, b.footprint) for b in buildings)
    max_height = max(b.height for b in buildings)
    requirement = SIDE_SETBACK_BASE + SIDE_SETBACK_RATE * max_height
    status = CheckStatus.PASS if min_setback >= requirement else CheckStatus.FAIL
    notes = (
        f"Clause {rule_meta['id']} minimum setback {min_setback:.1f} m compared to {requirement:.1f} m requirement."
    )
    return utils.base_result(
        rule_meta,
        status=status,
        metrics={"min_setback_m": float(min_setback), "required_m": float(requirement)},
        notes=notes,
    )


def walls_on_boundaries(
    *,
    site: Site,
    buildings: list[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
    rule_meta: dict,
) -> CheckResult:
    if not buildings:
        return utils.base_result(rule_meta, status=CheckStatus.NA, notes="No buildings to assess.")

    if HAS_SHAPELY:
        site_poly = to_polygon(site.boundary)
        boundary_length = site_poly.length
        contact_length = 0.0
        for building in buildings:
            footprint = to_polygon(building.footprint)
            intersection = footprint.boundary.intersection(site_poly.boundary)
            contact_length += float(intersection.length)
    else:
        boundary_length = _perimeter(site.boundary)
        contact_length = 0.0
        sx1, sy1, sx2, sy2 = _bbox(site.boundary)
        for building in buildings:
            bx1, by1, bx2, by2 = _bbox(building.footprint)
            if abs(bx1 - sx1) < 1e-6:
                contact_length += max(0.0, min(by2, sy2) - max(by1, sy1))
            if abs(bx2 - sx2) < 1e-6:
                contact_length += max(0.0, min(by2, sy2) - max(by1, sy1))
            if abs(by1 - sy1) < 1e-6:
                contact_length += max(0.0, min(bx2, sx2) - max(bx1, sx1))
            if abs(by2 - sy2) < 1e-6:
                contact_length += max(0.0, min(bx2, sx2) - max(bx1, sx1))
    ratio = contact_length / boundary_length if boundary_length else 0.0
    status = CheckStatus.PASS if ratio <= BOUNDARY_MAX_RATIO else CheckStatus.FAIL
    notes = f"Clause {rule_meta['id']} boundary wall ratio {ratio:.2f} vs limit {BOUNDARY_MAX_RATIO:.2f}."
    return utils.base_result(
        rule_meta,
        status=status,
        metrics={"boundary_contact_ratio": float(ratio)},
        notes=notes,
    )


def overlooking_to_spos(
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
            notes=f"Clause {rule_meta['id']} not assessed – no SPOS defined.",
        )
    min_distance = float("inf")
    for building in buildings:
        for opening in building.openings:
            if opening.head_height < 1.7:
                continue
            for spos in site.spos:
                distance = line_of_sight(opening, spos.polygon)
                min_distance = min(min_distance, distance)
    if math.isinf(min_distance):
        return utils.base_result(
            rule_meta,
            status=CheckStatus.NA,
            notes=f"Clause {rule_meta['id']} no elevated habitable openings provided.",
        )
    status = CheckStatus.PASS if min_distance >= OVERLOOKING_DISTANCE else CheckStatus.FAIL
    notes = (
        f"Clause {rule_meta['id']} minimum overlooking distance {min_distance:.1f} m compared to {OVERLOOKING_DISTANCE:.1f} m requirement."
    )
    return utils.base_result(
        rule_meta,
        status=status,
        metrics={"min_overlooking_distance_m": float(min_distance)},
        notes=notes,
    )


def _bbox(coords: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _perimeter(coords: Sequence[tuple[float, float]]) -> float:
    total = 0.0
    points = list(coords)
    if points[0] != points[-1]:
        points.append(points[0])
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def _min_setback_manual(site_boundary: Sequence[tuple[float, float]], footprint: Sequence[tuple[float, float]]) -> float:
    sx1, sy1, sx2, sy2 = _bbox(site_boundary)
    bx1, by1, bx2, by2 = _bbox(footprint)
    distances = [bx1 - sx1, by1 - sy1, sx2 - bx2, sy2 - by2]
    return max(0.0, min(distances))
