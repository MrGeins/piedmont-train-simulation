"""A single scheduled passenger-service movement."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Trip:
    trip_id: str
    service_id: str
    direction: str
    origin: str
    destination: str
    departure_seconds: int
    arrival_seconds: int
    trainset_id: int

    def __post_init__(self) -> None:
        if self.arrival_seconds <= self.departure_seconds:
            raise ValueError("trip arrival must be later than departure")
