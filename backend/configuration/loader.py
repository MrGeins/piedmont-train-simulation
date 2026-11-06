"""Load and validate the declarative railway infrastructure configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.model.models import RailwayLine, RailwayStation
from backend.configuration.providers import InfrastructureProvider, LocalJsonInfrastructureProvider
from backend.configuration.validator import validate_infrastructure

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "infrastructure" / "sfm.json"


def load_infrastructure(
    config_path: str | Path | None = None,
    provider: InfrastructureProvider | None = None,
) -> tuple[dict[str, RailwayStation], list[RailwayLine], dict[str, dict[str, Any]]]:
    """Load runtime infrastructure through a provider, defaulting to local JSON.

    Providers return the same normalized configuration document, so validation
    and conversion into runtime model objects remain independent of the source.
    """
    if provider is not None and config_path is not None:
        raise ValueError("Pass either config_path or provider, not both")
    source_provider = provider or LocalJsonInfrastructureProvider(
        Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    )
    data = source_provider.load_data()
    validate_infrastructure(data, source=source_provider.source)

    registry = {
        key: RailwayStation(
            key=key, name=item["name"], roro_station=item["roro_station"],
            default_dwell=item["default_dwell"], terminal=item["terminal"],
            num_tracks=item["num_tracks"], available_tracks=item["available_tracks"],
            stub_tracks={int(track): direction for track, direction in item["stub_tracks"].items()},
        )
        for key, item in data["stations"].items()
    }
    links = [
        RailwayLine(
            item["from"], item["to"], item["double_track"],
            distance_km=item.get("distance_km"),
            speed_limit_kmh=item.get("speed_limit_kmh"),
            gradient_permille=item.get("gradient_permille"),
            electrified=item.get("electrified"),
            track_type=item.get("track_type"),
        )
        for item in data["links"]
    ]
    topology = {
        key: {"nome": item["name"], "x": item["x"], "y": item["y"], "display_label": item["display_label"]}
        for key, item in data["topology"].items()
    }
    return registry, links, topology
