"""Rolling-stock performance parameters used by the running-time model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccelerationPoint:
    """A documented acceleration value at a vehicle speed."""

    speed_kmh: float
    acceleration_mps2: float

    def __post_init__(self) -> None:
        for name in ("speed_kmh", "acceleration_mps2"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                or (name == "acceleration_mps2" and value == 0)
            ):
                raise ValueError(
                    f"{name} must be a positive number"
                    if name == "acceleration_mps2"
                    else f"{name} must be non-negative"
                )


@dataclass(frozen=True)
class VehiclePerformance:
    """Physical performance envelope for one rolling-stock type.

    Values are SI-compatible inputs: km/h, m/s² and seconds. They must come
    from a documented vehicle profile; this class deliberately supplies no
    invented SFM fleet defaults.

    acceleration_curve is optional. When supplied, it contains explicit
    speed/acceleration knots from 0 km/h through at least max_speed_kmh.
    The running-time model linearly interpolates between those knots. No
    curve is inferred from the rolling-stock reference-candidate dataset.
    """

    max_speed_kmh: float
    acceleration_mps2: float
    service_braking_mps2: float
    minimum_turnback_seconds: int = 90
    acceleration_curve: tuple[AccelerationPoint, ...] = ()

    def __post_init__(self) -> None:
        for name in ("max_speed_kmh", "acceleration_mps2", "service_braking_mps2"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{name} must be a positive number")
        if (
            isinstance(self.minimum_turnback_seconds, bool)
            or not isinstance(self.minimum_turnback_seconds, int)
            or self.minimum_turnback_seconds < 0
        ):
            raise ValueError("minimum_turnback_seconds must be a non-negative integer")

        if not isinstance(self.acceleration_curve, tuple):
            raise ValueError("acceleration_curve must be a tuple of AccelerationPoint values")
        if self.acceleration_curve:
            if not all(isinstance(point, AccelerationPoint) for point in self.acceleration_curve):
                raise ValueError("acceleration_curve entries must be AccelerationPoint values")
            speeds = [point.speed_kmh for point in self.acceleration_curve]
            if speeds[0] != 0:
                raise ValueError("acceleration_curve must start at 0 km/h")
            if any(right <= left for left, right in zip(speeds, speeds[1:])):
                raise ValueError("acceleration_curve speeds must be strictly increasing")
            if speeds[-1] < self.max_speed_kmh:
                raise ValueError("acceleration_curve must cover max_speed_kmh")
