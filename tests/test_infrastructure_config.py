import unittest
from backend.configuration.loader import load_infrastructure
from backend.configuration.validator import InfrastructureConfigError, validate_infrastructure


class InfrastructureConfigTests(unittest.TestCase):
    def test_active_configuration_loads(self):
        stations, links, topology = load_infrastructure()
        self.assertGreater(len(stations), 0)
        self.assertGreater(len(links), 0)
        self.assertGreater(len(topology), 0)
        self.assertEqual(set(stations) - set(topology), set())
        self.assertIn("STURA", stations)
        self.assertIn("STURA", topology)

    def test_unknown_link_endpoint_is_rejected(self):
        data = {
            "schema_version": 1,
            "stations": {"A": {"name": "A", "roro_station": True, "default_dwell": 1, "terminal": False,
                "num_tracks": 1, "available_tracks": [1], "stub_tracks": {}}},
            "topology": {"A": {"name": "A", "x": 0, "y": 0, "display_label": True}},
            "links": [{"from": "A", "to": "MISSING", "double_track": True}],
        }
        with self.assertRaises(InfrastructureConfigError):
            validate_infrastructure(data)


if __name__ == "__main__":
    unittest.main()
