import math
from collections import deque

_PATH_CACHE = {}
_EDGE_DOUBLE_CACHE = {}


def get_physical_path(start_node: str, end_node: str, infrastructure_network: list) -> list[str]:
    if start_node == end_node:
        return [start_node]
    cache_key = (start_node, end_node)
    if cache_key in _PATH_CACHE:
        return _PATH_CACHE[cache_key]

    adj = {}
    for track in infrastructure_network:
        adj.setdefault(track.node_from, []).append(track.node_to)
        adj.setdefault(track.node_to, []).append(track.node_from)

    queue = deque([[start_node]])
    visited = {start_node}
    while queue:
        path = queue.popleft()
        curr = path[-1]
        for neighbor in adj.get(curr, []):
            if neighbor == end_node:
                result = path + [neighbor]
                _PATH_CACHE[cache_key] = result
                return result
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return [start_node, end_node]


def is_segment_double_track(u: str, v: str, infrastructure_network: list) -> bool:
    key = (u, v) if u < v else (v, u)
    if key in _EDGE_DOUBLE_CACHE:
        return _EDGE_DOUBLE_CACHE[key]
    for track in infrastructure_network:
        if (track.node_from == u and track.node_to == v) or (track.node_from == v and track.node_to == u):
            _EDGE_DOUBLE_CACHE[key] = track.double_track
            return track.double_track
    return False


def get_active_physical_edge(
    start_node: str,
    end_node: str,
    progress: float,
    infrastructure_network: list,
    stations_coord: dict
) -> tuple[str, str]:
    progress = max(0.0, min(1.0, progress))
    path = get_physical_path(start_node, end_node, infrastructure_network)
    valid_nodes = [n for n in path if n in stations_coord]
    if len(valid_nodes) < 2:
        return (start_node, end_node)

    points = [(stations_coord[n].get("x", 0), stations_coord[n].get("y", 0)) for n in valid_nodes]
    seg_lengths = []
    total_length = 0.0
    for i in range(len(points) - 1):
        d = math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        seg_lengths.append(d)
        total_length += d

    if total_length <= 0:
        return (valid_nodes[0], valid_nodes[1])

    target_dist = progress * total_length
    accumulated = 0.0
    for i, seg_len in enumerate(seg_lengths):
        if accumulated + seg_len >= target_dist or i == len(seg_lengths) - 1:
            return (valid_nodes[i], valid_nodes[i + 1])
        accumulated += seg_len

    return (valid_nodes[-2], valid_nodes[-1])


def interpolate_along_tracks(
    start_node: str,
    end_node: str,
    progress: float,
    infrastructure_network: list,
    stations_coord: dict
) -> tuple[float, float]:
    progress = max(0.0, min(1.0, progress))
    path = get_physical_path(start_node, end_node, infrastructure_network)

    valid_nodes = [n for n in path if n in stations_coord]
    points = [
        (stations_coord[n].get("x", 0), stations_coord[n].get("y", 0))
        for n in valid_nodes
    ]
    if not points:
        return 0.0, 0.0
    if len(points) == 1:
        return points[0]

    seg_lengths = []
    total_length = 0.0
    for i in range(len(points) - 1):
        d = math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        seg_lengths.append(d)
        total_length += d

    if total_length == 0:
        return points[0]

    target_dist = progress * total_length
    accumulated = 0.0
    for i, seg_len in enumerate(seg_lengths):
        if accumulated + seg_len >= target_dist or i == len(seg_lengths) - 1:
            local_t = (target_dist - accumulated) / seg_len if seg_len > 0 else 0.0
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            cx = points[i][0] + dx * local_t
            cy = points[i][1] + dy * local_t

            u_node, v_node = valid_nodes[i], valid_nodes[i + 1]
            if seg_len > 0 and is_segment_double_track(u_node, v_node, infrastructure_network):
                track_offset = 2.5 / 3.5
                lx = (dy / seg_len) * track_offset
                ly = (-dx / seg_len) * track_offset
                cx += lx
                cy += ly

            return cx, cy
        accumulated += seg_len

    return points[-1]