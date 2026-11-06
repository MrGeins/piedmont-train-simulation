from backend.utils.time_formatter import time_to_seconds, seconds_to_string
from backend.controller.pathfinder import interpolate_along_tracks, get_active_physical_edge


class TrainAgent:
    DEFAULT_SEGMENT_TRAVEL_MINUTES = 3.0

    def __init__(
        self,
        service_id: str,
        train_number: int,
        route: list,
        departure_time_str: str,
        end_service_str: str = "23:30:00",
        forward_platforms: dict[str, int] | None = None,
        reverse_platforms: dict[str, int] | None = None,
        is_reverse_direction: bool = False,
        custom_travel_times: dict[tuple[str, str], float] | None = None,
        custom_dwell_times: dict[tuple[str, str], float] | None = None,
        takt_anchors: dict[str, int] | None = None,
        frequency_seconds: int = 3600,
        claimed_slots: set[tuple[str, int]] | None = None
    ):
        self.service_id = service_id
        self.train_number = train_number
        self.route = list(route)
        self.current_station_index = 0

        self.departure_time = time_to_seconds(departure_time_str)
        self.next_departure_time = self.departure_time
        self.end_service_time = time_to_seconds(end_service_str)
        self.current_progress = 0.0
        self.accumulated_delay = 0
        self.dwell_timer = 0.0

        self.status = "PENDING"
        self.current_x = 0.0
        self.current_y = 0.0

        self.forward_platforms = forward_platforms or {}
        self.reverse_platforms = reverse_platforms or {}
        self.is_reverse = is_reverse_direction

        self.custom_travel_times = custom_travel_times or {}
        self.custom_dwell_times = custom_dwell_times or {}
        self.takt_anchors = takt_anchors or {}
        self.frequency_seconds = frequency_seconds
        self.claimed_slots = claimed_slots if claimed_slots is not None else set()

        first_station = self.route[0] if self.route else ""
        self.assigned_track = self.get_scheduled_track(first_station)
        self.departure_track = self.assigned_track
        self.track_changed = False

        self.claimed_slots.add((first_station, self.departure_time))

        self.last_departure_time = self.departure_time
        self.expected_arrival_time = self.departure_time + int(self._get_leg_minutes(0) * 60)
        self.planned_departure_time = self.departure_time

        self.current_physical_edge: tuple[str, str] | None = None

    def _get_leg_minutes(self, station_idx: int) -> float:
        if station_idx + 1 >= len(self.route):
            return 3.0
        u, v = self.route[station_idx], self.route[station_idx + 1]
        val = self.custom_travel_times.get((u, v), self.DEFAULT_SEGMENT_TRAVEL_MINUTES)
        return val if val > 0 else self.DEFAULT_SEGMENT_TRAVEL_MINUTES

    def get_scheduled_track(self, station_key: str) -> int:
        active_plan = self.reverse_platforms if self.is_reverse else self.forward_platforms
        return active_plan.get(station_key, 1)

    def get_last_dep_str(self) -> str:
        return seconds_to_string(self.last_departure_time)[:5]

    def get_next_arr_str(self) -> str:
        return seconds_to_string(self.expected_arrival_time)[:5]

    def get_planned_dep_str(self) -> str:
        return seconds_to_string(self.planned_departure_time)[:5]

    def _compute_next_departure_time(self, terminal_key: str, current_sim_time: int) -> int:
        min_turnaround_sec = 90
        earliest_dep = current_sim_time + min_turnaround_sec

        anchor_sec = self.takt_anchors.get(terminal_key)
        if anchor_sec is None or self.frequency_seconds <= 0:
            candidate = earliest_dep
        elif earliest_dep <= anchor_sec:
            candidate = anchor_sec
        else:
            elapsed = earliest_dep - anchor_sec
            steps = (elapsed + self.frequency_seconds - 1) // self.frequency_seconds
            candidate = anchor_sec + (steps * self.frequency_seconds)

        while (terminal_key, candidate) in self.claimed_slots:
            candidate += self.frequency_seconds

        self.claimed_slots.add((terminal_key, candidate))
        return candidate

    def _enter_turnaround(self, current_sim_time: int):
        self.current_station_index = len(self.route) - 1
        self.status = "TURNAROUND"
        self.current_physical_edge = None
        terminal_key = self.route[-1]
        self.next_departure_time = self._compute_next_departure_time(terminal_key, current_sim_time)
        self.planned_departure_time = self.next_departure_time
        self.dwell_timer = float(max(0, self.next_departure_time - current_sim_time))

    def update_position(
        self,
        tick_seconds: float,
        current_sim_time: int,
        infrastructure_network: list,
        stations_registry: dict,
        stations_coord: dict
    ):
        if self.status == "PENDING":
            if current_sim_time >= self.departure_time:
                self.status = "RUNNING"
                self.current_progress = 0.0
                self.departure_track = self.assigned_track
                self.last_departure_time = current_sim_time
                self.expected_arrival_time = current_sim_time + int(self._get_leg_minutes(0) * 60)
                dep_station = stations_coord.get(self.route[0])
                if dep_station:
                    self.current_x = dep_station.get("x", 0)
                    self.current_y = dep_station.get("y", 0)
            return

        if self.status == "TERMINATED":
            self.current_physical_edge = None
            return

        if self.status == "TURNAROUND":
            terminal_key = self.route[-1]
            target_station = stations_coord.get(terminal_key)
            if target_station:
                self.current_x = target_station.get("x", 0)
                self.current_y = target_station.get("y", 0)

            self.dwell_timer = float(max(0, self.next_departure_time - current_sim_time))
            self.planned_departure_time = self.next_departure_time

            if current_sim_time >= self.next_departure_time:
                if current_sim_time >= self.end_service_time:
                    self.status = "TERMINATED"
                else:
                    self.route.reverse()
                    self.is_reverse = not self.is_reverse
                    self.current_station_index = 0
                    self.current_progress = 0.0
                    self.train_number += 2
                    self.accumulated_delay = 0
                    self.departure_track = self.assigned_track
                    self.last_departure_time = current_sim_time
                    self.expected_arrival_time = current_sim_time + int(self._get_leg_minutes(0) * 60)
                    self.status = "RUNNING"
            return

        if self.current_station_index + 1 >= len(self.route):
            self._enter_turnaround(current_sim_time)
            return

        station_from_key = self.route[self.current_station_index]
        station_to_key = self.route[self.current_station_index + 1]

        if self.status == "DWELLING":
            self.dwell_timer -= tick_seconds
            self.current_physical_edge = None
            target_station = stations_coord.get(station_to_key)
            if target_station:
                self.current_x = target_station.get("x", 0)
                self.current_y = target_station.get("y", 0)

            if self.dwell_timer <= 0:
                self.current_station_index += 1
                if self.current_station_index >= len(self.route) - 1:
                    self._enter_turnaround(current_sim_time)
                else:
                    self.status = "RUNNING"
                    self.current_progress = 0.0
                    self.departure_track = self.assigned_track
                    self.last_departure_time = current_sim_time
                    leg_sec = int(self._get_leg_minutes(self.current_station_index) * 60)
                    self.expected_arrival_time = current_sim_time + leg_sec
            return

        if self.status == "RUNNING":
            travel_time_minutes = self._get_leg_minutes(self.current_station_index)
            total_segment_seconds = travel_time_minutes * 60.0
            self.current_progress += tick_seconds / total_segment_seconds

            rem_seconds = max(0.0, (1.0 - self.current_progress) * total_segment_seconds)
            self.expected_arrival_time = current_sim_time + int(rem_seconds)

            if self.current_progress >= 1.0:
                self.current_progress = 1.0
                self.current_physical_edge = None

                if self.current_station_index + 1 >= len(self.route) - 1:
                    self._enter_turnaround(current_sim_time)
                else:
                    origin_key = self.route[0]
                    if (origin_key, station_to_key) in self.custom_dwell_times:
                        dwell_minutes = self.custom_dwell_times[(origin_key, station_to_key)]
                    else:
                        arrival_station_data = stations_registry.get(station_to_key)
                        dwell_minutes = arrival_station_data.default_dwell if arrival_station_data else 1.0

                    self.status = "DWELLING"
                    self.dwell_timer = max(0.5, dwell_minutes) * 60.0
                    self.planned_departure_time = current_sim_time + int(self.dwell_timer)
            else:
                self.current_physical_edge = get_active_physical_edge(
                    station_from_key, station_to_key, self.current_progress, infrastructure_network, stations_coord
                )

            self.current_x, self.current_y = interpolate_along_tracks(
                station_from_key, station_to_key, self.current_progress, infrastructure_network, stations_coord
            )