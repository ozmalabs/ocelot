# Thoughtexperiment effect-target trace cost panel v1 (preregistration)

Question: can the engine expose effect-index to node/edge write targets without copying before/after graph values, at lower memory cost than full value tracing?

The panel reuses the three fixtures from `thoughtexperiment_event_effect_cost_v1.py`: a direct small writer, same-event multiwrite, and a 33-group report-object-cap stress fixture. It compares endpoint event attribution, full per-effect value snapshots, and target-only per-effect attribution. Each fixture/mode receives three isolated process replicates and all workers run the existing semantic/parity panel. Sources and native binary are SHA-256 locked before capture and checked after capture.

Primary outcomes are process wall and CPU time, RSS/PSS delta, event JSON size, semantic graph digest, event count, retained target count, value snapshot bytes/objects, and explicit truncation. The target-only report must include effect-indexed node/edge locations, no value objects, zero value-snapshot bytes, and identical closure state. The intended bounded implementation caps targets per effect and report; truncation must be visible. These fixtures are synthetic instrumentation workloads and do not establish natural-task performance or general thoughtexperiment capability.
