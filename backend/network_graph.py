"""Compatibility exports for the active railway network configuration."""
from backend.model.models import RailwayStation, RailwayLine
from backend.configuration.loader import load_infrastructure

stations_registry, infrastructure_map, stations = load_infrastructure()

__all__ = [
    "RailwayStation",
    "RailwayLine",
    "stations_registry",
    "infrastructure_map",
    "stations",
]
