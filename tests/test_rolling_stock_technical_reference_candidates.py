import json
import unittest
from pathlib import Path


class RollingStockTechnicalReferenceCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.candidates = json.loads(
            (root / "config/rolling_stock/technical_reference_candidates.json").read_text(encoding="utf-8")
        )
        cls.operational = json.loads(
            (root / "config/rolling_stock/sfm.json").read_text(encoding="utf-8")
        )

    def test_candidate_dataset_is_explicitly_unverified_and_user_supplied(self):
        metadata = self.candidates["metadata"]
        self.assertEqual(metadata["verification_status"], "user_supplied_unverified")
        self.assertTrue(metadata["supplied_by_user"])
        self.assertEqual(metadata["source_file"], "specifiche_tecniche_treni_piemonte.pdf")
        self.assertEqual(metadata["source_pages"], [1, 2, 3])

    def test_all_vehicle_variants_are_preserved(self):
        vehicles = {item["type_id"]: item for item in self.candidates["vehicles"]}
        self.assertEqual(set(vehicles), {
            "ROCK_ETR521", "POP_ETR104", "JAZZ_ETR425", "TAF_ALE426",
            "MINUETTO_ELECTRIC", "MINUETTO_DIESEL", "BLUES_HTR312", "BLUES_HTR412",
            "VIVALTO_E464_5NCDP", "MD_E464_5MDVC_MDVE",
        })
        self.assertEqual(vehicles["ROCK_ETR521"]["equivalent_mass_t"], 313)
        self.assertEqual(vehicles["ROCK_ETR521"]["davis_coefficients_kgf"], {"A": 320, "B": 1.30, "C": 0.024})
        self.assertEqual(vehicles["POP_ETR104"]["maximum_power_kw"], 2400)
        self.assertEqual(vehicles["TAF_ALE426"]["maximum_power_kw"], 2360)
        self.assertEqual(vehicles["JAZZ_ETR425"]["emergency_braking_mps2"], 1.10)
        self.assertEqual(vehicles["MINUETTO_DIESEL"]["maximum_tractive_effort_kn"], 95)
        self.assertEqual(vehicles["BLUES_HTR312"]["maximum_speed_by_mode_kmh"]["battery"], 100)
        self.assertEqual(vehicles["BLUES_HTR412"]["mass_empty_t"], 190)
        self.assertEqual(vehicles["VIVALTO_E464_5NCDP"]["equivalent_mass_t"], 335)
        self.assertEqual(vehicles["MD_E464_5MDVC_MDVE"]["pneumatic_brake_delay_seconds"], 2.5)

    def test_candidate_values_are_not_loaded_as_operational_profiles(self):
        self.assertEqual(self.operational["profiles"], {})


if __name__ == "__main__":
    unittest.main()
