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
            item["type_id"]: item["published_specs"]
            for item in data["observed_types"]
            if "published_specs" in item
        }
        self.assertEqual(set(published), {"MINUETTO", "POP", "ROCK", "TAF", "E464_VIVALTO"})
        expected = {
            "MINUETTO": (160, 1250),
            "POP": (160, 2000),
            "ROCK": (160, 3400),
            "TAF": (140, 3640),
            "E464_VIVALTO": (160, 3500),
        }
        for type_id, (max_speed, hourly_power) in expected.items():
            self.assertEqual(published[type_id]["max_speed_kmh"], max_speed)
            self.assertEqual(published[type_id]["hourly_power_kw"], hourly_power)
            self.assertIn(published[type_id]["source_id"], {
                "treniebinari_minuetto", "treniebinari_pop", "treniebinari_rock",
                "treniebinari_taf", "treniebinari_e464",
            })
        self.assertEqual(published["E464_VIVALTO"]["continuous_power_kw"], 3000)
        self.assertEqual(published["E464_VIVALTO"]["service_mass_t"], 72)
        self.assertEqual(published["E464_VIVALTO"]["maximum_tractive_effort_kn"], 200)
        self.assertEqual(data["profiles"], {})

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
