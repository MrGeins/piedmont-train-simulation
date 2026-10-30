import unittest

from backend.controller.timetable_generator import TimetableGenerator
from backend.controller.train_agent import TrainAgent
from backend.data.schedules_service import SERVICES


class TimetableGenerationTests(unittest.TestCase):
    def test_full_day_timetable_has_unique_ids_and_valid_platforms(self):
        trains = TimetableGenerator.generate_full_day_timetable()
        self.assertEqual(len(trains), 37)
        self.assertEqual(len({train.train_number for train in trains}), len(trains))
        TimetableGenerator.validate_generated_timetable(trains)

    def test_generated_agents_represent_physical_trainsets(self):
        trains = TimetableGenerator.generate_full_day_timetable()
        self.assertTrue(trains)
        self.assertTrue(all(train.frequency_seconds > 0 for train in trains))
        self.assertTrue(all(not train.custom_travel_times for train in trains))
        self.assertTrue(all(not train.custom_dwell_times for train in trains))
        self.assertEqual(len(trains), sum(config["fleet_size"] for config in SERVICES.values()))

    def test_generated_trains_use_service_parameters(self):
        trains = TimetableGenerator.generate_full_day_timetable()
        self.assertTrue(all(train.end_service_time > train.departure_time for train in trains))

    def test_fleet_capacity_uses_running_time_and_turnback(self):
        route = ["STURA", "REBAUDENGO"]
        required = TimetableGenerator.required_fleet_size(
            route,
            frequency_min=10,
            travel_times={("STURA", "REBAUDENGO"): 10.0},
            turnback_seconds=120,
        )
        self.assertEqual(required, 3)

    def test_fleet_capacity_is_derived_from_route_and_frequency(self):
        route = ["STURA", "REBAUDENGO", "DORA", "PORTA_SUSA"]
        required = TimetableGenerator.required_fleet_size(route, frequency_min=10)
        self.assertGreaterEqual(required, 2)

    def test_travel_model_arguments_must_be_supplied_together(self):
        with self.assertRaisesRegex(ValueError, "must be provided together"):
            TimetableGenerator.generate_full_day_timetable(travel_time_calculator=object())

    def test_duplicate_train_numbers_are_rejected(self):
        first = TrainAgent(service_id="X", train_number=1, route=["STURA"], departure_time_str="05:00:00")
        second = TrainAgent(service_id="Y", train_number=1, route=["STURA"], departure_time_str="05:01:00")
        with self.assertRaisesRegex(ValueError, "duplicate train number"):
            TimetableGenerator.validate_generated_timetable([first, second])


if __name__ == "__main__":
    unittest.main()
