# Thoughtexperiment deferred framebuffer sample attribution v1 preregistration

## Question

Can a queued `Effect::FbSample` retain its producer rule through the drain, and do the deferred write targets cover exact graph changes from perception?

## Change under evaluation

The transient framebuffer queue carries the originating rule symbol. Its drain wraps the existing `fb_sample` operation in a `deferred=true` write event and marks the event progressed when sampling succeeds. Framebuffer access, segmentation, and graph semantics remain unchanged.

## Protocol and gates

Run three fresh source-locked workers. Each writes one deterministic 8×8 BGRA frame to a uniquely named POSIX shared-memory framebuffer, attaches it to a fresh seeded WorldAdapter, and installs the existing frame-sequence-gated look rule with a 2×2 sample grid. Compare ordinary settlement, attributed target reporting, and exact snapshot delta. Require status/progress/pass parity, one successful deferred event named `look_when_frame_advances`, non-vacuous WorldInstance/Region output, exact node/edge delta coverage, aggregate target containment, no dropped events, distinct worker PIDs, and stable source/native fingerprints. The harness performs no direct sample call.

This measures one static frame and one producer binding. It does not measure moving-frame tracking, multi-rule competition, perception accuracy, or continuous ingestion rate.

## Reproduction

Build with `PYTHON=python3 scripts/engine_build.sh`, then run the source-locked runner with `--lock` and `--run`, followed by its analyzer. The lock binds Rust implementation, Python binding, fixture helper, seed, protocol, runner, analyzer, and loaded native binary.
