"""Backward-compatible station registry export backed by external JSON."""
from backend.configuration.loader import load_infrastructure

stations_registry, _, _ = load_infrastructure()

__all__ = ["stations_registry"]
