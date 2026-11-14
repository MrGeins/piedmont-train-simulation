import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SfmReferenceDataTests(unittest.TestCase):
    def test_authoritative_source_registry_has_rinf_and_operating_plan(self):
        data = json.loads((ROOT / "config/data_sources/sfm.json").read_text(encoding="utf-8"))
        self.assertIn("rinf_rfi_2026_09", data["sources"])
        self.assertIn("sfm_program_2026", data["sources"])
        self.assertEqual(data["sources"]["rinf_rfi_2026_09"]["infrastructure_manager_code"], "0083")

    def test_2026_observations_are_route_level_and_have_provenance(self):
        data = json.loads(
            (ROOT / "config/reference_data/sfm_2026_operating_observations.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["source_id"], "sfm_program_2026")
        self.assertGreaterEqual(len(data["observations"]), 4)
        for observation in data["observations"]:
            self.assertGreater(observation["route_distance_km"], 0)
            self.assertGreater(observation["planned_duration_min"], 0)
            self.assertIn("rolling_stock_type", observation)
            self.assertNotIn("distance_km", observation)

    def test_observed_rolling_stock_types_are_not_physics_profiles(self):
        data = json.loads((ROOT / "config/rolling_stock/sfm.json").read_text(encoding="utf-8"))
        self.assertEqual(data["profiles"], {})
        types = {item["type_id"] for item in data["observed_types"]}
        self.assertTrue({"MINUETTO", "POP", "JAZZ", "ROCK", "TAF", "E464_VIVALTO"} <= types)
        self.assertTrue(all(item["performance_profile_status"] == "not_calibrated" for item in data["observed_types"]))


if __name__ == "__main__":
    unittest.main()
