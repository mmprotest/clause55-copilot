"""Input parsers for site and massing data."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, List

from ..domain.models import Building, Site


def load_site_json(path: Path | str) -> Site:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Site.model_validate(data)


def _buildings_from_payload(items: Iterable[dict]) -> List[Building]:
    return [Building.model_validate(item) for item in items]


def _parse_massing_json(text: str) -> List[Building]:
    data = json.loads(text)
    payload = data.get("buildings", data) if isinstance(data, dict) else data
    if not isinstance(payload, list):
        raise ValueError("Expected 'buildings' list in massing JSON")
    return _buildings_from_payload(payload)


def load_massing_json(path: Path | str) -> List[Building]:
    return _parse_massing_json(Path(path).read_text(encoding="utf-8"))


def load_ifc(path: Path | str) -> List[Building]:  # pragma: no cover - optional pathway
    try:
        import ifcopenshell  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise ImportError("ifcopenshell not installed – install optional extra") from exc
    model = ifcopenshell.open(str(path))
    buildings: List[Building] = []
    for building in model.by_type("IfcBuildingStorey"):
        extras = getattr(building, "Description", "")
        if extras:
            try:
                payload = json.loads(extras)
                buildings.append(Building.model_validate(payload))
                continue
            except json.JSONDecodeError:
                pass
        footprint = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        buildings.append(
            Building(
                name=getattr(building, "Name", "IfcBuilding"),
                footprint=footprint,
                height=3.0,
            )
        )
    return buildings


def _parse_gltf_json(text: str) -> List[Building]:
    data = json.loads(text)
    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    buildings: List[Building] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        extras = node.get("extras")
        if not isinstance(extras, dict):
            continue
        footprint = extras.get("footprint")
        height = extras.get("height")
        if footprint and height:
            payload = {
                "name": node.get("name", f"Node {len(buildings) + 1}"),
                "footprint": footprint,
                "height": height,
            }
            if "openings" in extras:
                payload["openings"] = extras["openings"]
            buildings.append(Building.model_validate(payload))
    if not buildings:
        raise ValueError("GLTF file missing 'extras.footprint' definitions for nodes")
    return buildings


def load_gltf(path: Path | str) -> List[Building]:  # pragma: no cover - optional pathway
    return _parse_gltf_json(Path(path).read_text(encoding="utf-8"))


def load_massing(path: Path | str) -> List[Building]:
    suffix = Path(path).suffix.lower()
    if suffix == ".ifc":
        return load_ifc(path)
    if suffix == ".gltf":
        return load_gltf(path)
    return load_massing_json(path)


def load_massing_from_bytes(data: bytes, filename: str | None = None) -> List[Building]:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".ifc":
        with NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            return load_ifc(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Unsupported massing encoding; expected UTF-8 JSON") from exc
    if suffix == ".gltf":
        return _parse_gltf_json(text)
    return _parse_massing_json(text)
