"""Rolling-stock performance parameters used by the running-time model."""

from dataclasses import dataclass
from math import isfinite


def _positive_number(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _non_negative_number(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


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
                or not isfinite(value)
                or value < 0
                or (name == "acceleration_mps2" and value == 0)
            ):
                raise ValueError(
                    f"{name} must be a positive number"
                    if name == "acceleration_mps2"
                    else f"{name} must be non-negative"
                )


@dataclass(frozen=True)
class DavisResistance:
    """Davis resistance coefficients in SI units.

    Resistance_N = A_N + B_N_per_mps * speed_mps
                   + C_N_per_mps2 * speed_mps**2.
    """

    A_N: float
    B_N_per_mps: float
    C_N_per_mps2: float

    def __post_init__(self) -> None:
        for name in ("A_N", "B_N_per_mps", "C_N_per_mps2"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0
            ):
                raise ValueError(f"{name} must be a finite non-negative number")
        if self.A_N == self.B_N_per_mps == self.C_N_per_mps2 == 0:
            raise ValueError("at least one Davis resistance coefficient must be positive")

    def force_n(self, speed_mps: float) -> float:
        if not isfinite(speed_mps) or speed_mps < 0:
            raise ValueError("speed_mps must be finite and non-negative")
        return (
            self.A_N
            + self.B_N_per_mps * speed_mps
            + self.C_N_per_mps2 * speed_mps * speed_mps
        )


@dataclass(frozen=True)
class TractionModel:
    """Longitudinal traction model for one complete train formation."""

    mass_kg: float
    max_tractive_effort_n: float
    max_power_w: float
    resistance: DavisResistance

    def __post_init__(self) -> None:
        _positive_number("mass_kg", self.mass_kg)
        _positive_number("max_tractive_effort_n", self.max_tractive_effort_n)
        _positive_number("max_power_w", self.max_power_w)
        if not isinstance(self.resistance, DavisResistance):
            raise ValueError("resistance must be a DavisResistance instance")

    def tractive_effort_n(self, speed_mps: float) -> float:
        if not isfinite(speed_mps) or speed_mps < 0:
            raise ValueError("speed_mps must be finite and non-negative")
        if speed_mps == 0:
            return float(self.max_tractive_effort_n)
        return min(
            float(self.max_tractive_effort_n),
            float(self.max_power_w) / speed_mps,
        )

    def acceleration_mps2(self, speed_mps: float) -> float:
        net_force = self.tractive_effort_n(speed_mps) - self.resistance.force_n(speed_mps)
        return net_force / float(self.mass_kg)


@dataclass(frozen=True)
class VehiclePerformance:
    """Physical performance envelope for one rolling-stock type.

    brake_propagation_delay_seconds represents the delay before the model
    applies full service braking. It defaults to zero until verified data
    exists for the exact train formation.
    """

    max_speed_kmh: float
    acceleration_mps2: float
    service_braking_mps2: float
    minimum_turnback_seconds: int = 90
    acceleration_curve: tuple[AccelerationPoint, ...] = ()
    traction_model: TractionModel | None = None
    brake_propagation_delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        for name in ("max_speed_kmh", "acceleration_mps2", "service_braking_mps2"):
            _positive_number(name, getattr(self, name))
        if (
            isinstance(self.minimum_turnback_seconds, bool)
            or not isinstance(self.minimum_turnback_seconds, int)
            or self.minimum_turnback_seconds < 0
        ):
            raise ValueError("minimum_turnback_seconds must be a non-negative integer")
        _non_negative_number(
            "brake_propagation_delay_seconds", self.brake_propagation_delay_seconds
        )

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

        if self.traction_model is not None:
            if not isinstance(self.traction_model, TractionModel):
                raise ValueError("traction_model must be a TractionModel instance")
            if self.acceleration_curve:
                raise ValueError(
                    "acceleration_curve and traction_model are alternative models; configure only one"
                )
