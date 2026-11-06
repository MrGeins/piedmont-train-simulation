"""Build review-only candidates from an ERA RINF SPARQL CSV export.

This tool never edits the active infrastructure configuration. RINF sections
are between operational points and can span multiple project topology edges.
Track-level speed limits are retained per running track and are never silently
flattened into a section-wide value when multiple tracks are present.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

DEFAULT_INFRASTRUCTURE = Path("config/infrastructure/sfm.json")
DEFAULT_ALIASES = Path("config/infrastructure/rinf_operational_point_aliases.json")


def normalize_name(value: str) -> str:
    """Normalize a display name for explicit alias lookup only."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def parse_optional_number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    parsed = float(value.strip().replace(",", "."))
    if parsed <= 0:
        raise ValueError("operational values must be positive")
    return parsed


def build_candidates(
    rows: Iterable[dict[str, str]],
    infrastructure: dict[str, Any],
    aliases: dict[str, str],
    source_snapshot: str,
) -> dict[str, Any]:
    """Normalize RINF rows into candidates without changing live network data."""
    topology = infrastructure.get("topology", {})
    links = {
        frozenset((item["from"], item["to"]))
        for item in infrastructure.get("links", [])
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rejected: list[dict[str, Any]] = []

    for row_number, row in enumerate(rows, start=2):
        section_uri = (row.get("section_uri") or "").strip()
        start_name = (row.get("start_name") or "").strip()
        end_name = (row.get("end_name") or "").strip()
        if not section_uri or not start_name or not end_name:
            rejected.append({
                "row": row_number,
                "reason": "section_uri, start_name and end_name are required",
                "input": row,
            })
            continue
        try:
            distance = parse_optional_number(row.get("distance_km"))
            speed = parse_optional_number(row.get("speed_limit_kmh"))
        except ValueError as exc:
            rejected.append({"row": row_number, "section_uri": section_uri, "reason": str(exc)})
            continue
        if distance is None:
            rejected.append({
                "row": row_number,
                "section_uri": section_uri,
                "reason": "missing distance_km",
            })
            continue

        track_uri = (row.get("track_uri") or "").strip()
        track_id = (row.get("track_id") or "").strip()
        track_direction = (row.get("track_direction") or "").strip()
        # If the export omits track identity, keep each row separate: assuming
        # that two rows describe the same track would risk merging directions.
        track_key = track_uri or track_id or f"unidentified-row-{row_number}"
        grouped[section_uri].append({
            "start_name": start_name,
            "end_name": end_name,
            "distance_km": distance,
            "track_uri": track_uri or None,
            "track_id": track_id or None,
            "track_direction": track_direction or None,
            "track_key": track_key,
            "speed_limit_kmh": speed,
        })

    candidates = []
    unmatched = []
    for section_uri, section_rows in sorted(grouped.items()):
        first = section_rows[0]
        start_key = aliases.get(normalize_name(first["start_name"]))
        end_key = aliases.get(normalize_name(first["end_name"]))
        if not start_key or not end_key:
            unmatched.append({
                "section_uri": section_uri,
                "start_name": first["start_name"],
                "end_name": first["end_name"],
                "reason": "missing_explicit_operational_point_alias",
            })
            continue
        if start_key not in topology or end_key not in topology:
            unmatched.append({
                "section_uri": section_uri,
                "start_name": first["start_name"],
                "end_name": first["end_name"],
                "mapped_start": start_key,
                "mapped_end": end_key,
                "reason": "alias_targets_unknown_topology_node",
            })
            continue
        if start_key == end_key:
            unmatched.append({
                "section_uri": section_uri,
                "reason": "start_and_end_map_to_same_topology_node",
            })
            continue

        distances = {item["distance_km"] for item in section_rows}
        distance = next(iter(distances)) if len(distances) == 1 else None

        tracks_by_key: dict[str, dict[str, Any]] = {}
        for item in section_rows:
            track = tracks_by_key.setdefault(item["track_key"], {
                "track_uri": item["track_uri"],
                "track_id": item["track_id"],
                "track_direction": item["track_direction"],
                "speed_limit_kmh": item["speed_limit_kmh"],
            })
            if track["speed_limit_kmh"] != item["speed_limit_kmh"]:
                track["speed_limit_kmh"] = None
                track["conflicting_speed_values"] = True

        track_records = list(tracks_by_key.values())
        all_track_speeds = [item["speed_limit_kmh"] for item in track_records]
        speed = (
            all_track_speeds[0]
            if len(track_records) == 1 and all_track_speeds[0] is not None
            else None
        )
        reasons = []
        if distance is None:
            reasons.append("conflicting_section_lengths")
        if not track_records or any(value is None for value in all_track_speeds):
            reasons.append("missing_or_conflicting_track_speed_limit")
        if len(track_records) > 1:
            reasons.append("multiple_running_tracks_require_directional_review")

        direct_link_exists = frozenset((start_key, end_key)) in links
        if not direct_link_exists:
            reasons.append("rinf_section_not_a_single_project_topology_edge")

        candidates.append({
            "section_uri": section_uri,
            "rinf_start_name": first["start_name"],
            "rinf_end_name": first["end_name"],
            "from": start_key,
            "to": end_key,
            "distance_km": distance,
            "speed_limit_kmh": speed,
            "track_speed_limits": track_records,
            "source": {
                "source_id": "rinf_rfi_2026_09",
                "snapshot": source_snapshot,
                "section_uri": section_uri,
            },
            "rinf_track_rows": len(section_rows),
            "rinf_running_tracks": len(track_records),
            "direct_project_link": direct_link_exists,
            "status": "pending_manual_review",
            "review_reasons": reasons,
        })

    return {
        "schema_version": 1,
        "source_snapshot": source_snapshot,
        "active_infrastructure_modified": False,
        "candidate_sections": candidates,
        "unmatched_sections": unmatched,
        "rejected_rows": rejected,
        "summary": {
            "candidate_sections": len(candidates),
            "unmatched_sections": len(unmatched),
            "rejected_rows": len(rejected),
            "ready_for_manual_review": sum(
                not item["review_reasons"] for item in candidates
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="RINF SPARQL CSV export")
    parser.add_argument("--output", required=True, help="Review-only JSON output")
    parser.add_argument("--snapshot", required=True, help="RINF dataset snapshot identifier/date")
    parser.add_argument("--infrastructure", type=Path, default=DEFAULT_INFRASTRUCTURE)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    args = parser.parse_args()

    infrastructure = json.loads(args.infrastructure.read_text(encoding="utf-8"))
    alias_document = json.loads(args.aliases.read_text(encoding="utf-8"))
    aliases = {
        normalize_name(name): node
        for name, node in alias_document.get("operational_point_aliases", {}).items()
    }
    with Path(args.input).open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    report = build_candidates(rows, infrastructure, aliases, args.snapshot)
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
