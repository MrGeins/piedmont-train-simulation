# Intermediate distributed pneumatic braking model

## Scope

The braking package provides an opt-in, independently testable model for a
complete train formation. It does not change the default running-time path.
Until a verified formation-specific brake configuration is supplied,
TravelTimeCalculator continues to use the existing constant service
deceleration and optional brake_propagation_delay_seconds fallback.

## Model stages

1. **Brake-pipe command propagation** — each vehicle receives the command
   after position_m / propagation_speed_mps.
2. **Local brake-pipe pressure response** — after the command front arrives,
   local pressure reduction approaches the configured full-service reduction
   through a first-order response.
3. **Brake-cylinder filling** — cylinder target pressure is proportional to
   local brake-pipe reduction and capped at configured maximum pressure.
   Cylinder pressure approaches that target with its own first-order time
   constant.
4. **Vehicle brake force** — each vehicle develops force in proportion to
   cylinder pressure, capped by configured maximum brake force.
5. **Train dynamics** — the simulator sums vehicle forces and integrates
   speed and distance. Positive gradient is uphill; negative is downhill.

All pressure values use kPa, positions use metres, speed uses m/s, mass uses
kg, force uses N and time uses seconds.

## Configuration contract

The caller must explicitly provide brake-pipe propagation speed, local
pressure-response time constant, full-service pressure reduction and, for
each vehicle, position, mass, maximum brake force, maximum cylinder pressure
and cylinder filling time constant.

No defaults are supplied for these physical parameters. Unverified PDF values
and guessed generic values cannot silently become operational SFM data.

## Deliberate limitations

This intermediate model is not a compressible-flow solver. It does not
calculate air mass flow, pipe diameter/friction, distributed pipe volume,
distributor-valve dynamics, reservoir depletion, leakage, brake release,
emergency braking, wheel/rail adhesion limits, brake rigging efficiency or
electrodynamic blending. The first-order pipe and cylinder responses are
explicit approximations requiring calibration against identified rolling-
stock data or measurements.

The service-braking simulation is exposed as a separate API. Integration into
TravelTimeCalculator is deferred until verified per-formation configuration
and validation data exist. Existing three-minute segment and 90-second
turnback fallbacks are untouched.


## Numerical integration and stopping event

The simulator advances brake-pipe and cylinder states over each integration
interval. If the end-of-step braking force implies that the train stops before
the interval ends, it solves for the stopping instant by bisection. The final
sample therefore uses cylinder pressures evaluated over the actual partial
interval, rather than advancing pneumatic states through time after the train
has already stopped.

The test suite checks both this final partial-step consistency and convergence
of stopping distance as the integration time step is refined. These are
numerical consistency checks; they do not replace calibration against measured
rolling-stock braking data.

## JSON formation configuration

```json
{
  "schema_version": 1,
  "formations": []
}
```

The opt-in loader is `backend.configuration.braking_loader.load_brake_formations`.
The default file is `config/braking/formations.json`; it is intentionally
empty until a complete formation has traceable, calibrated parameters. The
loader returns a mapping from unique `formation_id` values to
`BrakeFormation` instances. It is not called by the normal timetable or
running-time path.

The accompanying `config/braking/schema.json` defines the JSON structure.
The Python validator additionally enforces cross-field constraints that a
basic JSON Schema cannot express here: unique formation and vehicle IDs,
the first vehicle at the command source (0 m), and non-decreasing vehicle
positions. Unknown keys and missing physical parameters are rejected.

| Parameter | Unit | Constraint |
|---|---:|---|
| `propagation_speed_mps` | m/s | finite, > 0 |
| `pressure_response_time_constant_seconds` | s | finite, > 0 |
| `full_service_pressure_reduction_kpa` | kPa | finite, > 0 |
| `position_m` | m | finite, >= 0; first vehicle is 0 |
| `mass_kg` | kg | finite, > 0 |
| `maximum_brake_force_n` | N | finite, > 0 |
| `maximum_pressure_kpa` | kPa | finite, > 0 |
| `fill_time_constant_seconds` | s | finite, > 0 |

No physical defaults are supplied. The active configuration contains no
formations, and the unverified technical-reference candidate file is not
read by this loader. A formation must be populated only from evidence for the
exact consist and its brake equipment. Existing segment and turnback fallback
values are unaffected.

## Explicit configured simulation entry point

Use `backend.configuration.braking_service.ConfiguredBrakingService` when a
caller explicitly wants the distributed pneumatic model:

```python
from backend.configuration.braking_service import ConfiguredBrakingService

service = ConfiguredBrakingService()
print(service.available_formations)
result = service.simulate_service_braking(
    formation_id="VERIFIED_FORMATION_ID",
    initial_speed_mps=20.0,
)
```

The service loads the JSON configuration once when constructed. The caller
must select an existing `formation_id`; an unknown ID raises
`UnknownBrakeFormationError`. An empty formation list exposes no selectable
formations. Invalid or incomplete configuration fails during construction;
the service does not substitute legacy values or synthesize a formation.

This is a separate simulation API, not an alternate mode hidden inside
`TravelTimeCalculator`. The running-time calculator and its existing
constant-deceleration / optional propagation-delay behavior remain unchanged.
Integration tests exercise a complete configured braking run, empty and
invalid configurations, and the separation from the legacy running-time path.
