"""Allocate scheduled trips to physical trainsets."""

from __future__ import annotations

from backend.model.trainset import Trainset
from backend.model.trip import Trip


class FleetCapacityError(ValueError):
    """Raised when the available trainsets cannot cover the requested timetable."""


class FleetManager:
    @staticmethod
    def plan_service(
        service_id: str,
        route: list[str],
        base_train_number: int,
        fleet_size: int,
        start_seconds: int,
        end_seconds: int,
        frequency_seconds: int,
        one_way_running_seconds: int,
        turnback_seconds: int,
    ) -> list[Trainset]:
        """Build every directional trip and assign it to a compatible trainset.

        The initial fleet is distributed evenly between the two terminals.
        Each assignment updates the trainset's location and next availability.
        """
        if len(route) < 2:
            raise ValueError(f"service {service_id} route must contain at least two stations")
        if fleet_size < 2 or fleet_size % 2:
            raise ValueError("bidirectional services require an even fleet_size of at least two")
        if frequency_seconds <= 0 or one_way_running_seconds <= 0:
            raise ValueError("frequency and running time must be positive")
        if turnback_seconds < 0:
            raise ValueError("turnback_seconds must be non-negative")
        if end_seconds < start_seconds:
            raise ValueError("service end time must not precede start time")

        midpoint = fleet_size // 2
        trainsets = [
            Trainset(
                trainset_id=base_train_number + index,
                service_id=service_id,
                location=route[0] if index < midpoint else route[-1],
                available_at=start_seconds,
            )
            for index in range(fleet_size)
        ]

        departures: list[tuple[int, str, str, str]] = []
        departure_seconds = start_seconds
        while departure_seconds <= end_seconds:
            departures.append((departure_seconds, "FORWARD", route[0], route[-1]))
            departures.append((departure_seconds, "REVERSE", route[-1], route[0]))
            departure_seconds += frequency_seconds
        departures.sort(key=lambda item: (item[0], item[1]))

        for departure, direction, origin, destination in departures:
            candidates = [
                unit for unit in trainsets
                if unit.location == origin and unit.available_at <= departure
            ]
            if not candidates:
                raise FleetCapacityError(
                    f"service {service_id} has no trainset available at {origin} "
                    f"for {direction} departure at {departure}; "
                    f"configured fleet_size={fleet_size}"
                )
            unit = min(candidates, key=lambda item: (item.available_at, item.trainset_id))
            trip = Trip(
                trip_id=f"{service_id}:{direction}:{departure}",
                service_id=service_id,
                direction=direction,
                origin=origin,
                destination=destination,
                departure_seconds=departure,
                arrival_seconds=departure + one_way_running_seconds,
                trainset_id=unit.trainset_id,
            )
            unit.assign_trip(trip, turnback_seconds)

        return trainsets
