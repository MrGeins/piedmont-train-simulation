"""Load verified rolling-stock performance profiles from JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.railway.vehicle_performance import VehiclePerformance

DEFAULT_ROLLING_STOCK_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "rolling_stock" / "sfm.json"
)


class RollingStockConfigError(ValueError):
    """Raised when a rolling-stock profile is invalid."""


def validate_rolling_stock(data: Any, source: str = "rolling stock config") -> None:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise RollingStockConfigError(f"{source}: root must be a JSON object")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        errors.append("profiles must be an object")
    else:
        for profile_id, profile in profiles.items():
            prefix = f"profiles.{profile_id}"
            if not isinstance(profile, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for field in ("max_speed_kmh", "acceleration_mps2", "service_braking_mps2"):
                value = profile.get(field)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                    errors.append(f"{prefix}.{field} must be a positive number")
            turnback = profile.get("minimum_turnback_seconds", 90)
            if isinstance(turnback, bool) or not isinstance(turnback, int) or turnback < 0:
                errors.append(f"{prefix}.minimum_turnback_seconds must be a non-negative integer")
    if errors:
        raise RollingStockConfigError(
            f"{source}: validation failed:\\n- " + "\\n- ".join(errors)
        )


def load_vehicle_profiles(
    config_path: str | Path | None = None,
) -> dict[str, VehiclePerformance]:
    """Return configured vehicle profiles; empty means no verified profile exists yet."""
    path = Path(config_path) if config_path is not None else DEFAULT_ROLLING_STOCK_PATH
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise RuntimeError(f"Cannot read rolling stock configuration '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in rolling stock configuration '{path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    validate_rolling_stock(data, source=str(path))
    return {
        profile_id: VehiclePerformance(
            max_speed_kmh=profile["max_speed_kmh"],
            acceleration_mps2=profile["acceleration_mps2"],
            service_braking_mps2=profile["service_braking_mps2"],
            minimum_turnback_seconds=profile.get("minimum_turnback_seconds", 90),
        )
        for profile_id, profile in data["profiles"].items()
    }
