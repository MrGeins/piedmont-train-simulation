"""Intermediate distributed-command pneumatic service-brake simulation.

This is not a compressible-flow solver. It models a travelling command front,
local brake-pipe pressure response, individual cylinder filling and
per-vehicle brake-force development.
"""

from __future__ import annotations
from dataclasses import dataclass
from math import exp, isfinite
from typing import Tuple

from backend.railway.braking.brake_cylinder import BrakeCylinderModel


def _positive(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _non_negative(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


@dataclass(frozen=True)
class BrakePipeModel:
    """Travelling pressure-reduction front with local first-order response."""

    propagation_speed_mps: float
    pressure_response_time_constant_seconds: float
    full_service_pressure_reduction_kpa: float

    def __post_init__(self) -> None:
        _positive("propagation_speed_mps", self.propagation_speed_mps)
        _positive("pressure_response_time_constant_seconds", self.pressure_response_time_constant_seconds)
        _positive("full_service_pressure_reduction_kpa", self.full_service_pressure_reduction_kpa)

    def pressure_reduction_kpa(self, position_m: float, elapsed_seconds: float) -> float:
        _non_negative("position_m", position_m)
        _non_negative("elapsed_seconds", elapsed_seconds)
        local_elapsed = elapsed_seconds - position_m / self.propagation_speed_mps
        if local_elapsed <= 0:
            return 0.0
        return self.full_service_pressure_reduction_kpa * (
            1.0 - exp(-local_elapsed / self.pressure_response_time_constant_seconds)
        )


@dataclass(frozen=True)
class BrakeVehicle:
    """One vehicle, ordered from the brake-command source."""

    vehicle_id: str
    position_m: float
    mass_kg: float
    maximum_brake_force_n: float
    brake_cylinder: BrakeCylinderModel

    def __post_init__(self) -> None:
        if not isinstance(self.vehicle_id, str) or not self.vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string")
        _non_negative("position_m", self.position_m)
        _positive("mass_kg", self.mass_kg)
        _positive("maximum_brake_force_n", self.maximum_brake_force_n)
        if not isinstance(self.brake_cylinder, BrakeCylinderModel):
            raise ValueError("brake_cylinder must be a BrakeCylinderModel")


@dataclass(frozen=True)
class BrakeFormation:
    """Ordered complete formation and shared brake-pipe model."""

    vehicles: Tuple[BrakeVehicle, ...]
    brake_pipe: BrakePipeModel

    def __post_init__(self) -> None:
        if not isinstance(self.vehicles, tuple) or not self.vehicles:
            raise ValueError("vehicles must be a non-empty tuple")
        if not all(isinstance(item, BrakeVehicle) for item in self.vehicles):
            raise ValueError("vehicles must contain BrakeVehicle values")
        ids = [item.vehicle_id for item in self.vehicles]
        if len(ids) != len(set(ids)):
            raise ValueError("vehicle_id values must be unique")
        positions = [item.position_m for item in self.vehicles]
        if positions[0] != 0:
            raise ValueError("the first vehicle position must be 0 m at the command source")
        if any(right < left for left, right in zip(positions, positions[1:])):
            raise ValueError("vehicles must be ordered by non-decreasing position")
        if not isinstance(self.brake_pipe, BrakePipeModel):
            raise ValueError("brake_pipe must be a BrakePipeModel")

    @property
    def total_mass_kg(self) -> float:
        return sum(vehicle.mass_kg for vehicle in self.vehicles)


@dataclass(frozen=True)
class BrakeSimulationSample:
    time_seconds: float
    distance_m: float
    speed_mps: float
    brake_force_n: float
    deceleration_mps2: float
    cylinder_pressures_kpa: Tuple[float, ...]


@dataclass(frozen=True)
class BrakeSimulationResult:
    stopping_time_seconds: float
    stopping_distance_m: float
    initial_speed_mps: float
    final_speed_mps: float
    peak_brake_force_n: float
    samples: Tuple[BrakeSimulationSample, ...]


class BrakeSimulation:
    """Integrate service-braking response for every vehicle in a formation."""

    _GRAVITY_MPS2 = 9.80665

    def simulate_service_braking(
        self,
        formation: BrakeFormation,
        initial_speed_mps: float,
        gradient_permille: float = 0.0,
        time_step_seconds: float = 0.05,
        max_duration_seconds: float = 600.0,
    ) -> BrakeSimulationResult:
        if not isinstance(formation, BrakeFormation):
            raise ValueError("formation must be a BrakeFormation")
        _positive("initial_speed_mps", initial_speed_mps)
        _positive("time_step_seconds", time_step_seconds)
        _positive("max_duration_seconds", max_duration_seconds)
        if isinstance(gradient_permille, bool) or not isinstance(gradient_permille, (int, float)) or not isfinite(gradient_permille):
            raise ValueError("gradient_permille must be a finite number")

        vehicles = formation.vehicles
        pressures = [0.0 for _ in vehicles]
        total_mass = formation.total_mass_kg
        maximum_force = sum(vehicle.maximum_brake_force_n for vehicle in vehicles)
        grade_acceleration = self._GRAVITY_MPS2 * gradient_permille / 1000.0
        if maximum_force / total_mass + grade_acceleration <= 0:
            raise ValueError("maximum service braking cannot overcome the downhill gradient")

        time_seconds = 0.0
        distance_m = 0.0
        speed_mps = float(initial_speed_mps)
        peak_force = 0.0
        samples = []

        while speed_mps > 0 and time_seconds < max_duration_seconds:
            elapsed = min(time_step_seconds, max_duration_seconds - time_seconds)
            next_time = time_seconds + elapsed
            total_force = 0.0
            next_pressures = []

            for index, vehicle in enumerate(vehicles):
                pipe_reduction = formation.brake_pipe.pressure_reduction_kpa(
                    vehicle.position_m, next_time
                )
                target_pressure = vehicle.brake_cylinder.target_pressure_kpa(
                    pipe_reduction, formation.brake_pipe.full_service_pressure_reduction_kpa
                )
                pressure = vehicle.brake_cylinder.pressure_after(
                    pressures[index], target_pressure, elapsed
                )
                next_pressures.append(pressure)
                total_force += vehicle.maximum_brake_force_n * (
                    pressure / vehicle.brake_cylinder.maximum_pressure_kpa
                )

            deceleration = total_force / total_mass + grade_acceleration
            actual_elapsed = min(elapsed, speed_mps / deceleration) if deceleration > 0 else elapsed
            next_speed = max(0.0, speed_mps - deceleration * actual_elapsed)
            distance_m += (speed_mps + next_speed) * 0.5 * actual_elapsed
            time_seconds += actual_elapsed
            pressures = next_pressures
            speed_mps = next_speed
            peak_force = max(peak_force, total_force)
            samples.append(BrakeSimulationSample(
                time_seconds, distance_m, speed_mps, total_force, deceleration, tuple(pressures)
            ))

        if speed_mps > 0:
            raise RuntimeError("braking simulation exceeded max_duration_seconds before stopping")

        return BrakeSimulationResult(
            time_seconds, distance_m, float(initial_speed_mps), speed_mps, peak_force,
            tuple(samples),
        )
