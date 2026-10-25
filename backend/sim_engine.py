import random
import time
import threading
from backend.utils.time_formatter import seconds_to_string, time_to_seconds
from backend.network_graph import infrastructure_map, stations_registry, stations
from backend.controller.timetable_generator import TimetableGenerator
from backend.controller.interlocking_system import InterlockingSystem


class SimEngine:
    def __init__(self, start_time_str: str, end_time_str: str):
        self.sim_current_time = time_to_seconds(start_time_str)
        self.sim_end_time = time_to_seconds(end_time_str)
        self.active_trains = []
        self.is_running = False
        self.is_paused = False
        self.speed_multiplier = 1
        self.on_tick_callback = None
        self.rush_hour_stress = False
        self.interlocking = InterlockingSystem()

    def register_callback(self, callback_function):
        self.on_tick_callback = callback_function

    def toggle_rush_hour_stress(self, status: bool):
        self.rush_hour_stress = status

    def set_paused(self, paused: bool):
        self.is_paused = paused

    def set_speed(self, multiplier: int):
        self.speed_multiplier = max(1, multiplier)
        self.is_paused = False

    def initialize_timetable(self):
        self.active_trains = TimetableGenerator.generate_full_day_timetable()

    def start_sim(self):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._sim_loop, daemon=True).start()

    def _sim_loop(self):
        base_time_step = 10.0
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue

            self.sim_current_time += int(base_time_step)

            for train in self.active_trains:
                prev_status = train.status
                old_train_num = train.train_number

                if train.status == "RUNNING":
                    station_from = train.route[train.current_station_index]
                    station_to = train.route[train.current_station_index + 1]
                    preferred_track = train.get_scheduled_track(station_to)
                    is_final_stop = (train.current_station_index + 1 == len(train.route) - 1)
                    rem_route = train.route[train.current_station_index:]

                    assigned_platform = self.interlocking.request_track_clearance(
                        train.train_number,
                        station_from,
                        station_to,
                        infrastructure_map,
                        preferred_track=preferred_track,
                        is_terminating=is_final_stop,
                        remaining_route=rem_route
                    )

                    if assigned_platform is not None:
                        train.assigned_track = assigned_platform
                        train.track_changed = (assigned_platform != preferred_track)
                        self.interlocking.release_platform(train.train_number, station_from)

                        train.update_position(
                            base_time_step, self.sim_current_time, infrastructure_map, stations_registry, stations
                        )

                        if train.status == "TURNAROUND":
                            self.interlocking.release_track_section(train.train_number, station_from, station_to)
                    else:
                        train.accumulated_delay += int(base_time_step)

                else:
                    if train.status == "DWELLING" and self.rush_hour_stress:
                        if random.random() < 0.35:
                            additional_delay = random.randint(10, 45)
                            train.accumulated_delay += additional_delay
                            train.dwell_timer += float(additional_delay)

                    train.update_position(
                        base_time_step, self.sim_current_time, infrastructure_map, stations_registry, stations
                    )

                    if train.train_number != old_train_num:
                        self.interlocking.rename_train_id(old_train_num, train.train_number)

                    if train.status == "RUNNING" and prev_status == "DWELLING":
                        station_prev = train.route[train.current_station_index - 1]
                        station_curr = train.route[train.current_station_index]
                        self.interlocking.release_track_section(train.train_number, station_prev, station_curr)

                    elif train.status == "TERMINATED" and prev_status == "TURNAROUND":
                        station_prev = train.route[-2]
                        station_curr = train.route[-1]
                        self.interlocking.release_track_section(old_train_num, station_prev, station_curr)
                        self.interlocking.release_platform(old_train_num, station_curr)

            if self.on_tick_callback:
                current_time_str = seconds_to_string(self.sim_current_time)
                self.on_tick_callback(current_time_str, self.active_trains)

            sleep_duration = 1.0 / float(self.speed_multiplier)
            time.sleep(max(0.05, sleep_duration))