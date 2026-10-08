# Thoughtexperiment deferred TrackIdentity attribution v1 preregistration

## Question

Can the engine retain a rule's identity when an `Effect::TrackIdentity` is queued during matching and applied later between settlement passes, and does that deferred write attribution reconcile with exact graph changes?

## Change under evaluation

The queued TrackIdentity payload now retains the originating rule symbol. During queue drain, the existing write-target observer opens a `deferred=true` event under that origin and captures the node/edge mutation targets. Ordinary direct rule-attempt events remain `deferred=false`. No matching, effect, queue ordering, or graph update semantics are intended to change.

## Protocol and gates

Run three fresh workers. Each constructs two identical substrates with previous/current percept nodes, one anchor self-edge, a rule-triggered `TrackIdentity` effect, and an independent direct-write control rule. A three-progress-step cap permits the first pass to enqueue the deferred effect and the next pass to drain it; this effect's repeated queueing can prevent full closure, so fixed-point convergence is not a gate in this diagnostic. Compare ordinary, attributed, and exact-snapshot reports on matched fresh substrates. Require status, progress, and pass parity; exact changed nodes/edges must be covered by event targets; aggregate targets must cover all event targets; and no events may be dropped. Require at least one deferred event attributed to `trans_frame_identity_assignment` and one direct event attributed to `trace_direct_control` with `deferred=false`. Verify the deferred event reaches all five percept node IDs that the exact oracle shows changed. Source and loaded native binary fingerprints must be stable in each worker.

## Interpretation boundary

Passing establishes producer-rule identity retention for this one queued graph-mutating family. It does not cover other deferred queues, multiple producers deduplicated into one queue item, field-level writes, binding identity, or autonomous residual diagnosis. It also does not prove that origin identity is a causal explanation when separate rules can write the same facts; future controls must inject such ambiguity and preserve it explicitly.

## Reproduction

Build an isolated extension with `maturin build --manifest-path runners/dsl/Cargo.toml --out /tmp/ocelot-deferred-track-wheel`, extract it to `/tmp/ocelot-deferred-track-pkg`, then use `OCELot_NATIVE_IMPORT_ROOT=/tmp/ocelot-deferred-track-pkg` for `--lock`, `--run`, and analysis.
