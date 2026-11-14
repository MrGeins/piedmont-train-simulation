import json
import tempfile
import unittest
from pathlib import Path

from backend.configuration.braking_service import (
    ConfiguredBrakingService,
    UnknownBrakeFormationError,
)
from backend.railway.travel_time_calculator import SegmentPerformance, TravelTimeCalculator
from backend.railway.vehicle_performance import VehiclePerformance


def formation_config():
    return {
        "schema_version": 1,
        "formations": [{
            "formation_id": "TEST_2_CAR",
            "brake_pipe": {
                "propagation_speed_mps": 200.0,
                "pressure_response_time_constant_seconds": 0.5,
                "full_service_pressure_reduction_kpa": 150.0,
            },
            "vehicles": [
                {
                    "vehicle_id": "CAR_1",
                    "position_m": 0.0,
                    "mass_kg": 40000.0,
                    "maximum_brake_force_n": 100000.0,
                    "brake_cylinder": {
                        "maximum_pressure_kpa": 380.0,
                        "fill_time_constant_seconds": 0.5,
                    },
                },
                {
                    "vehicle_id": "CAR_2",
                    "position_m": 25.0,
                    "mass_kg": 40000.0,
                    "maximum_brake_force_n": 100000.0,
                    "brake_cylinder": {
                        "maximum_pressure_kpa": 380.0,
                        "fill_time_constant_seconds": 0.5,
                    },
                },
            ],
        }],
    }


class ConfiguredBrakingServiceTests(unittest.TestCase):
    def write_config(self, directory, data):
        path = Path(directory) / "formations.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_selected_formation_runs_complete_braking_simulation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, formation_config())
            service = ConfiguredBrakingService(path)
            self.assertEqual(service.available_formations, ("TEST_2_CAR",))
            result = service.simulate_service_braking(
                "TEST_2_CAR", 20.0, time_step_seconds=0.02
            )

        self.assertEqual(result.initial_speed_mps, 20.0)
        self.assertEqual(result.final_speed_mps, 0.0)
        self.assertGreater(result.stopping_time_seconds, 0.0)
        self.assertGreater(result.stopping_distance_m, 0.0)
        self.assertTrue(result.samples)
        self.assertEqual(len(result.samples[-1].cylinder_pressures_kpa), 2)

    def test_empty_configuration_has_no_implicit_or_default_formation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, {"schema_version": 1, "formations": []})
            service = ConfiguredBrakingService(path)

        self.assertEqual(service.available_formations, ())
        with self.assertRaises(UnknownBrakeFormationError):
            service.simulate_service_braking("MINUETTO", 20.0)

    def test_invalid_configuration_fails_before_simulation(self):
        config = formation_config()
        del config["formations"][0]["vehicles"][0]["mass_kg"]
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, config)
            with self.assertRaises(ValueError):
                ConfiguredBrakingService(path)

    def test_configured_service_does_not_change_legacy_running_time_path(self):
        calculator = TravelTimeCalculator()
        vehicle = VehiclePerformance(
            max_speed_kmh=120,
            acceleration_mps2=0.7,
            service_braking_mps2=0.8,
        )
        segment = SegmentPerformance(distance_km=10, speed_limit_kmh=100)
        before = calculator.calculate_segment_minutes(segment, vehicle)

        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, formation_config())
            service = ConfiguredBrakingService(path)
            service.simulate_service_braking("TEST_2_CAR", 20.0)

        after = calculator.calculate_segment_minutes(segment, vehicle)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
