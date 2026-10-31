"""Compatibility exports for route and parameter-based service configuration."""
from backend.configuration.services_loader import load_services

ROUTES, PLATFORM_PLANS, SERVICES = load_services()

# Deprecated compatibility alias for callers not yet migrated.
TAKT_TEMPLATES = SERVICES

__all__ = ["ROUTES", "PLATFORM_PLANS", "SERVICES", "TAKT_TEMPLATES"]
