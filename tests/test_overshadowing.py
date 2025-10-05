from datetime import date, time

from datetime import date, time

from c55copilot.domain.models import Building, ReportSpec, Site, SPOS
from c55copilot.domain.overshadowing import aggregate_shadow_metrics, compute_overshadowing


SITE = Site(
    name="Test",
    address="",
    latitude=-37.8,
    longitude=144.97,
    timezone="Australia/Melbourne",
    boundary=[(0, 0), (20, 0), (20, 20), (0, 20), (0, 0)],
    spos=[SPOS(name="Yard", polygon=[(5, 5), (15, 5), (15, 15), (5, 15)])],
)

BUILDINGS = [
    Building(name="House", footprint=[(2, 2), (8, 2), (8, 8), (2, 8)], height=6.0)
]


def test_overshadowing_minimum_sun_hours():
    spec = ReportSpec(analysis_date=date(2024, 9, 22), start_time=time(9), end_time=time(15))
    slices = compute_overshadowing(SITE, BUILDINGS, spec)
    metrics = aggregate_shadow_metrics(slices, SITE)
    assert metrics["Yard"]["min_continuous_sun_hours"] >= 2.0
    first_slice = slices[0]
    assert "Yard" in first_slice.spos_sunlit
