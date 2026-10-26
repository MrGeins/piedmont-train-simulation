"""Backward-compatible track map export backed by external JSON."""
from backend.configuration.loader import load_infrastructure

_, infrastructure_map, _ = load_infrastructure()

__all__ = ["infrastructure_map"]
