"""Load and validate timetable service configuration stored as JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.configuration.services_validator import validate_services

DEFAULT_SERVICES_PATH = Path(__file__).resolve().parents[2] / "config" / "services" / "sfm.json"


def load_services(
    config_path: str | Path | None = None,
    infrastructure: dict[str, Any] | None = None,
) -> tuple[dict[str, list[str]], dict[str, dict[str, int]], dict[str, dict[str, Any]]]:
    """Return routes, platform plans and parameter-only service definitions."""
    path = Path(config_path) if config_path is not None else DEFAULT_SERVICES_PATH
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise RuntimeError(f"Cannot read services configuration '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in services configuration '{path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if infrastructure is None:
        from backend.configuration.loader import load_infrastructure
        stations, _, _ = load_infrastructure()
        infrastructure = {
            key: {"available_tracks": station.available_tracks}
            for key, station in stations.items()
        }
    validate_services(data, infrastructure, source=str(path))
    return data["ROUTES"], data["PLATFORM_PLANS"], data["SERVICES"]
