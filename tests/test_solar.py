from datetime import datetime
from datetime import datetime
from zoneinfo import ZoneInfo

from c55copilot.domain.solar import solar_position


def test_solar_position_melbourne_equinox():
    dt = datetime(2024, 9, 22, 12, 0, tzinfo=ZoneInfo("Australia/Melbourne"))
    altitude, azimuth = solar_position(-37.81, 144.96, dt)
    assert 45 < altitude < 60
    assert 0 <= azimuth <= 360
