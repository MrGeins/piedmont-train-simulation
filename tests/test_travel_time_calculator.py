import unittest

from backend.railway.travel_time_calculator import (
    MissingOperationalDataError,
    SegmentPerformance,
    TravelTimeCalculator,
)
from backend.railway.vehicle_performance import (
    AccelerationPoint,
    DavisResistance,
    TractionModel,
    VehiclePerformance,
)
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

    def test_speed_dependent_acceleration_curve_is_used(self):
        profiled_vehicle = VehiclePerformance(
            max_speed_kmh=120,
            acceleration_mps2=0.7,
            service_braking_mps2=0.8,
            acceleration_curve=(
                AccelerationPoint(0, 1.0),
                AccelerationPoint(50, 0.8),
                AccelerationPoint(120, 0.4),
            ),
        )
        segment = SegmentPerformance(distance_km=10, speed_limit_kmh=100)

        profiled_time = self.calculator.calculate_segment_minutes(segment, profiled_vehicle)
        constant_time = self.calculator.calculate_segment_minutes(segment, self.vehicle)

        self.assertGreater(profiled_time, 0)
        self.assertLess(profiled_time, constant_time)

    def test_speed_dependent_profile_handles_short_segments(self):
        profiled_vehicle = VehiclePerformance(
            max_speed_kmh=120,
            acceleration_mps2=0.7,
            service_braking_mps2=0.8,
            acceleration_curve=(
                AccelerationPoint(0, 1.0),
                AccelerationPoint(120, 0.4),
            ),
        )
        time_minutes = self.calculator.calculate_segment_minutes(
            SegmentPerformance(distance_km=0.5, speed_limit_kmh=120),
            profiled_vehicle,
        )
        self.assertGreater(time_minutes, 0)
        self.assertLess(time_minutes, 2)

    def test_acceleration_curve_must_start_at_zero_and_cover_max_speed(self):
        with self.assertRaises(ValueError):
            VehiclePerformance(
                120, 0.7, 0.8,
                acceleration_curve=(AccelerationPoint(10, 0.9), AccelerationPoint(120, 0.4)),
            )
        with self.assertRaises(ValueError):
            VehiclePerformance(
                120, 0.7, 0.8,
                acceleration_curve=(AccelerationPoint(0, 0.9), AccelerationPoint(100, 0.4)),
            )

    def test_acceleration_curve_speeds_must_be_strictly_increasing(self):
        with self.assertRaises(ValueError):
            VehiclePerformance(
                120, 0.7, 0.8,
                acceleration_curve=(
                    AccelerationPoint(0, 0.9),
                    AccelerationPoint(60, 0.6),
                    AccelerationPoint(60, 0.5),
                    AccelerationPoint(120, 0.4),
                ),
            )

    def test_davis_resistance_uses_explicit_si_units(self):
        resistance = DavisResistance(A_N=1000, B_N_per_mps=10, C_N_per_mps2=2)
        self.assertAlmostEqual(resistance.force_n(5), 1050)

    def test_tractive_effort_is_limited_by_effort_and_power(self):
        model = TractionModel(
            mass_kg=200_000,
            max_tractive_effort_n=200_000,
            max_power_w=2_000_000,
            resistance=DavisResistance(1000, 10, 2),
        )
        self.assertEqual(model.tractive_effort_n(0), 200_000)
        self.assertEqual(model.tractive_effort_n(5), 200_000)
        self.assertAlmostEqual(model.tractive_effort_n(20), 100_000)

    def test_traction_and_davis_model_calculates_segment_time(self):
        traction = TractionModel(
            mass_kg=200_000,
            max_tractive_effort_n=200_000,
            max_power_w=2_000_000,
            resistance=DavisResistance(1000, 10, 2),
        )
        vehicle = VehiclePerformance(
            max_speed_kmh=120,
            acceleration_mps2=0.7,
            service_braking_mps2=0.8,
            traction_model=traction,
        )
        minutes = self.calculator.calculate_segment_minutes(
            SegmentPerformance(distance_km=10, speed_limit_kmh=100), vehicle
        )
        self.assertGreater(minutes, 0)
        self.assertLess(minutes, 15)

    def test_traction_model_handles_short_segments(self):
        traction = TractionModel(
            mass_kg=200_000,
            max_tractive_effort_n=200_000,
            max_power_w=2_000_000,
            resistance=DavisResistance(1000, 10, 2),
        )
        vehicle = VehiclePerformance(120, 0.7, 0.8, traction_model=traction)
        minutes = self.calculator.calculate_segment_minutes(
            SegmentPerformance(0.5, 100), vehicle
        )
        self.assertGreater(minutes, 0)
        self.assertLess(minutes, 2)

    def test_traction_model_rejects_unable_to_start_train(self):
        traction = TractionModel(
            mass_kg=200_000,
            max_tractive_effort_n=10_000,
            max_power_w=2_000_000,
            resistance=DavisResistance(12_000, 10, 2),
        )
        vehicle = VehiclePerformance(120, 0.7, 0.8, traction_model=traction)
        with self.assertRaises(ValueError):
            self.calculator.calculate_segment_minutes(
                SegmentPerformance(1, 80), vehicle
            )

    def test_acceleration_curve_and_traction_model_are_mutually_exclusive(self):
        traction = TractionModel(
            mass_kg=200_000,
            max_tractive_effort_n=200_000,
            max_power_w=2_000_000,
            resistance=DavisResistance(1000, 10, 2),
        )
        with self.assertRaises(ValueError):
            VehiclePerformance(
                120, 0.7, 0.8,
                acceleration_curve=(
                    AccelerationPoint(0, 1.0),
                    AccelerationPoint(120, 0.4),
                ),
                traction_model=traction,
            )

    def test_davis_coefficients_must_be_non_negative_and_nonzero(self):
        with self.assertRaises(ValueError):
            DavisResistance(-1, 0, 0)
        with self.assertRaises(ValueError):
            DavisResistance(0, 0, 0)


if __name__ == "__main__":
    unittest.main()
