# SFM infrastructure data calibration

## Authoritative sources

The current source register is `config/data_sources/sfm.json`.

- **ERA RINF / RFI**: section-of-line endpoints and length; track-level maximum permitted speed. RFI's Infrastructure Manager code is `0083`. The public RINF dataset explorer exposes the RFI snapshot `20260929_RINF_RFI.ttl`.
- **RFI IFRP PIR**: regional infrastructure statement and access to the e-PIR technical GIS. The public PIR is useful for network context; detailed e-PIR access requires registration.
- **Agenzia della Mobilità Piemontese, PEA SFM 2026**: planned train movements, origin/destination, route distance, departure/arrival times, and rolling-stock composition. These are whole-trip or partial-trip observations, not per-edge measurements.
- **SFM FAQ**: confirms the families used across the network, but does not provide a line-by-line fleet assignment or vehicle performance curves.

## RINF extraction

1. Open the ERA RINF endpoint: <https://rinf.data.era.europa.eu/endpoint>.
2. Run `scripts/rinf_sections.sparql`.
3. Export the result as CSV. Required columns: `section_uri,start_name,end_name,distance_km`. Add `speed_limit_kmh` only when the running-track value has been linked to the section and the track/direction ambiguity has been reviewed.
4. Add reviewed name/ID mappings to `config/infrastructure/rinf_operational_point_aliases.json`. The importer normalizes names for lookup, but does not guess aliases.
5. Run:

```bash
python scripts/rinf_candidate_import.py \
  --input /path/to/rinf_sections.csv \
  --output /path/to/rinf_candidates.json \
  --snapshot 2026-09-29
```

6. Review `candidate_sections`, `unmatched_sections`, and `review_reasons`. In particular, a RINF section may span several project topology edges. Do not split a section length among those edges without a documented geometry/linear-reference method.
7. Only after review, promote accepted measurements into `config/infrastructure/sfm.json`, preserving source URI, snapshot, retrieval date and review status.

## Rolling stock

The SFM 2026 operating plan identifies rolling-stock types and train compositions. This is sufficient to create type records and compare planned service assignments, but not to populate `max_speed_kmh`, `acceleration_mps2`, `service_braking_mps2`, or turnback times. Those require an authoritative vehicle technical sheet, ERATV record, or operator-supplied performance data for the exact variant and formation.

## Data integrity rules

- No map-layout coordinates are used as railway distances.
- No line-wide or train-wide average is copied to individual infrastructure links.
- Do not treat RINF section length as an edge length unless endpoints map to that exact topology edge.
- Do not collapse different running-track speed limits into one value without a documented conservative/directional rule.
- The importer creates a review report only; it never modifies active infrastructure data.
- Keep the 3-minute simulation fallback until the required physical inputs are verified.
