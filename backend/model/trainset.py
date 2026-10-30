"""A physical rolling-stock unit and its assigned sequence of trips."""

from dataclasses import dataclass, field

from backend.model.trip import Trip


@dataclass
class Trainset:
    trainset_id: int
    service_id: str
    location: str
    available_at: int
    assigned_trips: list[Trip] = field(default_factory=list)

    def assign_trip(self, trip: Trip, turnback_seconds: int) -> None:
        if trip.service_id != self.service_id:
            raise ValueError("trip service does not match trainset service")
        if trip.origin != self.location:
            raise ValueError(
                f"trainset {self.trainset_id} is at {self.location}, not {trip.origin}"
            )
        if trip.departure_seconds < self.available_at:
            raise ValueError(f"trainset {self.trainset_id} is not available for trip {trip.trip_id}")
        self.assigned_trips.append(trip)
        self.location = trip.destination
        self.available_at = trip.arrival_seconds + turnback_seconds
