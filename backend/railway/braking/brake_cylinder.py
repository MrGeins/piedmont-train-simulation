"""First-order brake-cylinder pressure response."""

from __future__ import annotations
from dataclasses import dataclass
from math import exp, isfinite


def _positive(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _non_negative(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


@dataclass(frozen=True)
class BrakeCylinderModel:
    """Cylinder model with explicit maximum pressure and fill time constant."""

    maximum_pressure_kpa: float
    fill_time_constant_seconds: float

    def __post_init__(self) -> None:
        _positive("maximum_pressure_kpa", self.maximum_pressure_kpa)
        _positive("fill_time_constant_seconds", self.fill_time_constant_seconds)

    def target_pressure_kpa(
        self, brake_pipe_reduction_kpa: float, full_service_pressure_reduction_kpa: float
    ) -> float:
        _non_negative("brake_pipe_reduction_kpa", brake_pipe_reduction_kpa)
        _positive("full_service_pressure_reduction_kpa", full_service_pressure_reduction_kpa)
        demand = min(1.0, brake_pipe_reduction_kpa / full_service_pressure_reduction_kpa)
        return self.maximum_pressure_kpa * demand

    def pressure_after(
        self, current_pressure_kpa: float, target_pressure_kpa: float, elapsed_seconds: float
    ) -> float:
        """Return pressure after an exact first-order response interval."""
        _non_negative("current_pressure_kpa", current_pressure_kpa)
        _non_negative("target_pressure_kpa", target_pressure_kpa)
        _non_negative("elapsed_seconds", elapsed_seconds)
        if current_pressure_kpa > self.maximum_pressure_kpa:
            raise ValueError("current_pressure_kpa exceeds cylinder maximum")
        if target_pressure_kpa > self.maximum_pressure_kpa:
            raise ValueError("target_pressure_kpa exceeds cylinder maximum")
        if elapsed_seconds == 0:
            return float(current_pressure_kpa)
        fraction = 1.0 - exp(-elapsed_seconds / self.fill_time_constant_seconds)
        return current_pressure_kpa + (target_pressure_kpa - current_pressure_kpa) * fraction
