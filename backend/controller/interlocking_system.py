from backend.network_graph import stations_registry
from backend.controller.pathfinder import get_physical_path, is_segment_double_track, get_active_physical_edge


class InterlockingSystem:
    def __init__(self):
        self.single_track_locks = {}
        self.directional_blocks = {}

        self.station_platforms = {}
        for st_key, st_obj in stations_registry.items():
            self.station_platforms[st_key] = {}
            for track_num in range(1, st_obj.num_tracks + 1):
                if track_num in st_obj.available_tracks:
                    self.station_platforms[st_key][track_num] = None
                else:
                    self.station_platforms[st_key][track_num] = "RESERVED"

    def _get_undirected_key(self, node_a: str, node_b: str) -> tuple[str, str]:
        """Return a collision-safe key for an undirected physical section."""
        return (node_a, node_b) if node_a < node_b else (node_b, node_a)

    def rename_train_id(self, old_id: int, new_id: int):
        for st_key, platforms in self.station_platforms.items():
            for track_num, occupant in platforms.items():
                if occupant == old_id:
                    platforms[track_num] = new_id

        for sec_key, occ in list(self.single_track_locks.items()):
            if occ is not None and occ[0] == old_id:
                self.single_track_locks[sec_key] = (new_id, occ[1])

        for dir_key, occ in list(self.directional_blocks.items()):
            if occ == old_id:
                self.directional_blocks[dir_key] = new_id

    def allocate_platform(
        self,
        train_id: int,
        station_key: str,
        preferred_track: int | None = None,
        is_terminating: bool = False
    ) -> int | None:
        if station_key not in self.station_platforms:
            return None

        platforms = self.station_platforms[station_key]
        st_obj = stations_registry.get(station_key)
        available_list = st_obj.available_tracks if st_obj else list(platforms.keys())

        compatible_tracks = [
            t for t in available_list
            if is_terminating or not (st_obj and st_obj.is_stub_track(t))
        ]
        if not compatible_tracks:
            compatible_tracks = list(available_list)

        for track_num, occupant in platforms.items():
            if occupant == train_id:
                return track_num

        if preferred_track is not None and preferred_track in compatible_tracks:
            if platforms.get(preferred_track) is None:
                platforms[preferred_track] = train_id
                return preferred_track

        candidate_tracks = list(compatible_tracks)
        if preferred_track is not None:
            candidate_tracks.sort(key=lambda t: abs(t - preferred_track))

        for track_num in candidate_tracks:
            if platforms.get(track_num) is None:
                platforms[track_num] = train_id
                return track_num

        return None

    def release_platform(self, train_id: int, station_key: str):
        if station_key in self.station_platforms:
            for track_num, occupant in self.station_platforms[station_key].items():
                if occupant == train_id:
                    self.station_platforms[station_key][track_num] = None

    def release_all_train_blocks(self, train_id: int):
        for k, occ in list(self.single_track_locks.items()):
            if occ is not None and occ[0] == train_id:
                self.single_track_locks[k] = None
        for k, occ in list(self.directional_blocks.items()):
            if occ == train_id:
                self.directional_blocks[k] = None

    def request_track_clearance(
        self,
        train_id: int,
        node_from: str,
        node_to: str,
        infrastructure_network: list,
        preferred_track: int | None = None,
        is_terminating: bool = False,
        remaining_route: list[str] | None = None,
        current_progress: float = 0.0,
        stations_coord: dict | None = None
    ) -> int | None:
        phys_path = get_physical_path(node_from, node_to, infrastructure_network)

        if stations_coord and len(phys_path) >= 2:
            u_curr, v_curr = get_active_physical_edge(
                node_from, node_to, current_progress, infrastructure_network, stations_coord
            )
        else:
            u_curr, v_curr = node_from, node_to

        for i in range(len(phys_path) - 1):
            u, v = phys_path[i], phys_path[i + 1]
            if (u, v) == (u_curr, v_curr):
                break
            if self.directional_blocks.get((u, v)) == train_id:
                self.directional_blocks[(u, v)] = None

        is_double = is_segment_double_track(u_curr, v_curr, infrastructure_network)
        if is_double:
            occ_dir = self.directional_blocks.get((u_curr, v_curr))
            if occ_dir is not None and occ_dir != train_id:
                return None
        else:
            undir_k = self._get_undirected_key(u_curr, v_curr)
            occ_single = self.single_track_locks.get(undir_k)
            if occ_single is not None and occ_single[0] != train_id:
                return None

            if current_progress == 0.0 and remaining_route and len(remaining_route) >= 2:
                for i in range(len(remaining_route) - 1):
                    st_a, st_b = remaining_route[i], remaining_route[i + 1]
                    sub_path = get_physical_path(st_a, st_b, infrastructure_network)
                    for j in range(len(sub_path) - 1):
                        su, sv = sub_path[j], sub_path[j + 1]
                        if not is_segment_double_track(su, sv, infrastructure_network):
                            sk = self._get_undirected_key(su, sv)
                            s_occ = self.single_track_locks.get(sk)
                            if s_occ is not None and s_occ[0] != train_id and s_occ[1] == (sv, su):
                                return None
                    st_v_obj = stations_registry.get(st_b)
                    if st_v_obj and len(st_v_obj.available_tracks) == 1:
                        v_occ = self.station_platforms.get(st_b, {}).get(st_v_obj.available_tracks[0])
                        if v_occ is not None and v_occ != train_id:
                            return None
                    else:
                        break

        assigned_track = self.allocate_platform(
            train_id, node_to, preferred_track=preferred_track, is_terminating=is_terminating
        )
        if assigned_track is None:
            return None

        if is_double:
            self.directional_blocks[(u_curr, v_curr)] = train_id
        else:
            for i in range(len(phys_path) - 1):
                su, sv = phys_path[i], phys_path[i + 1]
                if not is_segment_double_track(su, sv, infrastructure_network):
                    sk = self._get_undirected_key(su, sv)
                    self.single_track_locks[sk] = (train_id, (su, sv))

        return assigned_track

    def release_track_section(
        self,
        train_id: int,
        node_from: str,
        node_to: str,
        infrastructure_network: list | None = None,
    ):
        """Release only the physical blocks belonging to the completed station-to-station leg."""
        if infrastructure_network:
            phys_path = get_physical_path(node_from, node_to, infrastructure_network)
        else:
            phys_path = [node_from, node_to]

        for index in range(len(phys_path) - 1):
            u, v = phys_path[index], phys_path[index + 1]
            section_key = self._get_undirected_key(u, v)
            occupant = self.single_track_locks.get(section_key)
            if occupant is not None and occupant[0] == train_id:
                self.single_track_locks[section_key] = None

            for direction in ((u, v), (v, u)):
                if self.directional_blocks.get(direction) == train_id:
                    self.directional_blocks[direction] = None