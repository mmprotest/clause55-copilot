"""Typed domain models used throughout the Clause 55 pipeline."""

from __future__ import annotations

from datetime import date, time
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field, RootModel, field_validator


Coordinate = Tuple[float, float]
Polygon = List[Coordinate]


class Opening(BaseModel):
    """Building opening metadata used for overlooking and daylight checks."""

    name: str
    sill_height: float = Field(gt=0, description="Sill height above finished floor level in metres")
    head_height: float = Field(gt=0, description="Head height above finished floor level in metres")
    centre: Coordinate = Field(description="Plan coordinate of the opening centre")
    orientation: float = Field(ge=0, lt=360, description="Orientation in degrees (0° = north)")

    @field_validator("head_height")
    @classmethod
    def check_head_above_sill(cls, v: float, values: Dict[str, object]) -> float:
        sill = values.get("sill_height")
        if isinstance(sill, (int, float)) and v <= sill:
            msg = "Opening head height must exceed sill height"
            raise ValueError(msg)
        return v


class SPOS(BaseModel):
    """Secluded private open space polygon definition."""

    name: str
    polygon: Polygon

    @field_validator("polygon")
    @classmethod
    def validate_polygon(cls, value: Sequence[Coordinate]) -> Polygon:
        if len(value) < 3:
            msg = "SPOS polygons require at least three vertices"
            raise ValueError(msg)
        return [tuple(map(float, pt)) for pt in value]


class Building(BaseModel):
    """Simple extruded building representation used for rules checks."""

    name: str
    footprint: Polygon
    height: float = Field(gt=0, description="Extrusion height in metres")
    roof_type: str = Field(default="flat")
    openings: List[Opening] = Field(default_factory=list)

    @field_validator("footprint")
    @classmethod
    def validate_footprint(cls, value: Sequence[Coordinate]) -> Polygon:
        if len(value) < 3:
            msg = "Building footprints require at least three vertices"
            raise ValueError(msg)
        return [tuple(map(float, pt)) for pt in value]


class Lot(BaseModel):
    """Lot-specific metadata including setbacks and easements."""

    site_name: str
    setbacks: Dict[str, float] = Field(default_factory=dict)
    easements: List[Polygon] = Field(default_factory=list)


class PropertyReport(BaseModel):
    """Property information sourced via VicPlan or local mock data."""

    address: str
    planning_scheme: str
    council: str
    zones: List[str] = Field(default_factory=list)
    overlays: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class Site(BaseModel):
    """Describes the site geometry and key metadata."""

    name: str
    address: str
    latitude: float
    longitude: float
    timezone: str
    boundary: Polygon
    spos: List[SPOS] = Field(default_factory=list)
    contours: Optional[List[Polygon]] = None
    northing: float = 0.0

    @field_validator("boundary")
    @classmethod
    def validate_boundary(cls, value: Sequence[Coordinate]) -> Polygon:
        if len(value) < 3:
            msg = "Site boundary must contain at least three points"
            raise ValueError(msg)
        return [tuple(map(float, pt)) for pt in value]


class CheckStatus(str, Enum):
    """Possible outcomes for a Clause 55 rule check."""

    PASS = "PASS"
    FAIL = "FAIL"
    NA = "N/A"


class CheckResult(BaseModel):
    """Result bundle for an individual standard or objective."""

    clause_id: str
    title: str
    status: CheckStatus
    metrics: Dict[str, float] = Field(default_factory=dict)
    notes: str = ""
    figure_refs: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)


class ReportSpec(BaseModel):
    """Controls solar analysis parameters for the report run."""

    analysis_date: date = Field(description="Primary solar analysis date")
    start_time: time = Field(description="Start time for solar time sweep")
    end_time: time = Field(description="End time for solar time sweep")
    time_step_minutes: int = Field(default=60, ge=5, le=180)
    shadow_resolution: float = Field(default=0.5, gt=0)

    @classmethod
    def default(cls) -> "ReportSpec":
        return cls(
            analysis_date=date(date.today().year, 9, 22),
            start_time=time(hour=9),
            end_time=time(hour=15),
            time_step_minutes=60,
            shadow_resolution=0.5,
        )


