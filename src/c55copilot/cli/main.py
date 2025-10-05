"""Command line interface for Clause55 Copilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..analysis import run_analysis
from ..config import settings
from ..domain.models import ReportSpec
from ..io.parsers import load_massing, load_site_json
from ..io.property_data import fetch_vicplan, load_property_report_mock

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "assets" / "samples"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Clause 55 assessments")
    parser.add_argument("--site", required=True, help="Path to site JSON")
    parser.add_argument("--massing", required=True, help="Path to massing JSON/GLTF/IFC")
    parser.add_argument("--out", default="out", help="Output directory")
    parser.add_argument("--property", dest="property_path", help="Property report JSON")
    parser.add_argument("--report-spec", dest="report_spec", help="Report spec JSON")
    parser.add_argument("--use-mock-property", action="store_true", help="Use bundled mock property report")
    parser.add_argument("--batch", help="Folder of batch jobs (Pro feature)")
    return parser.parse_args()


def run_single(args: argparse.Namespace) -> None:
    site_model = load_site_json(args.site)
    buildings = load_massing(args.massing)

    if args.property_path:
        property_model = load_property_report_mock(args.property_path)
    elif args.use_mock_property:
        property_model = load_property_report_mock(SAMPLES_DIR / "property_report_mock.json")
    else:
        property_model = fetch_vicplan(site_model.address)

    if args.report_spec:
        spec_payload = json.loads(Path(args.report_spec).read_text(encoding="utf-8"))
        spec_model = ReportSpec.model_validate(spec_payload)
    else:
        spec_model = ReportSpec.default()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = run_analysis(
        site=site_model,
        buildings=buildings,
        property_report=property_model,
        spec=spec_model,
        output_dir=out_dir,
        license_key=settings.license_key,
    )
    print(json.dumps(summary, indent=2))


def process_batch(batch_dir: Path, out_dir: Path) -> None:
    for child in batch_dir.iterdir():
        if not child.is_dir():
            continue
        site_path = child / "site.json"
        massing_path = child / "massing.json"
        if not site_path.exists() or not massing_path.exists():
            continue
        job_out = out_dir / child.name
        job_out.mkdir(parents=True, exist_ok=True)
        site_model = load_site_json(site_path)
        buildings = load_massing(massing_path)
        property_path = child / "property_report.json"
        property_model = (
            load_property_report_mock(property_path) if property_path.exists() else fetch_vicplan(site_model.address)
        )
        summary = run_analysis(
            site=site_model,
            buildings=buildings,
            property_report=property_model,
            spec=ReportSpec.default(),
            output_dir=job_out,
            license_key=settings.license_key,
        )
        (job_out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.batch:
        if not settings.license_key:
            raise SystemExit("Batch processing requires C55_LICENSE_KEY")
        process_batch(Path(args.batch), Path(args.out))
    else:
        run_single(args)


if __name__ == "__main__":  # pragma: no cover
    main()
