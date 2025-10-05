import pytest

from c55copilot.domain import geometry
from c55copilot.domain.models import Opening


def test_offset_polygon_grows_area():
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    buffered = geometry.offset_polygon(square, 1.0)
    assert geometry.area(buffered) > geometry.area(square)


def test_line_of_sight_distance():
    opening = Opening(name="Test", sill_height=1.0, head_height=2.4, centre=(5.0, 5.0), orientation=0)
    polygon = [(5, 20), (15, 20), (15, 22), (5, 22)]
    distance = geometry.line_of_sight(opening, polygon)
    assert distance == pytest.approx(15.0, rel=0.1)


def test_project_points_to_utm():
    coords = [(144.96, -37.81)]
    projected = geometry.project_points(coords, lat_lon_hint=(-37.81, 144.96))
    assert len(projected) == 1
    x, y = projected[0]
    assert x != coords[0][0] and y != coords[0][1]
