"""Regression checks for the first source-traceable RINF calibration."""

import json
import re
import unicodedata
import unittest
from pathlib import Path

from backend.configuration.validator import validate_infrastructure

ROOT = Path(__file__).resolve().parents[1]


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


class RinfCalibratedInfrastructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infrastructure = json.loads(
            (ROOT / "config/infrastructure/sfm.json").read_text(encoding="utf-8")
        )
        cls.alias_document = json.loads(
            (ROOT / "config/infrastructure/rinf_operational_point_aliases.json").read_text(
                encoding="utf-8"
            )
        )

    def test_calibrated_infrastructure_remains_valid(self):
        validate_infrastructure(self.infrastructure)

    def test_only_source_traced_links_receive_rinf_distances(self):
        links = self.infrastructure["links"]
        calibrated = [link for link in links if "distance_source" in link]
        self.assertEqual(len(calibrated), 40)
        self.assertTrue(all(link["distance_km"] > 0 for link in calibrated))
        for link in calibrated:
            source = link["distance_source"]
            self.assertEqual(source["source_id"], "rinf_rfi_2026_09")
            self.assertEqual(source["snapshot"], "2026-09-29")
            self.assertTrue(source["section_uri"].startswith("http://data.europa.eu/949/sectionOfLine/"))

    def test_speed_is_promoted_only_when_track_limits_are_unambiguous(self):
        links = self.infrastructure["links"]
        with_speed = [link for link in links if "speed_limit_source" in link]
        distance_only = [
            link for link in links
            if "distance_source" in link and "speed_limit_source" not in link
        ]
        self.assertEqual(len(with_speed), 39)
        self.assertEqual(len(distance_only), 1)
        for link in with_speed:
            source = link["speed_limit_source"]
            self.assertGreater(link["speed_limit_kmh"], 0)
            if "track_limits" in source:
                self.assertGreaterEqual(len(source["track_limits"]), 2)
                self.assertEqual(
                    len({track["speed_limit_kmh"] for track in source["track_limits"]}), 1
                )
                for track in source["track_limits"]:
                    self.assertTrue(track["track_uri"].startswith("http://data.europa.eu/949/track/"))
                    self.assertTrue(track["track_id"])
                    self.assertIn(track["track_direction_code"], (10, 20, 30))
            else:
                self.assertEqual(source["track_direction_code"], 30)
                self.assertEqual(source["track_direction"], "both")
                self.assertTrue(source["track_uri"].startswith("http://data.europa.eu/949/track/"))
                self.assertTrue(source["track_id"])
        self.assertTrue(all("speed_limit_kmh" not in link for link in distance_only))
        unresolved = next(link for link in distance_only if link["from"] == "BIVIO_CROCETTA")
        self.assertEqual(unresolved["to"], "PORTA_SUSA")

    def test_registered_aliases_are_unique_exact_normalized_name_matches(self):
        aliases = self.alias_document["operational_point_aliases"]
        topology = self.infrastructure["topology"]
        normalized_names = {}
        for node_key, node in topology.items():
            normalized = normalize_name(node["name"])
            self.assertNotIn(normalized, normalized_names)
            normalized_names[normalized] = node_key

        self.assertEqual(len(aliases), 73)
        for rinf_name, node_key in aliases.items():
            self.assertIn(node_key, topology)
            self.assertEqual(normalize_name(rinf_name), normalize_name(topology[node_key]["name"]))
            self.assertEqual(normalized_names[normalize_name(rinf_name)], node_key)


if __name__ == "__main__":
    unittest.main()
