"""Compatibility exports for route and timetable configuration."""
from backend.configuration.services_loader import load_services

ROUTES, PLATFORM_PLANS, TAKT_TEMPLATES = load_services()

__all__ = ["ROUTES", "PLATFORM_PLANS", "TAKT_TEMPLATES"]
