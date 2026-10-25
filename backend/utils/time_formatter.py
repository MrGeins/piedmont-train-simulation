def time_to_seconds(time_str: str) -> int:
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s


def seconds_to_string(total_seconds: int) -> str:
    h = (total_seconds // 3600) % 24
    m = (total_seconds // 60) % 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"