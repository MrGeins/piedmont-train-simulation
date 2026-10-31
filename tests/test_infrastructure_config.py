import unittest
from backend.configuration.loader import load_infrastructure
from backend.configuration.validator import InfrastructureConfigError, validate_infrastructure
from backend.configuration.providers import LocalJsonInfrastructureProvider
from backend.configuration.loader import DEFAULT_CONFIG_PATH


class InfrastructureConfigTests(unittest.TestCase):
    def test_active_configuration_loads(self):
        stations, links, topology = load_infrastructure()
        self.assertEqual(len(stations), 99)
        self.assertEqual(len(links), 123)
        self.assertEqual(len(topology), 122)
        self.assertEqual(set(stations) - set(topology), set())
        self.assertIn("STURA", stations)
        self.assertIn("STURA", topology)
        # The current SFM source has no measured segment lengths yet.
        self.assertTrue(all(link.distance_km is None for link in links))

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

    def test_invalid_operational_link_data_is_rejected(self):
        data = {
            "schema_version": 1,
            "stations": {"A": {"name": "A", "roro_station": True, "default_dwell": 1, "terminal": False,
                "num_tracks": 1, "available_tracks": [1], "stub_tracks": {}},
                "B": {"name": "B", "roro_station": True, "default_dwell": 1, "terminal": True,
                "num_tracks": 1, "available_tracks": [1], "stub_tracks": {}}},
            "topology": {"A": {"name": "A", "x": 0, "y": 0, "display_label": True},
                "B": {"name": "B", "x": 1, "y": 1, "display_label": True}},
            "links": [{"from": "A", "to": "B", "double_track": True,
                "distance_km": -1, "speed_limit_kmh": 80}],
        }
        with self.assertRaises(InfrastructureConfigError):
            validate_infrastructure(data)

    def test_infrastructure_can_be_loaded_through_a_provider(self):
        provider = LocalJsonInfrastructureProvider(DEFAULT_CONFIG_PATH)
        stations, links, topology = load_infrastructure(provider=provider)
        self.assertTrue(stations)
        self.assertTrue(links)
        self.assertTrue(topology)


if __name__ == "__main__":
    unittest.main()
