import unittest

from backend.railway.braking import (
    BrakeCylinderModel, BrakeFormation, BrakePipeModel, BrakeSimulation, BrakeVehicle,
)


class BrakeCylinderModelTests(unittest.TestCase):
    def setUp(self):
        self.cylinder = BrakeCylinderModel(380.0, 2.0)

    def test_cylinder_pressure_develops_progressively(self):
        first = self.cylinder.pressure_after(0.0, 380.0, 1.0)
        second = self.cylinder.pressure_after(first, 380.0, 1.0)
        self.assertGreater(first, 0.0)
        self.assertGreater(second, first)
        self.assertLess(second, 380.0)

    def test_cylinder_pressure_approaches_target_without_overshoot(self):
        pressure = self.cylinder.pressure_after(0.0, 380.0, 100.0)
        self.assertAlmostEqual(pressure, 380.0, places=5)
        self.assertLessEqual(pressure, 380.0)

    def test_pressure_target_is_limited_to_full_service_demand(self):
        self.assertEqual(self.cylinder.target_pressure_kpa(300.0, 150.0), 380.0)

    def test_invalid_cylinder_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            BrakeCylinderModel(0.0, 2.0)
        with self.assertRaises(ValueError):
            BrakeCylinderModel(380.0, -1.0)


class BrakePipeModelTests(unittest.TestCase):
    def setUp(self):
        self.pipe = BrakePipeModel(200.0, 0.5, 150.0)

    def test_no_pressure_change_before_command_front_arrives(self):
        self.assertEqual(self.pipe.pressure_reduction_kpa(200.0, 0.9), 0.0)

    def test_pressure_response_starts_at_local_arrival(self):
        self.assertEqual(self.pipe.pressure_reduction_kpa(200.0, 1.0), 0.0)
        self.assertGreater(self.pipe.pressure_reduction_kpa(200.0, 1.5), 0.0)

    def test_pressure_reduction_is_monotonic_and_bounded(self):
        early = self.pipe.pressure_reduction_kpa(100.0, 1.0)
        later = self.pipe.pressure_reduction_kpa(100.0, 2.0)
        self.assertGreater(later, early)
        self.assertLessEqual(later, 150.0)

    def test_invalid_pipe_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            BrakePipeModel(0.0, 0.5, 150.0)


class BrakeSimulationTests(unittest.TestCase):
    def setUp(self):
        self.pipe = BrakePipeModel(200.0, 0.2, 150.0)
        self.cylinder = BrakeCylinderModel(380.0, 0.8)
        self.simulator = BrakeSimulation()

    def make_formation(self, positions=(0.0, 100.0, 200.0)):
        vehicles = tuple(
            BrakeVehicle(f"V{index + 1}", position, 40_000.0, 60_000.0, self.cylinder)
            for index, position in enumerate(positions)
        )
        return BrakeFormation(vehicles, self.pipe)

    def test_rear_vehicle_receives_brake_command_after_front_vehicle(self):
        result = self.simulator.simulate_service_braking(
            self.make_formation(), 20.0, time_step_seconds=0.02
        )
        sample = next(item for item in result.samples if item.time_seconds >= 0.75)
        front, middle, rear = sample.cylinder_pressures_kpa
        self.assertGreater(front, middle)
        self.assertGreater(middle, rear)

    def test_longer_formation_increases_last_vehicle_command_delay(self):
        short = self.simulator.simulate_service_braking(self.make_formation((0.0, 100.0)), 20.0)
        long = self.simulator.simulate_service_braking(self.make_formation((0.0, 100.0, 400.0)), 20.0)
        short_first = next(s.time_seconds for s in short.samples if s.cylinder_pressures_kpa[-1] > 1.0)
        long_first = next(s.time_seconds for s in long.samples if s.cylinder_pressures_kpa[-1] > 1.0)
        self.assertGreater(long_first, short_first)

    def test_total_brake_force_never_exceeds_vehicle_force_sum(self):
        formation = self.make_formation()
        result = self.simulator.simulate_service_braking(formation, 20.0)
        limit = sum(item.maximum_brake_force_n for item in formation.vehicles)
        self.assertLessEqual(result.peak_brake_force_n, limit)

    def test_simulation_stops_train_and_returns_positive_distance(self):
        result = self.simulator.simulate_service_braking(self.make_formation(), 20.0)
        self.assertEqual(result.final_speed_mps, 0.0)
        self.assertGreater(result.stopping_time_seconds, 0.0)
        self.assertGreater(result.stopping_distance_m, 0.0)

    def test_uphill_grade_reduces_stopping_distance(self):
        formation = self.make_formation()
        level = self.simulator.simulate_service_braking(formation, 20.0)
        uphill = self.simulator.simulate_service_braking(formation, 20.0, gradient_permille=10.0)
        self.assertLess(uphill.stopping_distance_m, level.stopping_distance_m)

    def test_downhill_grade_increases_stopping_distance(self):
        formation = self.make_formation()
        level = self.simulator.simulate_service_braking(formation, 20.0)
        downhill = self.simulator.simulate_service_braking(formation, 20.0, gradient_permille=-10.0)
        self.assertGreater(downhill.stopping_distance_m, level.stopping_distance_m)

    def test_insufficient_maximum_braking_on_downhill_is_rejected(self):
        with self.assertRaises(ValueError):
            self.simulator.simulate_service_braking(self.make_formation(), 20.0, gradient_permille=-200.0)

    def test_formation_requires_ordered_vehicles_starting_at_zero(self):
        with self.assertRaises(ValueError):
            BrakeFormation(
                (BrakeVehicle("V1", 10.0, 40_000, 60_000, self.cylinder),), self.pipe
            )

    def test_simulation_rejects_non_positive_speed(self):
        with self.assertRaises(ValueError):
            self.simulator.simulate_service_braking(self.make_formation(), 0.0)


if __name__ == "__main__":
    unittest.main()
