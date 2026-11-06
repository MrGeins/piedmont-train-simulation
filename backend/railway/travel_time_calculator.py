"""Calculate segment running times from infrastructure and vehicle physics."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, inf, isfinite
from typing import Iterable

from backend.railway.vehicle_performance import VehiclePerformance


class MissingOperationalDataError(ValueError):
    """Raised when a segment lacks measured/configured operational attributes."""


@dataclass(frozen=True)
class SegmentPerformance:
    distance_km: float
    speed_limit_kmh: float
    gradient_permille: float = 0.0

    def __post_init__(self) -> None:
        for field_name in ("distance_km", "speed_limit_kmh"):
            value = getattr(self, field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value <= 0
            ):
                raise ValueError(f"{field_name} must be a finite positive number")
        if (
            isinstance(self.gradient_permille, bool)
            or not isinstance(self.gradient_permille, (int, float))
            or not isfinite(self.gradient_permille)
        ):
            raise ValueError("gradient_permille must be a finite number")


class TravelTimeCalculator:
    """Calculate accelerate-cruise-brake running times.

    Gradient is signed in the direction of travel: positive is uphill and
    negative is downhill. Brake propagation delay is represented as a
    constant-speed interval before full service braking takes effect.
    """

    _SPEED_INTEGRATION_STEP_MPS = 0.25
    _PEAK_SPEED_SOLVER_ITERATIONS = 60
    _GRAVITY_MPS2 = 9.80665

    @classmethod
    def _grade_acceleration(cls, gradient_permille: float) -> float:
        # Railway gradients are small; permille is converted to a signed
        # longitudinal gravity component using the small-angle approximation.
        return cls._GRAVITY_MPS2 * gradient_permille / 1000.0

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

    def _integrate_acceleration(
        self, peak_speed_mps: float, acceleration_at_speed
    ) -> tuple[float, float]:
        if peak_speed_mps <= 0:
            return 0.0, 0.0
        steps = max(1, ceil(peak_speed_mps / self._SPEED_INTEGRATION_STEP_MPS))
        delta_speed = peak_speed_mps / steps
        distance_m = 0.0
        time_seconds = 0.0
        for index in range(steps):
            speed_start = index * delta_speed
            speed_end = (index + 1) * delta_speed
            acceleration = acceleration_at_speed((speed_start + speed_end) / 2.0)
            if acceleration <= 0 or not isfinite(acceleration):
                return inf, inf
            distance_m += (speed_end * speed_end - speed_start * speed_start) / (
                2.0 * acceleration
            )
            time_seconds += delta_speed / acceleration
        return distance_m, time_seconds

    def _profile_acceleration_distance_time(
        self, peak_speed_mps: float, vehicle: VehiclePerformance, grade_acceleration: float
    ) -> tuple[float, float]:
        return self._integrate_acceleration(
            peak_speed_mps,
            lambda speed: self._acceleration_at_speed(vehicle, speed) - grade_acceleration,
        )

    def _traction_acceleration_distance_time(
        self, peak_speed_mps: float, vehicle: VehiclePerformance, grade_acceleration: float
    ) -> tuple[float, float]:
        model = vehicle.traction_model
        if model is None:
            raise ValueError("traction model is not configured")
        return self._integrate_acceleration(
            peak_speed_mps,
            lambda speed: model.acceleration_mps2(speed) - grade_acceleration,
        )

    def _constant_acceleration_distance_time(
        self, peak_speed_mps: float, vehicle: VehiclePerformance, grade_acceleration: float
    ) -> tuple[float, float]:
        acceleration = float(vehicle.acceleration_mps2) - grade_acceleration
        return self._integrate_acceleration(peak_speed_mps, lambda _speed: acceleration)

    def _maximum_sustainable_speed(
        self, speed_cap_mps: float, vehicle: VehiclePerformance, grade_acceleration: float
    ) -> float:
        model = vehicle.traction_model
        if model is None:
            raise ValueError("traction model is not configured")

        def net_acceleration(speed: float) -> float:
            return model.acceleration_mps2(speed) - grade_acceleration

        if net_acceleration(0.0) <= 0:
            raise ValueError("tractive effort does not overcome resistance and gradient at standstill")
        if net_acceleration(speed_cap_mps) > 0:
            return speed_cap_mps
        low, high = 0.0, speed_cap_mps
        for _ in range(self._PEAK_SPEED_SOLVER_ITERATIONS):
            midpoint = (low + high) / 2.0
            if net_acceleration(midpoint) > 0:
                low = midpoint
            else:
                high = midpoint
        return low * (1.0 - 1e-6)

    def _calculate_dynamic_segment_seconds(
        self,
        distance_m: float,
        speed_cap_mps: float,
        vehicle: VehiclePerformance,
        acceleration_distance_time,
        grade_acceleration: float,
    ) -> float:
        braking = float(vehicle.service_braking_mps2) + grade_acceleration
        if braking <= 0:
            raise ValueError("service braking cannot overcome the downhill gradient")

        acceleration_distance, acceleration_time = acceleration_distance_time(
            speed_cap_mps, vehicle, grade_acceleration
        )
        if acceleration_distance == inf:
            raise ValueError("vehicle cannot accelerate to the requested speed")

        brake_delay = float(vehicle.brake_propagation_delay_seconds)
        brake_delay_distance = speed_cap_mps * brake_delay
        braking_distance = speed_cap_mps * speed_cap_mps / (2.0 * braking)
        if acceleration_distance + brake_delay_distance + braking_distance <= distance_m:
            cruise_distance = (
                distance_m - acceleration_distance - brake_delay_distance - braking_distance
            )
            return (
                acceleration_time
                + cruise_distance / speed_cap_mps
                + brake_delay
                + speed_cap_mps / braking
            )

        low, high = 0.0, speed_cap_mps
        for _ in range(self._PEAK_SPEED_SOLVER_ITERATIONS):
            peak = (low + high) / 2.0
            peak_distance, _ = acceleration_distance_time(peak, vehicle, grade_acceleration)
            delay_distance = peak * brake_delay
            peak_braking_distance = peak * peak / (2.0 * braking)
            if peak_distance + delay_distance + peak_braking_distance > distance_m:
                high = peak
            else:
                low = peak

        peak_speed = (low + high) / 2.0
        _, acceleration_time = acceleration_distance_time(
            peak_speed, vehicle, grade_acceleration
        )
        return acceleration_time + brake_delay + peak_speed / braking

    def calculate_segment_minutes(
        self,
        segment: SegmentPerformance,
        vehicle: VehiclePerformance,
    ) -> float:
        distance_m = segment.distance_km * 1000.0
        speed_cap = min(float(segment.speed_limit_kmh), float(vehicle.max_speed_kmh)) / 3.6
        grade_acceleration = self._grade_acceleration(segment.gradient_permille)

        if vehicle.traction_model is not None:
            sustainable_speed = self._maximum_sustainable_speed(
                speed_cap, vehicle, grade_acceleration
            )
            total_seconds = self._calculate_dynamic_segment_seconds(
                distance_m,
                sustainable_speed,
                vehicle,
                self._traction_acceleration_distance_time,
                grade_acceleration,
            )
        elif vehicle.acceleration_curve:
            total_seconds = self._calculate_dynamic_segment_seconds(
                distance_m,
                speed_cap,
                vehicle,
                self._profile_acceleration_distance_time,
                grade_acceleration,
            )
        else:
            total_seconds = self._calculate_dynamic_segment_seconds(
                distance_m,
                speed_cap,
                vehicle,
                self._constant_acceleration_distance_time,
                grade_acceleration,
            )
        return total_seconds / 60.0

    def calculate_path_minutes(
        self,
        path: Iterable[str],
        infrastructure_network: Iterable[object],
        vehicle: VehiclePerformance,
    ) -> float:
        """Sum directional segment times; link gradients follow from -> to."""
        nodes = list(path)
        if len(nodes) < 2:
            return 0.0

        edge_data: dict[frozenset[str], tuple[object, SegmentPerformance]] = {}
        for link in infrastructure_network:
            distance = getattr(link, "distance_km", None)
            speed_limit = getattr(link, "speed_limit_kmh", None)
            edge = frozenset((link.node_from, link.node_to))
            if distance is not None and speed_limit is not None:
                edge_data[edge] = (
                    link,
                    SegmentPerformance(
                        distance,
                        speed_limit,
                        getattr(link, "gradient_permille", None) or 0.0,
                    ),
                )

        total_minutes = 0.0
        for start, end in zip(nodes, nodes[1:]):
            entry = edge_data.get(frozenset((start, end)))
            if entry is None:
                raise MissingOperationalDataError(
                    f"Missing distance_km or speed_limit_kmh for infrastructure link {start}--{end}"
                )
            link, segment = entry
            gradient = segment.gradient_permille
            if start == link.node_to and end == link.node_from:
                gradient = -gradient
            directional_segment = SegmentPerformance(
                segment.distance_km, segment.speed_limit_kmh, gradient
            )
            total_minutes += self.calculate_segment_minutes(directional_segment, vehicle)
        return total_minutes
