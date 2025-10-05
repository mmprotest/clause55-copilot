"""API routes for Clause55 Copilot."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..analysis import run_analysis
from ..config import settings
from ..domain.models import PropertyReport, ReportSpec, Site
from ..io.parsers import load_massing_from_bytes
from ..io.property_data import fetch_vicplan, load_property_report_mock

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "assets" / "samples"

router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze")
async def analyze(
    site: UploadFile = File(...),
    massing: UploadFile = File(...),
    property_report: UploadFile | None = File(None),
    report_spec: str | None = Form(None),
    use_mock_property: bool = Form(False),
) -> Dict[str, Any]:
    site_bytes = await site.read()
    massing_bytes = await massing.read()

    try:
        site_payload = json.loads(site_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:  # pragma: no cover - request guard
        raise HTTPException(status_code=400, detail="Invalid site JSON payload") from exc

    site_model = Site.model_validate(site_payload)

    try:
        buildings = load_massing_from_bytes(massing_bytes, massing.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if report_spec:
        spec_model = ReportSpec.model_validate(json.loads(report_spec))
    else:
        spec_model = ReportSpec.default()

    if property_report:
        report_payload = json.loads((await property_report.read()).decode("utf-8"))
        property_model = PropertyReport.model_validate(report_payload)
    elif use_mock_property:
        property_model = load_property_report_mock(SAMPLES_DIR / "property_report_mock.json")
    else:
        property_model = fetch_vicplan(site_model.address)

    output_dir = settings.storage_dir / f"api_job_{uuid.uuid4().hex}"

    summary = run_analysis(
        site=site_model,
        buildings=buildings,
        property_report=property_model,
        spec=spec_model,
        output_dir=output_dir,
        license_key=settings.license_key,
    )
    return summary
