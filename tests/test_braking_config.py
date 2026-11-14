import json
import tempfile
import unittest
from pathlib import Path

from backend.configuration.braking_loader import (
    BrakingConfigError,
    load_brake_formations,
    validate_braking_config,
)


def valid_config():
    return {
        "schema_version": 1,
        "formations": [{
            "formation_id": "TEST_3_CAR",
            "brake_pipe": {
                "propagation_speed_mps": 200.0,
                "pressure_response_time_constant_seconds": 0.5,
                "full_service_pressure_reduction_kpa": 150.0,
            },
            "vehicles": [
                {
                    "vehicle_id": "A",
                    "position_m": 0.0,
                    "mass_kg": 40000.0,
                    "maximum_brake_force_n": 60000.0,
                    "brake_cylinder": {
                        "maximum_pressure_kpa": 380.0,
                        "fill_time_constant_seconds": 2.0,
                    },
                },
                {
                    "vehicle_id": "B",
                    "position_m": 25.0,
                    "mass_kg": 40000.0,
                    "maximum_brake_force_n": 60000.0,
                    "brake_cylinder": {
                        "maximum_pressure_kpa": 380.0,
                        "fill_time_constant_seconds": 2.0,
                    },
                },
            ],
        }],
    }


class BrakingConfigTests(unittest.TestCase):
    def test_default_configuration_is_empty_and_does_not_activate_candidate_data(self):
        self.assertEqual(load_brake_formations(), {})

    def test_valid_configuration_loads_typed_formation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "braking.json"
            path.write_text(json.dumps(valid_config()), encoding="utf-8")
            formations = load_brake_formations(path)
        self.assertEqual(set(formations), {"TEST_3_CAR"})
        formation = formations["TEST_3_CAR"]
        self.assertEqual(formation.total_mass_kg, 80000.0)
        self.assertEqual(formation.vehicles[1].position_m, 25.0)
        self.assertEqual(formation.brake_pipe.propagation_speed_mps, 200.0)

    def test_missing_physical_parameter_is_rejected(self):
        config = valid_config()
        del config["formations"][0]["vehicles"][0]["mass_kg"]
        with self.assertRaisesRegex(BrakingConfigError, "mass_kg"):
            validate_braking_config(config)

    def test_non_finite_and_non_positive_parameters_are_rejected(self):
        for invalid in (0, -1, float("inf"), float("nan"), True):
            with self.subTest(value=invalid):
                config = valid_config()
                config["formations"][0]["brake_pipe"]["propagation_speed_mps"] = invalid
                with self.assertRaises(BrakingConfigError):
                    validate_braking_config(config)

    def test_duplicate_formation_ids_are_rejected(self):
        config = valid_config()
        config["formations"].append(config["formations"][0].copy())
        with self.assertRaisesRegex(BrakingConfigError, "duplicate formation_id"):
            validate_braking_config(config)

    def test_duplicate_vehicle_ids_are_rejected(self):
        config = valid_config()
        config["formations"][0]["vehicles"][1]["vehicle_id"] = "A"
        with self.assertRaisesRegex(BrakingConfigError, "duplicate vehicle_id"):
            validate_braking_config(config)

    def test_vehicle_order_and_command_source_position_are_enforced(self):
        config = valid_config()
        config["formations"][0]["vehicles"].reverse()
        with self.assertRaisesRegex(BrakingConfigError, "position_m"):
            validate_braking_config(config)
        config = valid_config()
        config["formations"][0]["vehicles"][0]["position_m"] = 1.0
        with self.assertRaisesRegex(BrakingConfigError, "command-source"):
            validate_braking_config(config)

    def test_unknown_fields_are_rejected(self):
        config = valid_config()
        config["formations"][0]["vehicles"][0]["estimated_braking_force"] = 123
        with self.assertRaisesRegex(BrakingConfigError, "unknown fields"):
            validate_braking_config(config)

    def test_empty_vehicle_list_is_rejected(self):
        config = valid_config()
        config["formations"][0]["vehicles"] = []
        with self.assertRaisesRegex(BrakingConfigError, "non-empty array"):
            validate_braking_config(config)


if __name__ == "__main__":
    unittest.main()
