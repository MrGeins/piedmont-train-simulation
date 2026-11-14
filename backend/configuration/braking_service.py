"""Explicit entry point for simulations using configured brake formations."""
from __future__ import annotations

from pathlib import Path

from backend.configuration.braking_loader import load_brake_formations
from backend.railway.braking import BrakeSimulation, BrakeSimulationResult


class UnknownBrakeFormationError(LookupError):
    """Raised when a requested formation is absent from the active config."""


class ConfiguredBrakingService:
    """Run pneumatic braking only for a formation explicitly selected by ID.

    This service is intentionally not wired into TravelTimeCalculator. An
    empty configuration exposes no selectable formations and never falls
    back to guessed physical values.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        simulator: BrakeSimulation | None = None,
    ) -> None:
        self._formations = load_brake_formations(config_path)
        self._simulator = simulator if simulator is not None else BrakeSimulation()

    @property
    def available_formations(self) -> tuple[str, ...]:
        """Return configured formation IDs in file order."""
        return tuple(self._formations)

    def simulate_service_braking(
        self,
        formation_id: str,
        initial_speed_mps: float,
        gradient_permille: float = 0.0,
        time_step_seconds: float = 0.05,
        max_duration_seconds: float = 600.0,
    ) -> BrakeSimulationResult:
        """Simulate braking for one explicitly selected configured formation."""
        if not isinstance(formation_id, str) or not formation_id.strip():
            raise ValueError("formation_id must be a non-empty string")
        try:
            formation = self._formations[formation_id]
        except KeyError as exc:
            raise UnknownBrakeFormationError(
                f"Brake formation '{formation_id}' is not present in the active configuration; "
                f"available formations: {', '.join(self.available_formations) or '(none)'}"
            ) from exc
        return self._simulator.simulate_service_braking(
            formation,
            initial_speed_mps,
            gradient_permille=gradient_permille,
            time_step_seconds=time_step_seconds,
            max_duration_seconds=max_duration_seconds,
        )
