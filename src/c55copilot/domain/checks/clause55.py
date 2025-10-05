"""Clause 55 rule orchestration."""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Dict, Iterable, List

try:  # pragma: no cover - optional dependency
    import yaml

    HAS_YAML = True
except Exception:  # pragma: no cover - fallback
    HAS_YAML = False

from ..models import Building, CheckResult, PropertyReport, ReportSpec, Site


RULES_PATH = Path(__file__).resolve().parents[2] / "rules" / "victoria_clause55.yaml"


@lru_cache(maxsize=1)
def _load_rule_configs() -> List[Dict[str, object]]:
    text = RULES_PATH.read_text(encoding="utf-8")
    if HAS_YAML:
        data = yaml.safe_load(text)
        return data.get("rules", []) if isinstance(data, dict) else []
    return _parse_rules(text)


def _parse_rules(text: str) -> List[Dict[str, object]]:
    rules: List[Dict[str, object]] = []
    current: Dict[str, object] | None = None
    list_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "rules:":
            continue
        indent = len(line) - len(stripped)
        if stripped.startswith("- ") and indent <= 2:
            if current:
                rules.append(current)
            current = {}
            list_key = None
            stripped = stripped[2:].strip()
            if stripped:
                key, value = _split_key_value(stripped)
                current[key] = value
            continue
        if current is None:
            continue
        if stripped.endswith(":"):
            list_key = stripped[:-1]
            current[list_key] = []
            continue
        if stripped.startswith("- ") and list_key:
            current[list_key].append(stripped[2:].strip().strip('"'))
            continue
        key, value = _split_key_value(stripped)
        current[key] = value
    if current:
        rules.append(current)
    return rules


def _split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        return line, ""
    key, value = line.split(":", 1)
    return key.strip(), value.strip().strip('"')


def _resolve_handler(handler: str):
    module_name, func_name = handler.split(":")
    module = import_module(f"c55copilot.domain.checks.standards.{module_name}")
    return getattr(module, func_name)


def run_clause55_checks(
    *,
    site: Site,
    buildings: Iterable[Building],
    property_report: PropertyReport | None,
    spec: ReportSpec,
) -> List[CheckResult]:
    results: List[CheckResult] = []
    building_list = list(buildings)
    for rule in _load_rule_configs():
        handler = _resolve_handler(str(rule["handler"]))
        result: CheckResult = handler(
            site=site,
            buildings=building_list,
            property_report=property_report,
            spec=spec,
            rule_meta=rule,
        )
        results.append(result)
    return results

