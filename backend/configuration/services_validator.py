"""Consistency checks for route, platform and timetable JSON configuration."""
from __future__ import annotations
from typing import Any

class ServicesConfigError(ValueError):
    """Raised when service configuration references invalid infrastructure."""

def validate_services(data: Any, infrastructure: dict[str, Any], source: str = "services config") -> None:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise ServicesConfigError(f"{source}: root must be a JSON object")
    if data.get("schema_version") != 1: errors.append("schema_version must be 1")
    for section in ("ROUTES", "PLATFORM_PLANS", "TAKT_TEMPLATES"):
        if not isinstance(data.get(section), dict): errors.append(f"{section} must be an object")
    if errors: raise ServicesConfigError(f"{source}: " + "; ".join(errors))
    routes, plans, templates = data["ROUTES"], data["PLATFORM_PLANS"], data["TAKT_TEMPLATES"]
    if not routes: errors.append("ROUTES must not be empty")
    for key, route in routes.items():
        if not isinstance(route, list) or not route: errors.append(f"ROUTES.{key} must be a non-empty list"); continue
        if any(not isinstance(station, str) or station not in infrastructure for station in route):
            missing = [station for station in route if not isinstance(station, str) or station not in infrastructure]
            errors.append(f"ROUTES.{key} references unknown station(s): {missing}")
        if len(set(route)) != len(route): errors.append(f"ROUTES.{key} contains duplicate stations")
    for service, plan in plans.items():
        if service not in routes: errors.append(f"PLATFORM_PLANS.{service} has no matching route")
        if not isinstance(plan, dict): errors.append(f"PLATFORM_PLANS.{service} must be an object"); continue
        for station, track in plan.items():
            if station not in infrastructure:
                errors.append(f"PLATFORM_PLANS.{service}.{station} references unknown station"); continue
            if isinstance(track, bool) or not isinstance(track, int):
                errors.append(f"PLATFORM_PLANS.{service}.{station} track must be an integer"); continue
            available = infrastructure[station].get("available_tracks", [])
            if track not in available: errors.append(f"PLATFORM_PLANS.{service}.{station} selects unavailable track {track}; available={available}")
    for name, template in templates.items():
        if not isinstance(template, dict): errors.append(f"TAKT_TEMPLATES.{name} must be an object"); continue
        route_key = template.get("route_key")
        if route_key not in routes: errors.append(f"TAKT_TEMPLATES.{name}.route_key references unknown route {route_key!r}")
        for field in ("service_id", "base_num", "fleet_size", "start_time_south", "start_time_north", "end_time", "frequency_min", "SOUTH", "NORTH"):
            if field not in template: errors.append(f"TAKT_TEMPLATES.{name}.{field} is required")
        for field in ("base_num", "fleet_size", "frequency_min"):
            value = template.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0: errors.append(f"TAKT_TEMPLATES.{name}.{field} must be a positive integer")
        route = routes.get(route_key, [])
        for direction in ("SOUTH", "NORTH"):
            times = template.get(direction)
            if not isinstance(times, dict) or not times: errors.append(f"TAKT_TEMPLATES.{name}.{direction} must be a non-empty object"); continue
            for station, time in times.items():
                if station not in infrastructure: errors.append(f"TAKT_TEMPLATES.{name}.{direction} references unknown station {station!r}")
                if station not in route: errors.append(f"TAKT_TEMPLATES.{name}.{direction} stop {station!r} is not in route {route_key!r}")
                if not isinstance(time, str) or not time.strip(): errors.append(f"TAKT_TEMPLATES.{name}.{direction}.{station} must be a non-empty time string")
    if errors: raise ServicesConfigError(f"{source}: validation failed:\n- " + "\n- ".join(errors))
