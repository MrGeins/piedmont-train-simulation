import unittest

from backend.configuration.services_loader import load_services
from backend.configuration.services_validator import ServicesConfigError, validate_services
from backend.configuration.loader import load_infrastructure


class ServicesConfigTests(unittest.TestCase):
    def test_services_load_and_reference_known_stations(self):
        routes, plans, services = load_services()
        stations, _, _ = load_infrastructure()
        self.assertEqual(len(routes), 13)
        self.assertEqual(len(plans), 13)
        self.assertEqual(len(services), 13)
        self.assertEqual(set(routes), set(plans))
        self.assertIn("S1", services)
        self.assertTrue(all(stop in stations for route in routes.values() for stop in route))
        self.assertTrue(all(set(cfg) == {
            "service_id", "base_num", "fleet_size", "frequency_min", "start_time", "end_time"
        } for cfg in services.values()))

    def test_unknown_route_station_is_rejected(self):
        data = {
            "schema_version": 1,
            "ROUTES": {"X": ["MISSING"]},
            "PLATFORM_PLANS": {"X": {}},
            "SERVICES": {"X": {
                "service_id": "X", "base_num": 1, "fleet_size": 1,
                "frequency_min": 60, "start_time": "05:00:00", "end_time": "23:00:00"
            }},
        }
        with self.assertRaises(ServicesConfigError):
            validate_services(data, {})

    def test_manual_stop_times_are_not_part_of_service_schema(self):
        _, _, services = load_services()
        for cfg in services.values():
            self.assertNotIn("SOUTH", cfg)
            self.assertNotIn("NORTH", cfg)
            self.assertNotIn("route_key", cfg)


if __name__ == "__main__":
    unittest.main()
