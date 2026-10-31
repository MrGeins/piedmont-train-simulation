import unittest

from backend.configuration.rolling_stock_loader import (
    load_vehicle_profiles,
    validate_rolling_stock,
    RollingStockConfigError,
)


class RollingStockConfigTests(unittest.TestCase):
    def test_unpopulated_sfm_profiles_are_explicitly_empty(self):
        profiles = load_vehicle_profiles()
        self.assertEqual(profiles, {})

    def test_valid_profile_is_accepted(self):
        validate_rolling_stock({
            "schema_version": 1,
            "profiles": {
                "TEST_EMU": {
                    "max_speed_kmh": 120,
                    "acceleration_mps2": 0.7,
                    "service_braking_mps2": 0.8,
                    "minimum_turnback_seconds": 180,
                }
            },
        })

    def test_invalid_profile_is_rejected(self):
        with self.assertRaises(RollingStockConfigError):
            validate_rolling_stock({
                "schema_version": 1,
                "profiles": {
                    "TEST_EMU": {
                        "max_speed_kmh": 0,
                        "acceleration_mps2": 0.7,
                        "service_braking_mps2": 0.8,
                    }
                },
            })


if __name__ == "__main__":
    unittest.main()
