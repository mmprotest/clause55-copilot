"""Runtime configuration for Clause55 Copilot."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    telemetry_enabled: bool = False
    license_key: Optional[str] = None
    storage_dir: Path = Path("out")

    @classmethod
    def from_env(cls) -> "Settings":
        telemetry = os.getenv("C55_TELEMETRY", "0").lower() in {"1", "true", "yes"}
        license_key = os.getenv("C55_LICENSE_KEY")
        storage_dir = Path(os.getenv("C55_STORAGE_DIR", "out"))
        return cls(telemetry_enabled=telemetry, license_key=license_key, storage_dir=storage_dir)


@dataclass
class TelemetryCounter:
    path: Path

    def increment(self, label: str) -> None:
        data = {}
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        data[label] = int(data.get(label, 0)) + 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")


settings = Settings.from_env()
telemetry = TelemetryCounter(settings.storage_dir / "telemetry.json") if settings.telemetry_enabled else None
