"""Calculate segment running times from infrastructure and vehicle physics."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
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
    """Calculate accelerate-cruise-brake running times.

    The default path retains the constant-acceleration kinematic model. An
    explicitly supplied vehicle acceleration curve enables numerical
    integration over speed, with linear interpolation between documented
    knots. Neither path models gradients, resistance, signals or temporary
    speed restrictions.
    """

    _SPEED_INTEGRATION_STEP_MPS = 0.25
    _PEAK_SPEED_SOLVER_ITERATIONS = 60

    @staticmethod
    def _acceleration_at_speed(vehicle: VehiclePerformance, speed_mps: float) -> float:
        speed_kmh = speed_mps * 3.6
        curve = vehicle.acceleration_curve
        for left, right in zip(curve, curve[1:]):
            if speed_kmh <= right.speed_kmh:
                ratio = (speed_kmh - left.speed_kmh) / (right.speed_kmh - left.speed_kmh)
                return left.acceleration_mps2 + ratio * (
                    right.acceleration_mps2 - left.acceleration_mps2
                )
        return curve[-1].acceleration_mps2

    def _profile_acceleration_distance_time(
        self, peak_speed_mps: float, vehicle: VehiclePerformance
    ) -> tuple[float, float]:
        """Integrate acceleration distance/time using small speed increments."""
        if peak_speed_mps <= 0:
            return 0.0, 0.0

        steps = max(1, ceil(peak_speed_mps / self._SPEED_INTEGRATION_STEP_MPS))
        delta_speed = peak_speed_mps / steps
        distance_m = 0.0
        time_seconds = 0.0

        for index in range(steps):
            speed_start = index * delta_speed
            speed_end = (index + 1) * delta_speed
            acceleration = self._acceleration_at_speed(
                vehicle, (speed_start + speed_end) / 2.0
            )
            distance_m += (speed_end * speed_end - speed_start * speed_start) / (
                2.0 * acceleration
            )
            time_seconds += delta_speed / acceleration

        return distance_m, time_seconds

    def _calculate_profile_segment_seconds(
        self, distance_m: float, speed_cap_mps: float, vehicle: VehiclePerformance
    ) -> float:
        braking = float(vehicle.service_braking_mps2)
        acceleration_distance, acceleration_time = self._profile_acceleration_distance_time(
            speed_cap_mps, vehicle
        )
        braking_distance = speed_cap_mps * speed_cap_mps / (2.0 * braking)

        if acceleration_distance + braking_distance <= distance_m:
            cruise_distance = distance_m - acceleration_distance - braking_distance
            return (
                acceleration_time
                + cruise_distance / speed_cap_mps
                + speed_cap_mps / braking
            )

        # The segment is too short to reach the speed cap. Solve the peak
        # speed for which acceleration and service-braking distances sum to
        # the segment length.
        low, high = 0.0, speed_cap_mps
        for _ in range(self._PEAK_SPEED_SOLVER_ITERATIONS):
            peak = (low + high) / 2.0
            peak_distance, _ = self._profile_acceleration_distance_time(peak, vehicle)
            peak_braking_distance = peak * peak / (2.0 * braking)
            if peak_distance + peak_braking_distance > distance_m:
                high = peak
            else:
                low = peak

        peak_speed = (low + high) / 2.0
        _, acceleration_time = self._profile_acceleration_distance_time(peak_speed, vehicle)
        return acceleration_time + peak_speed / braking

    def calculate_segment_minutes(
        self,
        segment: SegmentPerformance,
        vehicle: VehiclePerformance,
    ) -> float:
        distance_m = segment.distance_km * 1000.0
        speed_cap = min(float(segment.speed_limit_kmh), float(vehicle.max_speed_kmh)) / 3.6

        if vehicle.acceleration_curve:
            total_seconds = self._calculate_profile_segment_seconds(
                distance_m, speed_cap, vehicle
            )
            return total_seconds / 60.0

        acceleration = float(vehicle.acceleration_mps2)
        braking = float(vehicle.service_braking_mps2)
        accel_distance_at_cap = speed_cap * speed_cap / (2.0 * acceleration)
        brake_distance_at_cap = speed_cap * speed_cap / (2.0 * braking)

        if accel_distance_at_cap + brake_distance_at_cap >= distance_m:
            peak_speed = (
                2.0 * distance_m / (1.0 / acceleration + 1.0 / braking)
            ) ** 0.5
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
