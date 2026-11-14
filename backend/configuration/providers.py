"""Infrastructure data-source adapters.

An API adapter can implement InfrastructureProvider once an official endpoint,
authentication scheme and field mapping are confirmed. The simulator consumes
the normalized document and does not depend on a particular external provider.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class InfrastructureProvider(Protocol):
    """Source of normalized infrastructure configuration."""

    @property
    def source(self) -> str:
        ...

    def load_data(self) -> dict[str, Any]:
        ...


class LocalJsonInfrastructureProvider:
    """Read the normalized infrastructure document from a local JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @property
    def source(self) -> str:
        return str(self.path)

    def load_data(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except OSError as exc:
            raise RuntimeError(f"Cannot read infrastructure configuration '{self.path}': {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in infrastructure configuration '{self.path}' at line {exc.lineno}, "
                f"column {exc.colno}: {exc.msg}"
            ) from exc
        if not isinstance(data, dict):
            raise ValueError(f"Infrastructure configuration '{self.path}' must contain a JSON object")
        return data
