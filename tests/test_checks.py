from datetime import date

from c55copilot.domain.checks.standards import b4_amenity_impacts
from c55copilot.domain.checks.standards import b4_amenity_impacts
from c55copilot.domain.models import Building, Opening, ReportSpec, Site, SPOS

SITE = Site(
    name="Lot",
    address="",
    latitude=-37.8,
    longitude=144.97,
    timezone="Australia/Melbourne",
    boundary=[(0, 0), (20, 0), (20, 20), (0, 20)],
    spos=[SPOS(name="Yard", polygon=[(5, 5), (15, 5), (15, 15), (5, 15)])],
)

SPEC = ReportSpec.default()


def test_side_setback_passes():
    building = Building(name="House", footprint=[(3, 3), (9, 3), (9, 9), (3, 9)], height=6.0)
    result = b4_amenity_impacts.side_and_rear_setbacks(
        site=SITE,
        buildings=[building],
        property_report=None,
        spec=SPEC,
        rule_meta={"id": "55.04-1", "title": "Setbacks", "citations": []},
    )
    assert result.status.value == "PASS"


def test_overlooking_fails_when_close():
    building = Building(
        name="House",
        footprint=[(3, 3), (9, 3), (9, 9), (3, 9)],
        height=6.0,
        openings=[
            Opening(
                name="Upper",
                sill_height=1.2,
                head_height=2.4,
                centre=(6.0, 9.0),
                orientation=0,
            )
        ],
    )
    result = b4_amenity_impacts.overlooking_to_spos(
        site=SITE,
        buildings=[building],
        property_report=None,
        spec=SPEC,
        rule_meta={"id": "55.04-6", "title": "Overlooking", "citations": []},
    )
    assert result.status.value in {"FAIL", "N/A"}
