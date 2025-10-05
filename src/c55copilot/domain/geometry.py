"""Geometry utilities with optional shapely support."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

from .models import Opening

Coordinate = Tuple[float, float]

try:  # pragma: no cover - optional dependency
    from shapely import affinity
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union

    HAS_SHAPELY = True
except Exception:  # pragma: no cover - fallback
    HAS_SHAPELY = False
    Polygon = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from pyproj import CRS, Transformer

    HAS_PYPROJ = True
except Exception:  # pragma: no cover - fallback
    HAS_PYPROJ = False


def to_polygon(coords: Sequence[Coordinate]):
    if HAS_SHAPELY:
        return Polygon(coords)
    return list(coords)


def area(coords: Sequence[Coordinate]) -> float:
    if HAS_SHAPELY:
        return float(Polygon(coords).area)
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in _pairwise_closed(coords))) / 2.0


def perimeter(coords: Sequence[Coordinate]) -> float:
    if HAS_SHAPELY:
        return float(Polygon(coords).length)
    return sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in _pairwise_closed(coords))


def offset_polygon(coords: Sequence[Coordinate], distance: float) -> List[Coordinate]:
    if HAS_SHAPELY:
        geom = Polygon(coords)
        buffered = geom.buffer(distance, join_style=2)
        if buffered.is_empty:
            return list(coords)
        return list(zip(buffered.exterior.coords.xy[0], buffered.exterior.coords.xy[1]))
    min_x = min(x for x, _ in coords) - distance
    max_x = max(x for x, _ in coords) + distance
    min_y = min(y for _, y in coords) - distance
    max_y = max(y for _, y in coords) + distance
    return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]


def distance_point_to_polygon(point: Coordinate, polygon: Sequence[Coordinate]) -> float:
    if HAS_SHAPELY:
        return float(Point(point).distance(Polygon(polygon)))
    x, y = point
    min_dist = float("inf")
    for (x0, y0), (x1, y1) in _pairwise_closed(polygon):
        min_dist = min(min_dist, _distance_point_to_segment(x, y, x0, y0, x1, y1))
    return min_dist


def line_of_sight(opening: Opening, boundary: Sequence[Coordinate], max_distance: float = 200.0) -> float:
    ox, oy = opening.centre
    az_rad = math.radians(opening.orientation)
    dx = math.sin(az_rad)
    dy = math.cos(az_rad)
    best = max_distance
    for (x0, y0), (x1, y1) in _pairwise_closed(boundary):
        denom = (dx * (y1 - y0)) - (dy * (x1 - x0))
        if abs(denom) < 1e-9:
            continue
        t = ((x0 - ox) * (y1 - y0) - (y0 - oy) * (x1 - x0)) / denom
        u = ((x0 - ox) * dy - (y0 - oy) * dx) / denom
        if t > 0 and 0 <= u <= 1:
            distance = math.hypot(dx * t, dy * t)
            if distance < best:
                best = distance
    return best


def project_points(
    coords: Sequence[Coordinate],
    *,
    source_epsg: int = 4326,
    target_epsg: int | None = None,
    lat_lon_hint: Coordinate | None = None,
) -> List[Coordinate]:
    if HAS_PYPROJ:
        if target_epsg is None:
            if lat_lon_hint is None:
                raise ValueError("lat_lon_hint is required when target_epsg is not provided")
            target_epsg = _utm_epsg(lat_lon_hint[0], lat_lon_hint[1])
        transformer = Transformer.from_crs(CRS.from_epsg(source_epsg), CRS.from_epsg(target_epsg), always_xy=True)
        xs, ys = zip(*coords)
        projected_x, projected_y = transformer.transform(xs, ys)
        return list(zip(projected_x, projected_y))
    base_lat = lat_lon_hint[0] if lat_lon_hint else coords[0][1]
    base_lon = lat_lon_hint[1] if lat_lon_hint else coords[0][0]
    scale_x = math.cos(math.radians(base_lat)) * 111320
    scale_y = 110540
    projected: List[Coordinate] = []
    for lon, lat in coords:
        x = (lon - base_lon) * scale_x
        y = (lat - base_lat) * scale_y
        projected.append((x, y))
    return projected


def translate(coords: Sequence[Coordinate], dx: float, dy: float) -> List[Coordinate]:
    if HAS_SHAPELY:
        shifted = affinity.translate(Polygon(coords), xoff=dx, yoff=dy)
        return list(zip(shifted.exterior.coords.xy[0], shifted.exterior.coords.xy[1]))
    return [(x + dx, y + dy) for x, y in coords]


def convex_hull(coords: Sequence[Coordinate]):
    """Return the convex hull of the supplied coordinates."""

    if HAS_SHAPELY:
        return Polygon(coords).convex_hull

    points = sorted(set(tuple(pt) for pt in coords))
    if len(points) <= 1:
        return list(points)

    def _cross(o: Coordinate, a: Coordinate, b: Coordinate) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Coordinate] = []
    for p in points:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: List[Coordinate] = []
    for p in reversed(points):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    hull = lower[:-1] + upper[:-1]
    return hull


def union_area(polygons: Iterable[Sequence[Coordinate]]) -> float:
    if HAS_SHAPELY:
        geoms = [Polygon(poly) for poly in polygons]
        if not geoms:
            return 0.0
        return float(unary_union(geoms).area)
    total = 0.0
    polys = list(polygons)
    for poly in polys:
        total += area(poly)
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            total -= intersection_area(polys[i], polys[j])
    return max(total, 0.0)


def intersection_area(a: Sequence[Coordinate], b: Sequence[Coordinate]) -> float:
    if HAS_SHAPELY:
        return float(Polygon(a).intersection(Polygon(b)).area)
    ax1, ay1, ax2, ay2 = _bbox(a)
    bx1, by1, bx2, by2 = _bbox(b)
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _utm_epsg(lat: float, lon: float) -> int:
    zone = int((lon + 180) / 6) + 1
    is_northern = lat >= 0
    return 32600 + zone if is_northern else 32700 + zone


def _bbox(coords: Sequence[Coordinate]) -> Tuple[float, float, float, float]:
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _pairwise_closed(coords: Sequence[Coordinate]):
    points = list(coords)
    if points[0] != points[-1]:
        points.append(points[0])
    return zip(points[:-1], points[1:])


def _distance_point_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    dy = y2 - y1
    if dx == dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def point_in_polygon(point: Coordinate, polygon: Sequence[Coordinate]) -> bool:
    """Ray-casting point-in-polygon test."""

    if HAS_SHAPELY:
        pt = Point(point)
        poly = Polygon(polygon)
        return bool(poly.contains(pt) or poly.touches(pt))

    x, y = point
    inside = False
    points = list(polygon)
    if not points:
        return False
    if points[0] != points[-1]:
        points.append(points[0])
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        on_boundary = _distance_point_to_segment(x, y, x0, y0, x1, y1) < 1e-9
        if on_boundary:
            return True
        intersects = ((y0 > y) != (y1 > y)) and (
            x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-12) + x0
        )
        if intersects:
            inside = not inside
    return inside


def bounds(polygons: Iterable[Sequence[Coordinate]]) -> Tuple[float, float, float, float]:
    xs: List[float] = []
    ys: List[float] = []
    for poly in polygons:
        xs.extend(x for x, _ in poly)
        ys.extend(y for _, y in poly)
    if not xs or not ys:
        return 0.0, 0.0, 0.0, 0.0
    return min(xs), min(ys), max(xs), max(ys)

