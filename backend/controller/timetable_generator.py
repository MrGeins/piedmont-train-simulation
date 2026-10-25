from backend.controller.train_agent import TrainAgent
from backend.utils.time_formatter import time_to_seconds, seconds_to_string
from backend.data.stations_data import stations_registry
from backend.data.schedules_service import ROUTES, PLATFORM_PLANS, TAKT_TEMPLATES


class TimetableGenerator:
    @staticmethod
    def parse_takt_leg_times(
        takt_dict: dict[str, str],
        route_order: list[str]
    ) -> tuple[dict[tuple[str, str], float], dict[str, float], int | None]:
        """
        Analizza i token orari di una direzione ("p:MM", "MM-MM", "a:MM") lungo route_order
        e restituisce:
        - travel_times: {(st_from, st_to): minuti_percorrenza}
        - dwell_times: {st_key: minuti_sosta}
        - start_minute: intero del minuto di partenza (p:MM) dal capolinea
        """
        travel_times = {}
        dwell_times = {}
        start_minute = None
        prev_dep_min = None
        prev_st = None

        for st_key in route_order:
            token = takt_dict.get(st_key)
            if not token:
                continue
            token = token.strip()
            if token.startswith("p:"):
                dep_m = int(token.split(":")[1])
                start_minute = dep_m
                prev_dep_min = dep_m
                prev_st = st_key
            elif token.startswith("a:"):
                arr_m = int(token.split(":")[1])
                if prev_dep_min is not None and prev_st is not None:
                    diff = (arr_m - prev_dep_min) % 60
                    travel_times[(prev_st, st_key)] = float(diff if diff > 0 else 4.0)
            elif "-" in token:
                arr_s, dep_s = token.split("-")
                arr_m, dep_m = int(arr_s), int(dep_s)
                if prev_dep_min is not None and prev_st is not None:
                    diff = (arr_m - prev_dep_min) % 60
                    travel_times[(prev_st, st_key)] = float(diff if diff > 0 else 3.0)
                dwell = (dep_m - arr_m) % 60
                dwell_times[st_key] = float(max(1, dwell))
                prev_dep_min = dep_m
                prev_st = st_key

        return travel_times, dwell_times, start_minute

    @staticmethod
    def align_to_takt_minute(base_time_sec: int, target_minute: int | None) -> int:
        """Allinea l'orario di partenza iniziale al primo scoccare del minuto target_minute (p:MM)."""
        if target_minute is None:
            return base_time_sec
        base_h = base_time_sec // 3600
        base_m = (base_time_sec % 3600) // 60
        if target_minute >= base_m:
            return base_h * 3600 + target_minute * 60
        else:
            return (base_h + 1) * 3600 + target_minute * 60

    @classmethod
    def build_directional_schedules(cls, route_key: str, route: list) -> tuple[dict[str, int], dict[str, int]]:
        """Costruisce i piani binari per la direzione base (forward) e opposta (reverse)."""
        explicit_plan = PLATFORM_PLANS.get(route_key, {})
        forward_sched = {}
        reverse_sched = {}

        for i, st_key in enumerate(route):
            st_obj = stations_registry.get(st_key)
            avail = st_obj.available_tracks if st_obj and st_obj.available_tracks else [1]
            is_endpoint = (i == 0 or i == len(route) - 1)

            if st_key in explicit_plan and explicit_plan[st_key] in avail:
                fwd_tr = explicit_plan[st_key]
            else:
                fwd_tr = avail[0]
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
    def generate_full_day_timetable(cls) -> list[TrainAgent]:
        all_trains = []

        for template_key, cfg in TAKT_TEMPLATES.items():
            service_id = cfg.get("service_id", template_key)
            route_key = cfg.get("route_key", service_id)
            base_route = ROUTES.get(route_key, [])
            if not base_route:
                continue

            base_num = cfg.get("base_num", 1000)
            fleet_size = cfg.get("fleet_size", 4)
            end_str = cfg.get("end_time", "23:00:00")
            freq_sec = cfg.get("frequency_min", 60) * 60

            default_start = cfg.get("start_time", "05:00:00")
            start_south_str = cfg.get("start_time_south", default_start)
            start_north_str = cfg.get("start_time_north", default_start)

            start_sec_south = time_to_seconds(start_south_str)
            start_sec_north = time_to_seconds(start_north_str)

            fwd_sched, rev_sched = cls.build_directional_schedules(route_key, base_route)

            custom_travel = {}
            custom_dwell = {}
            dir_routes = {}
            dir_start_mins = {}

            for dir_key in ["SOUTH", "NORTH"]:
                if dir_key in cfg:
                    dir_dict = cfg[dir_key]
                    first_st = next(iter(dir_dict.keys()), None)
                    ordered_r = (
                        list(base_route)
                        if first_st == base_route[0]
                        else list(reversed(base_route))
                    )
                    dir_routes[dir_key] = ordered_r

                    t_map, d_map, p_min = cls.parse_takt_leg_times(dir_dict, ordered_r)
                    dir_start_mins[dir_key] = p_min
                    custom_travel.update(t_map)
                    for st_k, dw_val in d_map.items():
                        custom_dwell[(ordered_r[0], st_k)] = dw_val

            anchor_south = cls.align_to_takt_minute(start_sec_south, dir_start_mins.get("SOUTH"))
            anchor_north = cls.align_to_takt_minute(start_sec_north, dir_start_mins.get("NORTH"))

            dir_anchors = {
                "SOUTH": anchor_south,
                "NORTH": anchor_north,
            }

            station_anchors = {}
            if "SOUTH" in dir_routes:
                station_anchors[dir_routes["SOUTH"][0]] = anchor_south
            if "NORTH" in dir_routes:
                station_anchors[dir_routes["NORTH"][0]] = anchor_north

            for idx in range(fleet_size):
                dir_key = "SOUTH" if idx % 2 == 0 else "NORTH"
                if dir_key not in dir_routes:
                    dir_key = "SOUTH" if "SOUTH" in dir_routes else "NORTH"

                initial_route = dir_routes[dir_key]
                is_reverse = (initial_route[0] != base_route[0])
                wave = idx // 2

                first_dep_sec = dir_anchors[dir_key]
                dep_seconds = first_dep_sec + (wave * freq_sec)
                dep_str = seconds_to_string(dep_seconds)

                # Numerazione pari per SOUTH, dispari per NORTH
                train_num = base_num + (wave * 2) + (1 if dir_key == "NORTH" else 0)

                agent = TrainAgent(
                    service_id=service_id,
                    train_number=train_num,
                    route=list(initial_route),
                    departure_time_str=dep_str,
                    end_service_str=end_str,
                    forward_platforms=fwd_sched,
                    reverse_platforms=rev_sched,
                    is_reverse_direction=is_reverse,
                    custom_travel_times=custom_travel,
                    custom_dwell_times=custom_dwell,
                    takt_anchors=station_anchors,
                    frequency_seconds=freq_sec
                )
                all_trains.append(agent)

        return all_trains