"""Utility helpers for Clause 55 checks."""

from __future__ import annotations

from typing import Dict, Iterable, List

from ...models import Building, CheckResult, CheckStatus, PropertyReport, ReportSpec, Site


def base_result(
    rule_meta: Dict[str, str],
    status: CheckStatus,
    metrics: Dict[str, float] | None = None,
    notes: str = "",
    figures: Iterable[str] | None = None,
) -> CheckResult:
    citations = rule_meta.get("citations", [])
    if isinstance(citations, str):
        citations = [citations]
    return CheckResult(
        clause_id=rule_meta["id"],
        title=rule_meta.get("title", ""),
        status=status,
        metrics=metrics or {},
        notes=notes,
        figure_refs=list(figures or []),
        citations=list(citations),
    )


def summarise_pass(prefix: str, value: float, requirement: float) -> str:
    return f"{prefix} {value:.1f}m meets the {requirement:.1f}m requirement."


def summarise_fail(prefix: str, value: float, requirement: float) -> str:
    return f"{prefix} {value:.1f}m is below the {requirement:.1f}m requirement."


def requires_property_report(property_report: PropertyReport | None) -> None:
    if property_report is None:
        raise ValueError("This check requires a property report to run")
