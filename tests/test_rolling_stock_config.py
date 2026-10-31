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


    def test_published_maximum_speeds_are_not_mistaken_for_complete_profiles(self):
        import json
        from pathlib import Path

        config_path = Path(__file__).resolve().parents[1] / "config/rolling_stock/sfm.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["profiles"], {})
        published = {
            item["type_id"]: item["published_specs"]["max_speed_kmh"]
            for item in data["observed_types"]
            if "published_specs" in item
        }
        self.assertEqual(published, {"POP": 160, "ROCK": 160, "TAF": 140})
        for item in data["observed_types"]:
            if "published_specs" in item:
                self.assertEqual(
                    item["published_specs"]["calibration_status"],
                    "published_max_speed_only" if item["type_id"] == "ROCK"
                    else ("published_max_speed_only_exact_SFM_variant_not_fully_verified"
                          if item["type_id"] == "POP"
                          else "published_max_speed_only_exact_SFM_unit_not_fully_verified"),
                )

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
