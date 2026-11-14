"""Load explicitly calibrated pneumatic brake formations from JSON.

The loader is opt-in. It never derives physical parameters from rolling-stock
catalogue entries or technical-reference candidates.
"""
from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any

from backend.railway.braking import (
    BrakeCylinderModel,
    BrakeFormation,
    BrakePipeModel,
    BrakeVehicle,
)

DEFAULT_BRAKING_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "braking" / "formations.json"
)


class BrakingConfigError(ValueError):
    """Raised when a pneumatic brake formation configuration is invalid."""


def _object(value: Any, name: str, required: set[str], optional: set[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise BrakingConfigError(f"{name} must be an object")
    allowed = required | (optional or set())
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise BrakingConfigError(f"{name} is missing required fields: {', '.join(sorted(missing))}")
    if unknown:
        raise BrakingConfigError(f"{name} has unknown fields: {', '.join(sorted(unknown))}")
    return value


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BrakingConfigError(f"{name} must be a non-empty string")
    return value


def _number(value: Any, name: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise BrakingConfigError(f"{name} must be a finite number")
    if value < 0 if allow_zero else value <= 0:
        qualifier = "non-negative" if allow_zero else "positive"
        raise BrakingConfigError(f"{name} must be {qualifier}")
    return float(value)


def validate_braking_config(data: Any, source: str = "braking config") -> None:
    try:
        root = _object(data, "root", {"schema_version", "formations"})
        if isinstance(root["schema_version"], bool) or root["schema_version"] != 1:
            raise BrakingConfigError("schema_version must be 1")
        formations = root["formations"]
        if not isinstance(formations, list):
            raise BrakingConfigError("formations must be an array")
        seen_formations: set[str] = set()
        for index, raw_formation in enumerate(formations):
            prefix = f"formations[{index}]"
            formation = _object(
                raw_formation, prefix,
                {"formation_id", "brake_pipe", "vehicles"},
            )
            formation_id = _identifier(formation["formation_id"], f"{prefix}.formation_id")
            if formation_id in seen_formations:
                raise BrakingConfigError(f"duplicate formation_id: {formation_id}")
            seen_formations.add(formation_id)

            pipe = _object(
                formation["brake_pipe"], f"{prefix}.brake_pipe",
                {"propagation_speed_mps", "pressure_response_time_constant_seconds",
                 "full_service_pressure_reduction_kpa"},
            )
            for field in pipe:
                _number(pipe[field], f"{prefix}.brake_pipe.{field}")

            vehicles = formation["vehicles"]
            if not isinstance(vehicles, list) or not vehicles:
                raise BrakingConfigError(f"{prefix}.vehicles must be a non-empty array")
            seen_vehicles: set[str] = set()
            previous_position = -1.0
            for vehicle_index, raw_vehicle in enumerate(vehicles):
                vehicle_prefix = f"{prefix}.vehicles[{vehicle_index}]"
                vehicle = _object(
                    raw_vehicle, vehicle_prefix,
                    {"vehicle_id", "position_m", "mass_kg", "maximum_brake_force_n",
                     "brake_cylinder"},
                )
                vehicle_id = _identifier(vehicle["vehicle_id"], f"{vehicle_prefix}.vehicle_id")
                if vehicle_id in seen_vehicles:
                    raise BrakingConfigError(
                        f"{prefix} contains duplicate vehicle_id: {vehicle_id}"
                    )
                seen_vehicles.add(vehicle_id)
                position = _number(
                    vehicle["position_m"], f"{vehicle_prefix}.position_m", allow_zero=True
                )
                if vehicle_index == 0 and position != 0:
                    raise BrakingConfigError(
                        f"{vehicle_prefix}.position_m must be 0 for the command-source vehicle"
                    )
                if position < previous_position:
                    raise BrakingConfigError(
                        f"{prefix}.vehicles must be ordered by non-decreasing position_m"
                    )
                previous_position = position
                _number(vehicle["mass_kg"], f"{vehicle_prefix}.mass_kg")
                _number(
                    vehicle["maximum_brake_force_n"],
                    f"{vehicle_prefix}.maximum_brake_force_n",
                )
                cylinder = _object(
                    vehicle["brake_cylinder"], f"{vehicle_prefix}.brake_cylinder",
                    {"maximum_pressure_kpa", "fill_time_constant_seconds"},
                )
                for field in cylinder:
                    _number(cylinder[field], f"{vehicle_prefix}.brake_cylinder.{field}")
    except BrakingConfigError as exc:
        raise BrakingConfigError(f"{source}: {exc}") from exc


def load_brake_formations(
    config_path: str | Path | None = None,
) -> dict[str, BrakeFormation]:
    """Load configured formations; an empty mapping means none are calibrated."""
    path = Path(config_path) if config_path is not None else DEFAULT_BRAKING_CONFIG_PATH
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise RuntimeError(f"Cannot read braking configuration '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BrakingConfigError(
            f"Invalid JSON in braking configuration '{path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    validate_braking_config(data, source=str(path))
    loaded: dict[str, BrakeFormation] = {}
    for item in data["formations"]:
        pipe_data = item["brake_pipe"]
        pipe = BrakePipeModel(**pipe_data)
        vehicles = tuple(
            BrakeVehicle(
                vehicle_id=vehicle["vehicle_id"],
                position_m=vehicle["position_m"],
                mass_kg=vehicle["mass_kg"],
                maximum_brake_force_n=vehicle["maximum_brake_force_n"],
                brake_cylinder=BrakeCylinderModel(**vehicle["brake_cylinder"]),
            )
            for vehicle in item["vehicles"]
        )
        loaded[item["formation_id"]] = BrakeFormation(vehicles, pipe)
    return loaded
