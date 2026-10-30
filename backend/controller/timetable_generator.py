"""Generate explicit trip plans and reusable physical trainset agents."""

from backend.controller.train_agent import TrainAgent
from backend.controller.fleet_manager import FleetManager
from backend.utils.time_formatter import time_to_seconds, seconds_to_string
from backend.network_graph import stations_registry, infrastructure_map
from backend.controller.pathfinder import get_physical_path
from backend.data.schedules_service import ROUTES, PLATFORM_PLANS, SERVICES
from backend.railway.travel_time_calculator import (
    MissingOperationalDataError,
    TravelTimeCalculator,
)
from backend.railway.vehicle_performance import VehiclePerformance


class TimetableGenerator:
    # Compatibility fallback used only until a link has measured operational data.
    DEFAULT_SEGMENT_TRAVEL_MINUTES = TrainAgent.DEFAULT_SEGMENT_TRAVEL_MINUTES
    DEFAULT_TURNBACK_SECONDS = 90

    @classmethod
    def build_directional_schedules(cls, route_key: str, route: list) -> tuple[dict[str, int], dict[str, int]]:
        """Build the default and opposite-direction platform plans."""
        explicit_plan = PLATFORM_PLANS.get(route_key, {})
        forward_sched = {}
        reverse_sched = {}
        for i, st_key in enumerate(route):
            st_obj = stations_registry.get(st_key)
            avail = st_obj.available_tracks if st_obj and st_obj.available_tracks else [1]
            is_endpoint = i == 0 or i == len(route) - 1
            fwd_tr = explicit_plan.get(st_key) if explicit_plan.get(st_key) in avail else avail[0]
            forward_sched[st_key] = fwd_tr
            if is_endpoint or len(avail) == 1:
                rev_tr = fwd_tr
            else:
                non_stub_avail = [t for t in avail if not (st_obj and st_obj.is_stub_track(t))]
                if not non_stub_avail:
                    non_stub_avail = avail
                if fwd_tr in non_stub_avail and len(non_stub_avail) >= 2:
                    idx = non_stub_avail.index(fwd_tr)
                    rev_tr = non_stub_avail[len(non_stub_avail) - 1 - idx]
                    if rev_tr == fwd_tr:
                        rev_tr = non_stub_avail[(idx + 1) % len(non_stub_avail)]
                else:
                    rev_tr = non_stub_avail[0]
            reverse_sched[st_key] = rev_tr
        return forward_sched, reverse_sched

    @classmethod
    def _build_route_travel_times(
        cls,
        route: list[str],
        calculator: TravelTimeCalculator | None,
        vehicle: VehiclePerformance | None,
    ) -> dict[tuple[str, str], float]:
        """Return directional station-to-station times in minutes.

        If operational data is incomplete, retain the legacy simulation fallback
        for that station pair. The fallback is not presented as a real running time.
        """
        result: dict[tuple[str, str], float] = {}
        for start, end in zip(route, route[1:]):
            if calculator is not None and vehicle is not None:
                physical_path = get_physical_path(start, end, infrastructure_map)
                try:
                    result[(start, end)] = calculator.calculate_path_minutes(
                        physical_path, infrastructure_map, vehicle
                    )
                    continue
                except MissingOperationalDataError:
                    pass
            result[(start, end)] = cls.DEFAULT_SEGMENT_TRAVEL_MINUTES
        return result

    @staticmethod
    def validate_generated_timetable(trains: list[TrainAgent]) -> None:
        """Fail fast when generated trains reference invalid stations or platform tracks."""
        errors = []
        seen_numbers = set()
        for index, train in enumerate(trains):
            label = f"trains[{index}] (number={train.train_number})"
            if train.train_number in seen_numbers:
                errors.append(f"{label}: duplicate train number")
            seen_numbers.add(train.train_number)
            if not train.route:
                errors.append(f"{label}: route must not be empty")
                continue
            for station_key in train.route:
                station = stations_registry.get(station_key)
                if station is None:
                    errors.append(f"{label}: route references unknown station {station_key!r}")
                    continue
                for plan_name in ("forward_platforms", "reverse_platforms"):
                    track = getattr(train, plan_name, {}).get(station_key)
                    if track not in station.available_tracks:
                        errors.append(
                            f"{label}: {plan_name} selects unavailable track {track!r} "
                            f"at {station_key}; available={station.available_tracks}"
                        )
        if errors:
            raise ValueError("Generated timetable validation failed:\\n- " + "\\n- ".join(errors))

    @classmethod
    def required_fleet_size(
        cls,
        route: list[str],
        frequency_min: int,
        travel_times: dict[tuple[str, str], float] | None = None,
        turnback_seconds: int = DEFAULT_TURNBACK_SECONDS,
    ) -> int:
        """Calculate the even fleet minimum for a bidirectional service."""
        if frequency_min <= 0:
            raise ValueError("frequency_min must be positive")
        if turnback_seconds < 0:
            raise ValueError("turnback_seconds must be non-negative")
        travel_times = travel_times or {}
        one_way_travel_seconds = sum(
            travel_times.get((start, end), cls.DEFAULT_SEGMENT_TRAVEL_MINUTES) * 60
            for start, end in zip(route, route[1:])
        )
        dwell_minutes = sum(
            stations_registry[station].default_dwell
            for station in route[1:-1]
            if station in stations_registry
        )
        one_way_seconds = one_way_travel_seconds + dwell_minutes * 60
        round_trip_seconds = 2 * one_way_seconds + 2 * turnback_seconds
        headway_seconds = frequency_min * 60
        units_per_terminal = max(
            1,
            (round_trip_seconds + (2 * headway_seconds) - 1) // (2 * headway_seconds),
        )
        return 2 * units_per_terminal

    @classmethod
    def generate_full_day_trip_plan(
        cls,
        travel_time_calculator: TravelTimeCalculator | None = None,
        vehicle_performance: VehiclePerformance | None = None,
    ):
        """Generate every scheduled directional trip and assign it to trainsets."""
        if (travel_time_calculator is None) != (vehicle_performance is None):
            raise ValueError("travel_time_calculator and vehicle_performance must be provided together")

        plans = {}
        for service_key, cfg in SERVICES.items():
            service_id = cfg["service_id"]
            route = ROUTES.get(service_id, [])
            if not route:
                continue

            forward_times = cls._build_route_travel_times(
                route, travel_time_calculator, vehicle_performance
            )
            one_way_travel_seconds = sum(forward_times.values()) * 60
            dwell_seconds = sum(
                stations_registry[station].default_dwell * 60
                for station in route[1:-1]
                if station in stations_registry
            )
            one_way_running_seconds = int(one_way_travel_seconds + dwell_seconds)
            turnback_seconds = (
                vehicle_performance.minimum_turnback_seconds
                if vehicle_performance is not None
                else cls.DEFAULT_TURNBACK_SECONDS
            )
            required = cls.required_fleet_size(
                route, cfg["frequency_min"], forward_times, turnback_seconds
            )
            if cfg["fleet_size"] < required:
                raise ValueError(
                    f"Service {service_id} has fleet_size={cfg['fleet_size']}, "
                    f"but its bidirectional timetable requires at least {required} trainsets"
                )

            trainsets = FleetManager.plan_service(
                service_id=service_id,
                route=route,
                base_train_number=cfg["base_num"],
                # Only the minimum active fleet is dispatched; additional configured
                # units remain reserve stock and must not create duplicate departures.
                fleet_size=required,
                start_seconds=time_to_seconds(cfg["start_time"]),
                end_seconds=time_to_seconds(cfg["end_time"]),
                frequency_seconds=cfg["frequency_min"] * 60,
                one_way_running_seconds=one_way_running_seconds,
                turnback_seconds=turnback_seconds,
            )
            plans[service_key] = trainsets
        return plans

    @classmethod
    def generate_full_day_timetable(
        cls,
        travel_time_calculator: TravelTimeCalculator | None = None,
        vehicle_performance: VehiclePerformance | None = None,
    ) -> list[TrainAgent]:
        """Create one runtime agent per trainset from its first assigned trip."""
        plans = cls.generate_full_day_trip_plan(travel_time_calculator, vehicle_performance)
        all_trains = []
        for service_key, trainsets in plans.items():
            cfg = SERVICES[service_key]
            service_id = cfg["service_id"]
            route = ROUTES[service_id]
            forward, reverse = cls.build_directional_schedules(service_id, route)
            forward_times = cls._build_route_travel_times(
                route, travel_time_calculator, vehicle_performance
            )
            reverse_times = {(end, start): minutes for (start, end), minutes in forward_times.items()}
            cycle_times = {**forward_times, **reverse_times}
            start_seconds = time_to_seconds(cfg["start_time"])

            for trainset in trainsets:
                if not trainset.assigned_trips:
                    continue
                first_trip = trainset.assigned_trips[0]
                is_reverse = first_trip.direction == "REVERSE"
                initial_route = list(reversed(route)) if is_reverse else list(route)
                agent = TrainAgent(
                    service_id=service_id,
                    train_number=trainset.trainset_id,
                    route=initial_route,
                    departure_time_str=seconds_to_string(first_trip.departure_seconds),
                    end_service_str=cfg["end_time"],
                    forward_platforms=forward,
                    reverse_platforms=reverse,
                    is_reverse_direction=is_reverse,
                    custom_travel_times=cycle_times,
                    custom_dwell_times={},
                    takt_anchors={route[0]: start_seconds, route[-1]: start_seconds},
                    frequency_seconds=cfg["frequency_min"] * 60,
                )
                all_trains.append(agent)

        cls.validate_generated_timetable(all_trains)
        return all_trains
