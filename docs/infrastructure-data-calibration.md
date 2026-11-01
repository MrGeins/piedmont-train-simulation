# SFM infrastructure data calibration

## Authoritative sources

The current source register is `config/data_sources/sfm.json`.

- **ERA RINF / RFI**: section-of-line endpoints and length; track-level maximum permitted speed. RFI's Infrastructure Manager code is `0083`. The public RINF dataset explorer exposes the RFI snapshot `20260929_RINF_RFI.ttl`.
- **RFI IFRP PIR**: regional infrastructure statement and access to the e-PIR technical GIS. The public PIR is useful for network context; detailed e-PIR access requires registration.
- **Agenzia della Mobilità Piemontese, PEA SFM 2026**: planned train movements, origin/destination, route distance, departure/arrival times, and rolling-stock composition. These are whole-trip or partial-trip observations, not per-edge measurements.
- **SFM FAQ**: confirms the families used across the network, but does not provide a line-by-line fleet assignment or vehicle performance curves.

## RINF extraction

1. Open the ERA RINF endpoint: <https://rinf.data.era.europa.eu/endpoint>.
2. Run `scripts/rinf_sections.sparql` for the section-only export, or preferably `scripts/rinf_section_tracks.sparql` for the combined export.
3. The combined query emits one row per `SectionOfLine`/`RunningTrack` pair, with `track_uri`, `track_id`, `track_direction` and `speed_limit_kmh` where published. It filters both the section and running tracks to RFI infrastructure manager code `0083`. Export CSV with required columns `section_uri,start_name,end_name,distance_km` and optional track columns `track_uri,track_id,track_direction,speed_limit_kmh`. Do not combine tracks or directions; blank speed values remain missing data. `maximumPermittedSpeed` is a property of a running track, not of the section as a whole.
4. Add reviewed name/ID mappings to `config/infrastructure/rinf_operational_point_aliases.json`. The importer normalizes names for lookup, but does not guess aliases. Optional track columns are retained in `track_speed_limits`; a section-wide `speed_limit_kmh` is emitted only when exactly one identified running track is present.
5. Run:

```bash
python scripts/rinf_candidate_import.py \
  --input /path/to/rinf_sections.csv \
  --output /path/to/rinf_candidates.json \
  --snapshot 2026-09-29
```

6. Review `candidate_sections`, `unmatched_sections`, and `review_reasons`. In particular, a RINF section may span several project topology edges. Do not split a section length among those edges without a documented geometry/linear-reference method.
7. Only after review, promote accepted measurements into `config/infrastructure/sfm.json`, preserving source URI, snapshot, retrieval date and review status. Multiple running tracks remain separate directional records; they are not collapsed into a single link speed.

## Rolling stock

The SFM 2026 operating plan identifies rolling-stock types and train compositions. This is sufficient to create type records and compare planned service assignments, but not to populate `max_speed_kmh`, `acceleration_mps2`, `service_braking_mps2`, or turnback times. Those require an authoritative vehicle technical sheet, ERATV record, or operator-supplied performance data for the exact variant and formation.

## Data integrity rules

- No map-layout coordinates are used as railway distances.
- No line-wide or train-wide average is copied to individual infrastructure links.
- Do not treat RINF section length as an edge length unless endpoints map to that exact topology edge.
- Do not collapse different running-track speed limits into one value without a documented conservative/directional rule.
- The importer creates a review report only; it never modifies active infrastructure data.
- Keep the 3-minute simulation fallback until the required physical inputs are verified.


## First RINF calibration — 2026-10-31

The RFI snapshot `2026-09-29` was matched against the existing SFM topology. The matching rule was deliberately strict: a normalized RINF operational-point name had to match exactly one normalized topology display name, and both endpoints had to identify one existing undirected project link.

- Accepted exact-name mappings: **73** in `rinf_operational_point_aliases.json`.
- Promoted SectionOfLine distances: **40** links, each with its RINF section URI, snapshot and retrieval date.
- Promoted track speed limits: **22** links. Each has exactly one RINF RunningTrack and direction code `30` (both directions).
- Distance only: **18** links. These sections contain multiple running tracks; their individual speed values remain in the review report and are not collapsed into a single edge speed.
- Not promoted: **12** matched-endpoint sections that do not correspond to one existing topology link. A section spanning multiple project edges is not split or distributed.

RINF direction codes are `10` = normal direction, `20` = opposite direction, and `30` = both directions. This mapping is taken from the ERA RINF Application Guide. See <https://rinf.data.era.europa.eu/era-vocabulary/rinf-appGuide/v3.3.0/>.

Every promoted link carries `distance_source`; links with a promoted speed also carry `speed_limit_source`, including the RunningTrack URI, track ID and direction. The 3-minute fallback remains in place wherever calibrated distance/speed data is unavailable. This calibration does not populate rolling-stock performance profiles.


## Multi-track speed review — 2026-11-01

A second pass reviewed all 18 direct topology sections that contain multiple RINF RunningTracks. Seventeen sections publish a non-null, identical maximum permitted speed on every identified track. Their scalar edge speed is now promoted because it is unambiguous for the project's undirected link model; all RunningTrack URIs, IDs, direction codes and individual values are retained in `speed_limit_source.track_limits`. The remaining section, Bivio Crocetta–Torino Porta Susa, has different track limits (100 and 60 km/h) and remains distance-only until the simulator can represent track selection or a documented conservative policy is approved.

The active network now contains 39 speed-calibrated links and 1 distance-only calibrated link. The 12 RINF sections that span multiple topology edges remain unpromoted: a unique shortest path through technical topology nodes is not, by itself, evidence that the section's length can be allocated to each edge. Their route candidates should be reviewed as section-level overlays, not split into invented edge distances.


## Rolling-stock published maximum speeds — 2026-11-01

Public operator/manufacturer references provide maximum speeds for three families observed in the SFM 2026 operating plan:
- POP: 160 km/h (published four-car POP family summary; exact SFM unit subtype still requires confirmation).
- Rock ETR521: 160 km/h (Hitachi Rail manufacturer specification for the five-car ETR521).
- TAF: 140 km/h (operator fleet reference; exact SFM unit subtype still requires confirmation).

These values are stored as `published_specs` on the observed family records, not as calibrated `VehiclePerformance` profiles. The references do not provide the exact formation-specific acceleration and service-braking curves required by the running-time model. `profiles` therefore remains empty and the 3-minute fallback is unchanged.


## Rolling-stock technical reference pass — 2026-11-01

The user supplied five Treniebinari technical-sheet URLs. The published family/variant data now recorded in `config/rolling_stock/sfm.json` are:

| SFM family / variant | Maximum speed | Hourly power | Additional published data |
|---|---:|---:|---|
| Minuetto ALe 501-Le 220-ALe 502 | 160 km/h | 1,250 kW | Three-car family |
| POP ETR 104 | 160 km/h | 2,000 kW | Four-car variant |
| Rock ETR 521 | 160 km/h | 3,400 kW | Five-car variant |
| TAF ALe 506 + 2 Le 736 + ALe 426 | 140 km/h | 3,640 kW | Four-car formation |
| E.464 + Vivalto | 160 km/h | 3,500 kW | E.464 locomotive only: 3,000 kW continuous, 72 t service mass, 200 kN maximum tractive effort |

Source URLs are registered individually in `config/data_sources/sfm.json`. Values are scoped to the published family or variant; in particular, E.464 locomotive data are not treated as the mass or performance of the complete Vivalto train.

These references provide useful traction and speed constraints but not a full train performance model. They do not provide complete numeric acceleration and service-braking curves for the exact SFM formations, nor turnback times. The `profiles` object therefore remains empty and the 3-minute fallback is not changed. Published power and tractive effort must not be converted into an assumed constant acceleration without a verified mass model and traction/braking curves.
