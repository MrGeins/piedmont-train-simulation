"""Backward-compatible topology export backed by external JSON."""
from backend.configuration.loader import load_infrastructure

_, _, stations = load_infrastructure()

__all__ = ["stations"]
