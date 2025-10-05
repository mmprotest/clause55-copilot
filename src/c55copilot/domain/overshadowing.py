"""Shadow modelling utilities built on top of shapely."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import math
from zoneinfo import ZoneInfo

from .geometry import (
    HAS_SHAPELY,
    area,
    bounds,
    convex_hull,
    point_in_polygon,
    to_polygon,
    translate,
)

if HAS_SHAPELY:  # pragma: no cover - optional dependency
    from shapely import affinity
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
else:  # pragma: no cover - fallback
    Polygon = None  # type: ignore
from .models import Building, ReportSpec, Site
from .solar import solar_position


@dataclass(slots=True)
class RasterShadow:
    polygons: List[List[Tuple[float, float]]]
    resolution: float


@dataclass(slots=True)
class ShadowSlice:
    timestamp: datetime
    altitude: float
    azimuth: float
    combined_shadow: Any
    spos_sunlit: Dict[str, float]
    spos_shadow: Dict[str, float]
    resolution: float


def compute_overshadowing(site: Site, buildings: Iterable[Building], spec: ReportSpec) -> List[ShadowSlice]:
    zone = ZoneInfo(site.timezone)
    start_dt = datetime.combine(spec.analysis_date, spec.start_time, tzinfo=zone)
    end_dt = datetime.combine(spec.analysis_date, spec.end_time, tzinfo=zone)

    building_list = list(buildings)
    if HAS_SHAPELY:
        building_polys = [to_polygon(b.footprint) for b in building_list]
    else:
        building_polys = [list(b.footprint) for b in building_list]
    slices: List[ShadowSlice] = []

    dt = start_dt
    while dt <= end_dt:
        altitude, azimuth = solar_position(site.latitude, site.longitude, dt)
        if altitude <= 0:
            shadow_geom = _merge_polygons(building_polys, spec.shadow_resolution)
        else:
            building_shadows = [
                _shadow_polygon(poly, building.height, altitude, azimuth)
                for poly, building in zip(building_polys, building_list)
            ]
            shadow_geom = _merge_polygons(building_shadows, spec.shadow_resolution)

        spos_sunlit: Dict[str, float] = {}
        spos_shadow: Dict[str, float] = {}
        for spos in site.spos:
            total = area(spos.polygon)
            shadow = _shadow_intersection_area(
                shadow_geom,
                spos.polygon,
                spec.shadow_resolution,
            )
            spos_shadow[spos.name] = shadow
            spos_sunlit[spos.name] = max(total - shadow, 0.0)

        slices.append(
            ShadowSlice(
                timestamp=dt,
                altitude=altitude,
                azimuth=azimuth,
                combined_shadow=shadow_geom,
                spos_sunlit=spos_sunlit,
                spos_shadow=spos_shadow,
                resolution=spec.shadow_resolution,
            )
        )
        dt += timedelta(minutes=spec.time_step_minutes)
    return slices


def _shadow_polygon(footprint: Any, height: float, altitude: float, azimuth: float):
    alt_rad = math.radians(max(altitude, 1e-3))
    length = height / math.tan(alt_rad)
    az_rad = math.radians(azimuth)
    dx = -length * math.sin(az_rad)
    dy = -length * math.cos(az_rad)
    if HAS_SHAPELY:
        translated = affinity.translate(footprint, xoff=dx, yoff=dy)
        return unary_union([footprint, translated]).convex_hull
    translated = translate(footprint, dx, dy)
    hull_points = [tuple(pt) for pt in footprint] + [tuple(pt) for pt in translated]
    return convex_hull(hull_points)


def minimum_continuous_sun_hours(slices: List[ShadowSlice], site: Site, threshold_ratio: float = 0.75) -> Dict[str, float]:
    if not slices:
        return {spos.name: 0.0 for spos in site.spos}

    step_seconds = (
        (slices[1].timestamp - slices[0].timestamp).total_seconds() if len(slices) > 1 else 3600
    )
    step_hours = step_seconds / 3600

    results: Dict[str, float] = {spos.name: 0.0 for spos in site.spos}
    for spos in site.spos:
        total = area(spos.polygon)
        best_run = current = 0
        for slice_ in slices:
            sunlit = slice_.spos_sunlit.get(spos.name, 0.0)
            ratio = sunlit / total if total else 0.0
            if ratio >= threshold_ratio:
                current += 1
            else:
                best_run = max(best_run, current)
                current = 0
        best_run = max(best_run, current)
        results[spos.name] = best_run * step_hours
    return results


def aggregate_shadow_metrics(slices: List[ShadowSlice], site: Site) -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}
    sun_hours = minimum_continuous_sun_hours(slices, site)
    for spos in site.spos:
        data: Dict[str, float] = {
            "area": area(spos.polygon),
            "min_continuous_sun_hours": sun_hours.get(spos.name, 0.0),
        }
        for slice_ in slices:
            key = f"sunlit_{slice_.timestamp.strftime('%H%M')}"
            data[key] = slice_.spos_sunlit.get(spos.name, 0.0)
        metrics[spos.name] = data
    return metrics


def total_shadow_area(slices: List[ShadowSlice]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for slice_ in slices:
        totals[slice_.timestamp.strftime("%H:%M")] = _shadow_area(
            slice_.combined_shadow, slice_.resolution
        )
    return totals


def _merge_polygons(polygons: List[Any], resolution: float):
    if not polygons:
        if HAS_SHAPELY:
            return Polygon()
        return RasterShadow([], resolution)
    if HAS_SHAPELY:
        return unary_union(polygons)
    polygons_list = [list(poly) for poly in polygons if poly]
    return RasterShadow(polygons_list, resolution)


def _shadow_intersection_area(
    shadow_geom: Any, polygon: Sequence[tuple[float, float]], resolution: float
) -> float:
    if HAS_SHAPELY:
        spos_poly = Polygon(polygon)
        return float(shadow_geom.intersection(spos_poly).area)
    if isinstance(shadow_geom, RasterShadow):
        return _raster_intersection_area(shadow_geom, polygon)
    if not shadow_geom:
        return 0.0
    return 0.0


def _shadow_area(shadow_geom: Any, resolution: float) -> float:
    if HAS_SHAPELY:
        return float(shadow_geom.area)
    if isinstance(shadow_geom, RasterShadow):
        return _raster_area(shadow_geom)
    if not shadow_geom:
        return 0.0
    return 0.0


def _raster_intersection_area(shadow: RasterShadow, polygon: Sequence[Tuple[float, float]]) -> float:
    if not shadow.polygons:
        return 0.0

    res = shadow.resolution
    if res <= 0:
        return 0.0

    min_x, min_y, max_x, max_y = bounds([polygon])
    total = 0.0
    y = min_y
    while y < max_y:
        x = min_x
        while x < max_x:
            cx = x + res / 2
            cy = y + res / 2
            if point_in_polygon((cx, cy), polygon):
                if any(point_in_polygon((cx, cy), poly) for poly in shadow.polygons):
                    total += res * res
            x += res
        y += res
    max_area = area(polygon)
    return min(total, max_area)


def _raster_area(shadow: RasterShadow) -> float:
    if not shadow.polygons:
        return 0.0
    res = shadow.resolution
    if res <= 0:
        return 0.0
    min_x, min_y, max_x, max_y = bounds(shadow.polygons)
    total = 0.0
    y = min_y
    while y < max_y:
        x = min_x
        while x < max_x:
            cx = x + res / 2
            cy = y + res / 2
            if any(point_in_polygon((cx, cy), poly) for poly in shadow.polygons):
                total += res * res
            x += res
        y += res
    return total

