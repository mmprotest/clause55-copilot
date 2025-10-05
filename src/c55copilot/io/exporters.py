"""Export utilities for report artefacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence

HAS_MATPLOTLIB = False
HAS_OPENPYXL = False
HAS_WEASYPRINT = False
HAS_JINJA = False

try:  # pragma: no cover - optional dependency
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    HAS_MATPLOTLIB = True
except Exception:  # pragma: no cover - fallback
    plt = None  # type: ignore
    MplPolygon = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from openpyxl import Workbook

    HAS_OPENPYXL = True
except Exception:  # pragma: no cover - fallback
    Workbook = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from weasyprint import CSS, HTML

    HAS_WEASYPRINT = True
except Exception:  # pragma: no cover - fallback
    CSS = HTML = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    HAS_JINJA = True
except Exception:  # pragma: no cover - fallback
    Environment = FileSystemLoader = select_autoescape = None  # type: ignore

from ..domain.geometry import HAS_SHAPELY, area, to_polygon
from ..domain.models import Building, CheckResult, PropertyReport, ReportSpec, Site
from ..domain.overshadowing import (
    RasterShadow,
    ShadowSlice,
    aggregate_shadow_metrics,
    total_shadow_area,
)


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "assets" / "templates"


def export_report_pack(
    *,
    site: Site,
    buildings: List[Building],
    property_report: PropertyReport | None,
    results: List[CheckResult],
    slices: List[ShadowSlice],
    spec: ReportSpec,
    output_dir: Path,
    license_key: str | None,
) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    figure_paths = generate_shadow_figures(site, buildings, slices, figures_dir)
    matrix_path = export_matrix(results, output_dir / "matrix.xlsx")
    pdf_path = export_pdf(
        site=site,
        results=results,
        property_report=property_report,
        slices=slices,
        spec=spec,
        path=output_dir / "report.pdf",
        licensed=bool(license_key),
    )

    return {"pdf": pdf_path, "xlsx": matrix_path, "figures": figure_paths}


def generate_shadow_figures(
    site: Site,
    buildings: Iterable[Building],
    slices: Iterable[ShadowSlice],
    output_dir: Path,
) -> List[Path]:
    paths: List[Path] = []
    if HAS_MATPLOTLIB:
        site_poly = to_polygon(site.boundary)
        spos_polys = {spos.name: to_polygon(spos.polygon) for spos in site.spos}
        for slice_ in slices:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_title(f"Shadows {slice_.timestamp.strftime('%H:%M')} – alt {slice_.altitude:.1f}°")

            _draw_polygon(ax, site_poly, edgecolor="#111827", facecolor="none", linewidth=2)
            for building in buildings:
                _draw_polygon(ax, to_polygon(building.footprint), facecolor="#9ca3af", alpha=0.6)
            for spos_name, spos_poly in spos_polys.items():
                _draw_polygon(
                    ax,
                    spos_poly,
                    facecolor="#6ee7b7",
                    alpha=0.4,
                    hatch="///",
                    label=f"{spos_name}"
                )
            if slice_.combined_shadow:
                geometries = _iter_polygons(slice_.combined_shadow)
                for poly in geometries:
                    _draw_polygon(ax, poly, facecolor="#1f2937", alpha=0.35)

            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("Eastings (m)")
            ax.set_ylabel("Northings (m)")
            if site.spos:
                ax.legend(loc="upper right")
            ax.grid(True, linestyle="--", alpha=0.3)

            filename = f"{slice_.timestamp.strftime('%H')}.png"
            path = output_dir / filename
            fig.savefig(path, dpi=200, bbox_inches="tight")
            plt.close(fig)
            paths.append(path)
    else:
        for slice_ in slices:
            filename = f"{slice_.timestamp.strftime('%H')}.txt"
            path = output_dir / filename
            lines = [f"Shadows at {slice_.timestamp.isoformat()}"]
            for name, sunlit in slice_.spos_sunlit.items():
                lines.append(f"{name}: {sunlit:.2f} m2 sunlit")
            path.write_text("\n".join(lines), encoding="utf-8")
            paths.append(path)
    return paths


def export_matrix(results: Iterable[CheckResult], path: Path) -> Path:
    if HAS_OPENPYXL:
        wb = Workbook()
        ws = wb.active
        ws.title = "Clause 55 Matrix"
        ws.append(["Clause", "Title", "Status", "Key Metrics", "Notes"])
        for result in results:
            metrics_json = json.dumps(result.metrics, ensure_ascii=False)
            ws.append([result.clause_id, result.title, result.status.value, metrics_json, result.notes])
        wb.save(path)
    else:
        lines = ["Clause,Title,Status,Key Metrics,Notes"]
        for result in results:
            metrics_json = json.dumps(result.metrics, ensure_ascii=False)
            line = ",".join(
                [
                    result.clause_id,
                    result.title.replace(",", ";"),
                    result.status.value,
                    metrics_json.replace(",", ";"),
                    result.notes.replace(",", ";"),
                ]
            )
            lines.append(line)
        path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_pdf(
    *,
    site: Site,
    results: List[CheckResult],
    property_report: PropertyReport | None,
    slices: List[ShadowSlice],
    spec: ReportSpec,
    path: Path,
    licensed: bool,
) -> Path:
    citations = sorted({citation for result in results for citation in result.citations})
    metrics = aggregate_shadow_metrics(slices, site)
    shadow_totals = total_shadow_area(slices)
    branding_html = "" if licensed else "<div class='watermark'>Community Edition</div>"

    if HAS_JINJA:
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        )
        cover_template = env.get_template("cover.html")
        report_template = env.get_template("report.html")
        cover_html = cover_template.render(
            project_title=site.name,
            address=site.address,
            analysis_date=spec.analysis_date.strftime("%d %B %Y"),
        )
        report_html = report_template.render(
            site=site,
            results=results,
            property_report=property_report,
            spec=spec,
            metrics=metrics,
            shadow_totals=shadow_totals,
            branding=branding_html,
            citations=citations,
        )
    else:
        cover_html = f"""<html><body class='cover'><h1>{site.name}</h1><p>{site.address}</p></body></html>"""
        matrix_rows = "".join(
            f"<tr><td>{r.clause_id}</td><td>{r.title}</td><td>{r.status.value}</td><td>{json.dumps(r.metrics)}</td><td>{r.notes}</td></tr>"
            for r in results
        )
        citations_html = "".join(f"<li>{c}</li>" for c in citations)
        report_html = f"""<html><body>{branding_html}<table>{matrix_rows}</table><ol>{citations_html}</ol></body></html>"""

    if HAS_WEASYPRINT:
        stylesheets = [CSS(filename=str(TEMPLATES_DIR / "styles.css"))]
        cover_doc = HTML(string=cover_html, base_url=str(TEMPLATES_DIR)).render(stylesheets=stylesheets)
        report_doc = HTML(string=report_html, base_url=str(TEMPLATES_DIR)).render(stylesheets=stylesheets)
        cover_doc.pages.extend(report_doc.pages)
        cover_doc.attachments.extend(report_doc.attachments)
        cover_doc.write_pdf(target=str(path))
    else:
        path.write_text(cover_html + "\n<!--PAGEBREAK-->\n" + report_html, encoding="utf-8")
    return path


def _draw_polygon(ax, polygon, **kwargs):
    if not polygon:
        return
    if HAS_SHAPELY:
        if polygon.geom_type == "Polygon":
            patch = MplPolygon(list(polygon.exterior.coords), closed=True, **kwargs)
            ax.add_patch(patch)
        else:
            for geom in polygon.geoms:
                _draw_polygon(ax, geom, **kwargs)
    else:
        patch = MplPolygon(list(polygon), closed=True, **kwargs)
        ax.add_patch(patch)


def _iter_polygons(geometry):
    if HAS_SHAPELY:
        if geometry.is_empty:
            return []
        if geometry.geom_type == "Polygon":
            return [geometry]
        return list(geometry.geoms)
    if isinstance(geometry, RasterShadow):
        return geometry.polygons
    if not geometry:
        return []
    return [geometry]

