"""Rolling-stock performance parameters used by the running-time model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VehiclePerformance:
    """Physical performance envelope for one rolling-stock type.

    Values are SI-compatible inputs: km/h, m/s² and seconds. They must come
    from a documented vehicle profile; this class deliberately supplies no
    invented SFM fleet defaults.
    """

    max_speed_kmh: float
    acceleration_mps2: float
    service_braking_mps2: float
    minimum_turnback_seconds: int = 90

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
