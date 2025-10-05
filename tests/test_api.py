from pathlib import Path

from fastapi.testclient import TestClient

from c55copilot.api.main import app

client = TestClient(app)

SAMPLES = Path("src/c55copilot/assets/samples")


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint(tmp_path):
    site_data = (SAMPLES / "site_fitzroy.json").read_text(encoding="utf-8")
    massing_data = (SAMPLES / "massing_two_townhouses.json").read_text(encoding="utf-8")
    files = {
        "site": ("site.json", site_data, "application/json"),
        "massing": ("massing.json", massing_data, "application/json"),
    }
    data = {"use_mock_property": "true"}
    response = client.post("/analyze", files=files, data=data)
    assert response.status_code == 200
    payload = response.json()
    outputs = payload["outputs"]
    pdf_path = Path(outputs["pdf"])
    assert pdf_path.exists()
    matrix_path = Path(outputs["xlsx"])
    assert matrix_path.exists()
    figure_paths = [Path(p) for p in outputs["figures"]]
    assert len(figure_paths) >= 1
    assert all(path.exists() for path in figure_paths)


def test_analyze_accepts_gltf(tmp_path):
    site_bytes = (SAMPLES / "site_fitzroy.json").read_bytes()
    gltf_bytes = (SAMPLES / "massing_single.gltf").read_bytes()
    files = {
        "site": ("site.json", site_bytes, "application/json"),
        "massing": ("model.gltf", gltf_bytes, "model/gltf+json"),
    }
    data = {"use_mock_property": "true"}
    response = client.post("/analyze", files=files, data=data)
    assert response.status_code == 200
    payload = response.json()
    assert "outputs" in payload
