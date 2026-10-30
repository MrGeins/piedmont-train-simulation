import unittest

from scripts.rinf_candidate_import import build_candidates, normalize_name


class RinfCandidateImportTests(unittest.TestCase):
    def setUp(self):
        self.infrastructure = {
            "topology": {
                "A": {"name": "Alpha"},
                "B": {"name": "Beta"},
                "MID": {"name": "Intermediate"},
            },
            "links": [{"from": "A", "to": "MID", "double_track": True}],
        }
        self.aliases = {"ALPHA": "A", "BETA": "B"}

    def test_name_normalization_is_deterministic(self):
        self.assertEqual(normalize_name("Torino Porta-Sùsa"), "TORINO PORTA SUSA")

    def test_candidate_is_review_only_and_not_auto_promoted(self):
        report = build_candidates([{
            "section_uri": "https://example.test/sol/1",
            "start_name": "Alpha",
            "end_name": "Beta",
            "distance_km": "12.5",
            "speed_limit_kmh": "90",
        }], self.infrastructure, self.aliases, "2026-09-29")
        candidate = report["candidate_sections"][0]
        self.assertEqual(candidate["distance_km"], 12.5)
        self.assertEqual(candidate["speed_limit_kmh"], 90)
        self.assertEqual(candidate["status"], "pending_manual_review")
        self.assertFalse(candidate["direct_project_link"])
        self.assertIn("rinf_section_not_a_single_project_topology_edge", candidate["review_reasons"])
        self.assertFalse(report["active_infrastructure_modified"])

    def test_missing_alias_is_not_guessed(self):
        report = build_candidates([{
            "section_uri": "sol-2",
            "start_name": "Unmapped",
            "end_name": "Beta",
            "distance_km": "4.2",
            "speed_limit_kmh": "",
        }], self.infrastructure, self.aliases, "snapshot")
        self.assertEqual(report["summary"]["unmatched_sections"], 1)
        self.assertEqual(report["candidate_sections"], [])

    def test_multiple_track_speeds_require_review(self):
        rows = [
            {"section_uri": "sol-3", "start_name": "Alpha", "end_name": "Beta", "distance_km": "10", "speed_limit_kmh": "80"},
            {"section_uri": "sol-3", "start_name": "Alpha", "end_name": "Beta", "distance_km": "10", "speed_limit_kmh": "100"},
        ]
        report = build_candidates(rows, self.infrastructure, self.aliases, "snapshot")
        candidate = report["candidate_sections"][0]
        self.assertIsNone(candidate["speed_limit_kmh"])
        self.assertIn("multiple_track_speed_limits_require_directional_review", candidate["review_reasons"])

    def test_conflicting_lengths_are_not_imported(self):
        rows = [
            {"section_uri": "sol-4", "start_name": "Alpha", "end_name": "Beta", "distance_km": "10", "speed_limit_kmh": ""},
            {"section_uri": "sol-4", "start_name": "Alpha", "end_name": "Beta", "distance_km": "11", "speed_limit_kmh": ""},
        ]
        report = build_candidates(rows, self.infrastructure, self.aliases, "snapshot")
        self.assertIsNone(report["candidate_sections"][0]["distance_km"])
        self.assertIn("conflicting_section_lengths", report["candidate_sections"][0]["review_reasons"])


if __name__ == "__main__":
    unittest.main()
