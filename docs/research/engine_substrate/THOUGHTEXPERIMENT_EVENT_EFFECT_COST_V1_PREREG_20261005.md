# Thoughtexperiment endpoint versus effect-value observer cost preregistration

## Question

What incremental runtime, resident-memory, and serialized-report costs are associated with opt-in per-effect value snapshots compared with endpoint-only rule attribution, under equivalent closure and graph outcomes?

## Frozen arms

Use five modes: plain rule closure; endpoint-only mutation/event attribution; effect-level attribution; exact whole-graph snapshot diff; and a combined experiment residual journal with effect-level attribution. The direct and same-event fixtures use a three-step progress budget. The report-object-cap fixture contains 33 authored rule groups of 512 matches each and a budget of 40.

Three workers each run the complete fixture/mode matrix. For each fixture and mode, three additional isolated processes construct the graph before sampling RSS/PSS, execute closure, and capture elapsed wall/CPU time plus observer counters and serialized event size. All arms must end at the same graph and closure status for each fixture. The same-event fixture must show event endpoints `0→2`, effect transitions `0→1` and `1→2`, and edge deletion at effect 2. Endpoint-only mode must have zero effect payload. Effect snapshots must remain inside the declared per-report caps and report truncation under the stress fixture. Source files and loaded native binary hashes must remain stable.

## Build

The capture uses an optimized `opt-level=3` build with LTO disabled and 16 codegen units. The repository default (`fat` LTO, one codegen unit) required too long for the available build observation window. The override is recorded in the raw capture; its timing is not an exact production-profile estimate.

## Claim limit

The panel estimates the cost of these observer modes on three authored workloads. It does not establish trace utility for diagnosis, natural-workload prevalence, broad tractability, or self-improvement. RSS/PSS deltas are retained end-state measurements after graph construction, not allocation peaks.
