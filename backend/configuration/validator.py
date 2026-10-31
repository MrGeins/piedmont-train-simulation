"""Structural validation for external infrastructure configuration."""
from __future__ import annotations
from typing import Any


class InfrastructureConfigError(ValueError):
    """Raised when infrastructure data is inconsistent or incomplete."""


def validate_infrastructure(data: Any, source: str = "infrastructure config") -> None:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise InfrastructureConfigError(f"{source}: root must be a JSON object")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for section in ("stations", "topology", "links"):
        expected = list if section == "links" else dict
        if not isinstance(data.get(section), expected):
            errors.append(f"{section} must be a {'list' if section == 'links' else 'object'}")
    if errors:
        raise InfrastructureConfigError(f"{source}: " + "; ".join(errors))

    stations, topology, links = data["stations"], data["topology"], data["links"]
    if not stations:
        errors.append("stations must not be empty")
    if not topology:
        errors.append("topology must not be empty")
    for key, station in stations.items():
        prefix = f"stations.{key}"
        if not isinstance(station, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("name", "roro_station", "default_dwell", "terminal", "num_tracks", "available_tracks", "stub_tracks"):
            if field not in station:
                errors.append(f"{prefix}.{field} is required")
        if not isinstance(station.get("name"), str) or not station.get("name", "").strip():
            errors.append(f"{prefix}.name must be a non-empty string")
        for field in ("roro_station", "terminal"):
            if field in station and not isinstance(station[field], bool):
                errors.append(f"{prefix}.{field} must be boolean")
        dwell = station.get("default_dwell")
        if isinstance(dwell, bool) or not isinstance(dwell, (int, float)) or dwell < 0:
            errors.append(f"{prefix}.default_dwell must be a non-negative number")
        count = station.get("num_tracks")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            errors.append(f"{prefix}.num_tracks must be a positive integer")
            count = None
        available = station.get("available_tracks")
        if not isinstance(available, list) or not available:
            errors.append(f"{prefix}.available_tracks must be a non-empty list")
            safe_tracks = []
        else:
            safe_tracks = available
            if any(isinstance(track, bool) or not isinstance(track, int) or track < 1 or (count is not None and track > count) for track in available):
                errors.append(f"{prefix}.available_tracks contains a track outside 1..num_tracks")
            if len(set(available)) != len(available):
                errors.append(f"{prefix}.available_tracks contains duplicates")
        stubs = station.get("stub_tracks")
        if not isinstance(stubs, dict):
            errors.append(f"{prefix}.stub_tracks must be an object mapping track numbers to directions")
        else:
            for track, direction in stubs.items():
                try:
                    track_num = int(track)
                except (TypeError, ValueError):
                    errors.append(f"{prefix}.stub_tracks key {track!r} is not a track number")
                    continue
                if not isinstance(direction, str) or not direction:
                    errors.append(f"{prefix}.stub_tracks[{track!r}] must have a direction")
                if track_num not in safe_tracks:
                    errors.append(f"{prefix}.stub_tracks track {track_num} is not in available_tracks")
        if key not in topology:
            errors.append(f"{prefix} has no matching topology entry")

    for key, node in topology.items():
        prefix = f"topology.{key}"
        if not isinstance(node, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("name", "x", "y", "display_label"):
            if field not in node:
                errors.append(f"{prefix}.{field} is required")
        if not isinstance(node.get("name"), str) or not node.get("name", "").strip():
            errors.append(f"{prefix}.name must be a non-empty string")
        for field in ("x", "y"):
            if isinstance(node.get(field), bool) or not isinstance(node.get(field), int):
                errors.append(f"{prefix}.{field} must be an integer")
        if "display_label" in node and not isinstance(node["display_label"], bool):
            errors.append(f"{prefix}.display_label must be boolean")

    seen_edges: set[tuple[str, str]] = set()
    for index, link in enumerate(links):
        prefix = f"links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        start, end = link.get("from"), link.get("to")
        if not isinstance(start, str) or start not in topology:
            errors.append(f"{prefix}.from references unknown topology node {start!r}")
        if not isinstance(end, str) or end not in topology:
            errors.append(f"{prefix}.to references unknown topology node {end!r}")
        if start == end:
            errors.append(f"{prefix} cannot connect a node to itself ({start!r})")
        if not isinstance(link.get("double_track"), bool):
            errors.append(f"{prefix}.double_track must be boolean")
        for field in ("distance_km", "speed_limit_kmh"):
            if field in link and (
                isinstance(link[field], bool)
                or not isinstance(link[field], (int, float))
                or link[field] <= 0
            ):
                errors.append(f"{prefix}.{field} must be a positive number when provided")
        if "gradient_permille" in link and (
            isinstance(link["gradient_permille"], bool)
            or not isinstance(link["gradient_permille"], (int, float))
        ):
            errors.append(f"{prefix}.gradient_permille must be a number when provided")
        if "electrified" in link and not isinstance(link["electrified"], bool):
            errors.append(f"{prefix}.electrified must be boolean when provided")
        if "track_type" in link and (
            not isinstance(link["track_type"], str) or not link["track_type"].strip()
        ):
            errors.append(f"{prefix}.track_type must be a non-empty string when provided")
        if isinstance(start, str) and isinstance(end, str) and start != end:
            edge = tuple(sorted((start, end)))
            if edge in seen_edges:
                errors.append(f"{prefix} duplicates undirected link {edge[0]}--{edge[1]}")
            seen_edges.add(edge)
    if errors:
        raise InfrastructureConfigError(f"{source}: validation failed:\n- " + "\n- ".join(errors))
