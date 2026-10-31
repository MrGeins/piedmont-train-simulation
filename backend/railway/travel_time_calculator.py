"""Calculate segment running times from infrastructure and vehicle physics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.railway.vehicle_performance import VehiclePerformance


class MissingOperationalDataError(ValueError):
    """Raised when a segment lacks measured/configured operational attributes."""


@dataclass(frozen=True)
class SegmentPerformance:
    distance_km: float
    speed_limit_kmh: float

    def __post_init__(self) -> None:
        for field_name in ("distance_km", "speed_limit_kmh"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{field_name} must be a positive number")


class TravelTimeCalculator:
    """Compute a simplified accelerate-cruise-brake running time.

    This is a kinematic model, not a full railway dynamics simulator. It
    assumes constant acceleration and service braking, with no gradients,
    curves, signal checks or temporary speed restrictions. Those effects can
    be added as further infrastructure constraints when their data is known.
    """

    def calculate_segment_minutes(
        self,
        segment: SegmentPerformance,
        vehicle: VehiclePerformance,
    ) -> float:
        distance_m = segment.distance_km * 1000.0
        acceleration = float(vehicle.acceleration_mps2)
        braking = float(vehicle.service_braking_mps2)
        speed_cap = min(float(segment.speed_limit_kmh), float(vehicle.max_speed_kmh)) / 3.6

        accel_distance_at_cap = speed_cap * speed_cap / (2.0 * acceleration)
        brake_distance_at_cap = speed_cap * speed_cap / (2.0 * braking)

        if accel_distance_at_cap + brake_distance_at_cap >= distance_m:
            peak_speed = (2.0 * distance_m / (1.0 / acceleration + 1.0 / braking)) ** 0.5
            acceleration_time = peak_speed / acceleration
            braking_time = peak_speed / braking
            total_seconds = acceleration_time + braking_time
        else:
            acceleration_time = speed_cap / acceleration
            braking_time = speed_cap / braking
            cruise_distance = distance_m - accel_distance_at_cap - brake_distance_at_cap
            total_seconds = acceleration_time + cruise_distance / speed_cap + braking_time

        return total_seconds / 60.0

    def calculate_path_minutes(
        self,
        path: Iterable[str],
        infrastructure_network: Iterable[object],
        vehicle: VehiclePerformance,
    ) -> float:
        """Sum segment times along a path, failing if any edge lacks data."""
        nodes = list(path)
        if len(nodes) < 2:
            return 0.0

        edge_data: dict[frozenset[str], SegmentPerformance] = {}
        for link in infrastructure_network:
            distance = getattr(link, "distance_km", None)
            speed_limit = getattr(link, "speed_limit_kmh", None)
            edge = frozenset((link.node_from, link.node_to))
            if distance is not None and speed_limit is not None:
                edge_data[edge] = SegmentPerformance(distance, speed_limit)

        total_minutes = 0.0
        for start, end in zip(nodes, nodes[1:]):
            segment = edge_data.get(frozenset((start, end)))
            if segment is None:
                raise MissingOperationalDataError(
                    f"Missing distance_km or speed_limit_kmh for infrastructure link {start}--{end}"
                )
            total_minutes += self.calculate_segment_minutes(segment, vehicle)
        return total_minutes
