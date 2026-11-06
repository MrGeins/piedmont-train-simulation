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


## User-supplied rolling-stock technical summary — 2026-11-01

The user supplied `specifiche_tecniche_treni_piemonte.pdf`, a three-page synthesis of rolling-stock physical parameters. Its values have been transcribed into `config/rolling_stock/technical_reference_candidates.json` and the document has been registered in `config/data_sources/sfm.json`. The dataset preserves the source's terminology and scope for Rock ETR 521, POP ETR 104, Jazz ETR 425/526 family, TAF, electric and diesel Minuetto, Blues HTR 312/412, Vivalto + E.464, and MDVC/MDVE + E.464.

The candidate dataset includes, where supplied, empty/equivalent mass, rotational inertia factor, power, maximum tractive effort, speed limits, acceleration regimes or points, service/emergency braking, Davis coefficients, traction-mode constraints and pneumatic brake delay. Missing parameters remain absent; no values are derived to fill gaps. In particular, the Blues entries do not gain a fabricated equivalent mass or traction effort, and the locomotive's own mass/power is not substituted for the complete locomotive-hauled consist.

**Evidence status:** this is a user-supplied synthesis without traceable manufacturer document identifiers, revisions, test conditions or citations for each parameter. It is therefore classified as `user_supplied_unverified`. Its values are intentionally not merged with the separate Treniebinari family specifications, whose POP and TAF hourly power values differ. Both source records are retained without silently resolving the discrepancies.

**Runtime boundary:** `config/rolling_stock/sfm.json` remains the only operational profile source. Its `profiles` object remains empty; the candidate file is not loaded by `load_vehicle_profiles` or `TravelTimeCalculator`. The existing 3-minute segment fallback and 90-second default turnback remain unchanged. Before activation, the acceleration point/range semantics, Davis units and coefficients, braking assumptions, consist variants and source provenance need technical review. The current calculator also assumes constant acceleration and service braking and does not yet implement speed-dependent traction, Davis resistance or pneumatic propagation delay.

## Speed-dependent running-time model (2026-11-01)

- Extended `VehiclePerformance` with an optional, validated acceleration curve represented by explicit speed/acceleration knots. The curve must start at 0 km/h, have strictly increasing speeds and cover the configured vehicle maximum speed.
- Extended `TravelTimeCalculator` to integrate the acceleration phase numerically over speed, using linear interpolation only between knots explicitly supplied to an operational vehicle profile. A peak-speed solver handles segments too short to reach the infrastructure/vehicle speed cap; service braking remains the existing constant-deceleration model.
- The existing constant-acceleration path remains unchanged when no curve is supplied, preserving current callers and fallback behavior.
- The candidate technical-reference JSON is not loaded by this model. No PDF candidate values have been converted into knots because their source status and curve semantics remain unverified.
- This increment does not yet model Davis resistance, traction power/effort limits, gradients, pneumatic brake delay, signals or temporary speed restrictions. Those require additional source validation and explicit model contracts before implementation.

## Longitudinal traction and Davis resistance model (2026-11-06)

The running-time calculator now supports a third, optional longitudinal model alongside the legacy constant-acceleration model and the explicit acceleration-curve model.

- `TractionModel` requires complete-formation effective mass in kg, maximum tractive effort in N, maximum power in W, and a `DavisResistance` instance.
- The Davis convention is explicitly SI: `R_N(v) = A_N + B_N_per_mps * v_mps + C_N_per_mps2 * v_mps²`. Coefficients must be finite and non-negative, with at least one non-zero term.
- Available tractive effort is `min(max_tractive_effort_n, max_power_w / speed_mps)`; at standstill it is limited by maximum tractive effort. Net acceleration is (tractive effort minus Davis resistance) divided by effective mass.
- The calculator integrates acceleration distance/time over speed, constrains the target speed by the infrastructure limit, vehicle maximum and sustainable traction speed, and solves the peak speed for short segments. Service braking remains a constant deceleration.
- The acceleration-curve and traction/Davis representations are mutually exclusive. An acceleration curve already represents net acceleration; combining it with resistance would double-count losses.
- Effective mass must already include the rotational-inertia allowance when the source reports equivalent mass. Do not apply a second inertia multiplier.
- The model assumes level track and does not yet include gradients, brake propagation delay, traction transients, signals, temporary speed restrictions or direction-dependent track selection.

**Source-data restriction:** the Davis coefficients in `technical_reference_candidates.json` remain `user_supplied_unverified`. Their force and speed units/convention have not been established from a traceable source. They have not been converted, loaded or used by the runtime model. The new API accepts only explicitly SI-converted values; the candidate data remain unchanged. Likewise, no candidate train mass, power or tractive-effort values have been activated as SFM operational profiles.


## Track gradient and brake propagation delay (2026-11-06)

- `gradient_permille` is treated as a signed gradient in the infrastructure link's stored `from` -> `to` direction. The path calculator reverses its sign when a train traverses the same link in the opposite direction.
- Positive gradient is uphill and subtracts the longitudinal gravity component from acceleration; it also increases effective service-braking deceleration. Negative gradient is downhill and has the opposite effects.
- The gravity component uses `g = 9.80665 m/s²` and the small-angle approximation `g * gradient_permille / 1000`. This is suitable for railway gradients expressed in permille.
- `brake_propagation_delay_seconds` is an optional rolling-stock profile field, finite and non-negative, defaulting to zero. During the delay the simplified model holds speed constant; full service braking then acts at the gradient-adjusted deceleration.
- The delay value supplied in the technical-summary PDF remains unverified and is not copied into operational profiles. Existing profiles remain empty and all existing callers retain zero delay.
- No gradient values have been added to the active infrastructure dataset. The implementation only consumes a gradient when one is explicitly supplied and validated.
- Limitations: the model does not yet simulate a distributed brake pipe, per-vehicle brake build-up, traction cut-off transients, grade changes within a segment, or direction-specific running-track selection. Constant-speed motion during brake propagation is an explicit simplification.
