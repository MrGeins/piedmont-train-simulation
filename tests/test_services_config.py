import unittest
from backend.configuration.services_loader import load_services
from backend.configuration.services_validator import ServicesConfigError, validate_services
from backend.configuration.loader import load_infrastructure

class ServicesConfigTests(unittest.TestCase):
    def test_services_load_and_reference_known_stations(self):
        routes, plans, templates = load_services()
        stations, _, _ = load_infrastructure()
        self.assertEqual(set(routes), set(plans))
        self.assertIn("S1", templates)
        self.assertTrue(all(stop in stations for route in routes.values() for stop in route))

    def test_unknown_route_station_is_rejected(self):
        data = {"schema_version": 1, "ROUTES": {"X": ["MISSING"]}, "PLATFORM_PLANS": {"X": {}},
                "TAKT_TEMPLATES": {"X": {"route_key": "X", "service_id": "X", "base_num": 1,
                "fleet_size": 1, "start_time_south": "05:00:00", "start_time_north": "05:00:00",
                "end_time": "23:00:00", "frequency_min": 60, "SOUTH": {"MISSING": "a:00"}, "NORTH": {"MISSING": "a:00"}}}}
        with self.assertRaises(ServicesConfigError): validate_services(data, {})

if __name__ == "__main__": unittest.main()
