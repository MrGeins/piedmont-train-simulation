class RailwayStation:
    def __init__(
        self,
        key: str,
        name: str,
        roro_station: bool,
        default_dwell: float,
        terminal: bool = False,
        num_tracks: int = 2,
        available_tracks: list[int] | None = None,
        stub_tracks: dict[int, str] | None = None
    ):
        self.key = key
        self.name = name
        self.roro_station = roro_station
        self.default_dwell = default_dwell
        self.terminal = terminal
        self.num_tracks = num_tracks
        self.available_tracks = (
            list(available_tracks)
            if available_tracks is not None
            else list(range(1, num_tracks + 1))
        )
        self.stub_tracks = dict(stub_tracks) if stub_tracks is not None else {}

    def is_stub_track(self, track_num: int) -> bool:
        return track_num in self.stub_tracks


class RailwayLine:
    def __init__(self, node_from: str, node_to: str, double_track: bool):
        self.node_from = node_from
        self.node_to = node_to
        self.double_track = double_track