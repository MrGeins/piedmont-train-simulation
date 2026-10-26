"""Load and validate the declarative railway infrastructure configuration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.model.models import RailwayLine, RailwayStation
from backend.configuration.validator import validate_infrastructure

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "infrastructure" / "sfm.json"


def load_infrastructure(config_path: str | Path | None = None) -> tuple[dict[str, RailwayStation], list[RailwayLine], dict[str, dict[str, Any]]]:
    """Load config and return runtime objects compatible with legacy exports."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise RuntimeError(f"Cannot read infrastructure configuration '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in infrastructure configuration '{path}' at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    validate_infrastructure(data, source=str(path))
    registry = {
        key: RailwayStation(
            key=key, name=item["name"], roro_station=item["roro_station"],
            default_dwell=item["default_dwell"], terminal=item["terminal"],
            num_tracks=item["num_tracks"], available_tracks=item["available_tracks"],
            stub_tracks={int(track): direction for track, direction in item["stub_tracks"].items()},
        )
        for key, item in data["stations"].items()
    }
    links = [RailwayLine(item["from"], item["to"], item["double_track"]) for item in data["links"]]
    topology = {
        key: {"nome": item["name"], "x": item["x"], "y": item["y"], "display_label": item["display_label"]}
        for key, item in data["topology"].items()
    }
    return registry, links, topology
