import unittest

from backend.controller.timetable_generator import TimetableGenerator
from backend.controller.train_agent import TrainAgent
from backend.controller.fleet_manager import FleetManager, FleetCapacityError
from backend.data.schedules_service import SERVICES
from backend.utils.time_formatter import time_to_seconds


class TimetableGenerationTests(unittest.TestCase):
    def test_full_day_timetable_has_unique_ids_and_valid_platforms(self):
        trains = TimetableGenerator.generate_full_day_timetable()
        self.assertEqual(len(trains), 30)
        self.assertEqual(len({train.train_number for train in trains}), len(trains))
        TimetableGenerator.validate_generated_timetable(trains)

    def test_generated_agents_represent_physical_trainsets(self):
        trains = TimetableGenerator.generate_full_day_timetable()
        self.assertTrue(trains)
        self.assertTrue(all(train.frequency_seconds > 0 for train in trains))
        self.assertTrue(all(train.custom_travel_times for train in trains))
        self.assertTrue(all(value > 0 for train in trains for value in train.custom_travel_times.values()))
        self.assertTrue(all(not train.custom_dwell_times for train in trains))
        minimum_active = sum(
            TimetableGenerator.required_fleet_size(
                __import__("backend.data.schedules_service", fromlist=["ROUTES"]).ROUTES[cfg["service_id"]],
                cfg["frequency_min"],
            )
            for cfg in SERVICES.values()
        )
        self.assertEqual(len(trains), minimum_active)
        self.assertGreater(sum(cfg["fleet_size"] for cfg in SERVICES.values()), len(trains))
        self.assertTrue(all(train.takt_anchors for train in trains))
        self.assertTrue(all(
            train.route[0] in train.takt_anchors and train.route[-1] in train.takt_anchors
            for train in trains
        ))

    def test_full_day_trip_plan_creates_all_departures_and_assigns_trainsets(self):
        plans = TimetableGenerator.generate_full_day_trip_plan()
        for service_id, trainsets in plans.items():
            config = SERVICES[service_id]
            start = time_to_seconds(config["start_time"])
            end = time_to_seconds(config["end_time"])
            frequency = config["frequency_min"] * 60
            departures_per_direction = (end - start) // frequency + 1
            trips = [trip for unit in trainsets for trip in unit.assigned_trips]
            self.assertEqual(len(trips), departures_per_direction * 2)
            self.assertEqual(len({trip.trip_id for trip in trips}), len(trips))
            for unit in trainsets:
                self.assertTrue(unit.assigned_trips)
                for previous, following in zip(unit.assigned_trips, unit.assigned_trips[1:]):
                    self.assertEqual(previous.destination, following.origin)
                    self.assertGreaterEqual(following.departure_seconds, previous.arrival_seconds + 90)
                    self.assertEqual(following.trainset_id, unit.trainset_id)

    def test_fleet_capacity_uses_running_time_and_turnback(self):
        route = ["STURA", "REBAUDENGO"]
        required = TimetableGenerator.required_fleet_size(
            route,
            frequency_min=10,
            travel_times={("STURA", "REBAUDENGO"): 10.0},
            turnback_seconds=120,
        )
        self.assertEqual(required, 4)

    def test_fleet_capacity_is_derived_from_route_and_frequency(self):
        route = ["STURA", "REBAUDENGO", "DORA", "PORTA_SUSA"]
        required = TimetableGenerator.required_fleet_size(route, frequency_min=10)
        self.assertGreaterEqual(required, 2)
        self.assertEqual(required % 2, 0)

    def test_fleet_manager_rejects_an_insufficient_fleet(self):
        with self.assertRaises(FleetCapacityError):
            FleetManager.plan_service(
                service_id="TEST",
                route=["A", "B"],
                base_train_number=1,
                fleet_size=2,
                start_seconds=0,
                end_seconds=1200,
                frequency_seconds=600,
                one_way_running_seconds=1200,
                turnback_seconds=120,
            )

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
