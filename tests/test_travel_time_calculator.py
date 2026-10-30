import unittest

from backend.railway.travel_time_calculator import (
    MissingOperationalDataError,
    SegmentPerformance,
    TravelTimeCalculator,
)
from backend.railway.vehicle_performance import VehiclePerformance
from backend.model.models import RailwayLine


class TravelTimeCalculatorTests(unittest.TestCase):
    def setUp(self):
        self.calculator = TravelTimeCalculator()
        self.vehicle = VehiclePerformance(
            max_speed_kmh=120,
            acceleration_mps2=0.7,
            service_braking_mps2=0.8,
            minimum_turnback_seconds=180,
        )

    def test_running_time_uses_the_lower_speed_limit(self):
        segment = SegmentPerformance(distance_km=10, speed_limit_kmh=80)
        time_minutes = self.calculator.calculate_segment_minutes(segment, self.vehicle)
        self.assertGreater(time_minutes, 7.5)
        self.assertLess(time_minutes, 8.5)

    def test_short_segment_uses_acceleration_and_braking_profile(self):
        segment = SegmentPerformance(distance_km=0.5, speed_limit_kmh=120)
        time_minutes = self.calculator.calculate_segment_minutes(segment, self.vehicle)
        self.assertGreater(time_minutes, 0)
        self.assertLess(time_minutes, 2)

    def test_path_requires_operational_data_for_every_link(self):
        links = [RailwayLine("A", "B", True, distance_km=2, speed_limit_kmh=80)]
        result = self.calculator.calculate_path_minutes(["A", "B"], links, self.vehicle)
        self.assertGreater(result, 0)
        with self.assertRaises(MissingOperationalDataError):
            self.calculator.calculate_path_minutes(
                ["A", "B", "C"], links, self.vehicle
            )

    def test_invalid_vehicle_performance_is_rejected(self):
        with self.assertRaises(ValueError):
            VehiclePerformance(0, 0.7, 0.8)


if __name__ == "__main__":
    unittest.main()
