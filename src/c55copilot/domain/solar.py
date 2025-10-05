"""Solar position calculations."""

from __future__ import annotations

from datetime import datetime, timezone
from math import atan2, cos, degrees, radians, sin, sqrt
from typing import Tuple

try:  # pragma: no cover - optional dependency
    from pysolar.solar import get_altitude, get_azimuth
except Exception:  # pragma: no cover - fallback
    get_altitude = None
    get_azimuth = None


def solar_position(lat: float, lon: float, dt: datetime) -> Tuple[float, float]:
    """Return solar altitude and azimuth in degrees."""

    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")

    if get_altitude and get_azimuth:
        altitude = float(get_altitude(lat, lon, dt))
        azimuth = float(get_azimuth(lat, lon, dt))
        return altitude, (azimuth + 360.0) % 360.0

    # NOAA SPA simplified formula
    dt_utc = dt.astimezone(timezone.utc)
    n = dt_utc.timetuple().tm_yday
    hour = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    gamma = 2 * 3.14159265 / 365 * (n - 1 + (hour - 12) / 24)

    decl = (
        0.006918
        - 0.399912 * cos(gamma)
        + 0.070257 * sin(gamma)
        - 0.006758 * cos(2 * gamma)
        + 0.000907 * sin(2 * gamma)
        - 0.002697 * cos(3 * gamma)
        + 0.00148 * sin(3 * gamma)
    )

    eq_time = (
        229.18
        * (
            0.000075
            + 0.001868 * cos(gamma)
            - 0.032077 * sin(gamma)
            - 0.014615 * cos(2 * gamma)
            - 0.040849 * sin(2 * gamma)
        )
    )

    time_offset = eq_time + 4 * lon - 60 * dt.utcoffset().total_seconds() / 60
    tst = hour * 60 + time_offset
    ha = radians((tst / 4) - 180)

    lat_rad = radians(lat)
    decl_rad = decl

    cos_zenith = sin(lat_rad) * sin(decl_rad) + cos(lat_rad) * cos(decl_rad) * cos(ha)
    cos_zenith = max(min(cos_zenith, 1.0), -1.0)
    zenith = acos_safe(cos_zenith)
    altitude = 90 - degrees(zenith)

    sin_az = -(sin(ha) * cos(decl_rad)) / cos_safe(radians(altitude))
    cos_az = (sin(decl_rad) - sin(lat_rad) * sin(radians(altitude))) / (
        cos(lat_rad) * cos_safe(radians(altitude))
    )
    azimuth = (degrees(atan2(sin_az, cos_az)) + 360) % 360
    return altitude, azimuth


def sun_vector(altitude: float, azimuth: float) -> Tuple[float, float, float]:
    alt_rad = radians(altitude)
    az_rad = radians(azimuth)
    x = cos(alt_rad) * sin(az_rad)
    y = cos(alt_rad) * cos(az_rad)
    z = sin(alt_rad)
    norm = sqrt(x * x + y * y + z * z) or 1.0
    return x / norm, y / norm, z / norm


def acos_safe(value: float) -> float:
    from math import acos

    return acos(max(min(value, 1.0), -1.0))


def cos_safe(angle: float) -> float:
    c = cos(angle)
    if abs(c) < 1e-6:
        return 1e-6 if c >= 0 else -1e-6
    return c
