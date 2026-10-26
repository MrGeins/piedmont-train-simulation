"""Consistency checks for route, platform and service JSON configuration."""
from __future__ import annotations

import re
from typing import Any

_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$")


class ServicesConfigError(ValueError):
    """Raised when service configuration references invalid infrastructure."""


def validate_services(data: Any, infrastructure: dict[str, Any], source: str = "services config") -> None:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise ServicesConfigError(f"{source}: root must be a JSON object")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for section in ("ROUTES", "PLATFORM_PLANS", "SERVICES"):
        if not isinstance(data.get(section), dict):
            errors.append(f"{section} must be an object")
    if errors:
        raise ServicesConfigError(f"{source}: " + "; ".join(errors))

    routes, plans, services = data["ROUTES"], data["PLATFORM_PLANS"], data["SERVICES"]
    if not routes:
        errors.append("ROUTES must not be empty")

    for key, route in routes.items():
        if not isinstance(route, list) or not route:
            errors.append(f"ROUTES.{key} must be a non-empty list")
            continue
        if any(not isinstance(station, str) or station not in infrastructure for station in route):
            missing = [station for station in route if not isinstance(station, str) or station not in infrastructure]
            errors.append(f"ROUTES.{key} references unknown station(s): {missing}")
        if len(set(route)) != len(route):
            errors.append(f"ROUTES.{key} contains duplicate stations")

    for service, plan in plans.items():
        if service not in routes:
            errors.append(f"PLATFORM_PLANS.{service} has no matching route")
        if not isinstance(plan, dict):
            errors.append(f"PLATFORM_PLANS.{service} must be an object")
            continue
        for station, track in plan.items():
            if station not in infrastructure:
                errors.append(f"PLATFORM_PLANS.{service}.{station} references unknown station")
                continue
            if isinstance(track, bool) or not isinstance(track, int):
                errors.append(f"PLATFORM_PLANS.{service}.{station} track must be an integer")
                continue
            available = infrastructure[station].get("available_tracks", [])
            if track not in available:
                errors.append(f"PLATFORM_PLANS.{service}.{station} selects unavailable track {track}; available={available}")

    required = ("service_id", "base_num", "fleet_size", "frequency_min", "start_time", "end_time")
    for name, service_cfg in services.items():
        if not isinstance(service_cfg, dict):
            errors.append(f"SERVICES.{name} must be an object")
            continue
        for field in required:
            if field not in service_cfg:
                errors.append(f"SERVICES.{name}.{field} is required")
        service_id = service_cfg.get("service_id")
        if not isinstance(service_id, str) or not service_id:
            errors.append(f"SERVICES.{name}.service_id must be a non-empty string")
        elif service_id != name:
            errors.append(f"SERVICES.{name}.service_id must match its key")
        if service_id not in routes:
            errors.append(f"SERVICES.{name}.service_id references unknown route {service_id!r}")
        for field in ("base_num", "fleet_size", "frequency_min"):
            value = service_cfg.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                errors.append(f"SERVICES.{name}.{field} must be a positive integer")
        for field in ("start_time", "end_time"):
            value = service_cfg.get(field)
            if not isinstance(value, str) or not _TIME_RE.fullmatch(value):
                errors.append(f"SERVICES.{name}.{field} must use HH:MM:SS format")
    if errors:
        raise ServicesConfigError(f"{source}: validation failed:\n- " + "\n- ".join(errors))
