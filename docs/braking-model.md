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
