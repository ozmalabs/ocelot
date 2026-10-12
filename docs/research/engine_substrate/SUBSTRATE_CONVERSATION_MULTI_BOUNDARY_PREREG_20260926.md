# Conversation multi-boundary write-to-owner mapping preregistration (2026-09-26)

## Question

Can a caller derive the frame owners that must rerun after several shared evidence attributes change simultaneously, from the live runtime reader edges and live `has_concept` ownership? Does running all mapped owners match full closure, and does omitting one mapped owner leave a detectable result that full catch-up repairs?

## Workload and mutation plan

Reuse the locked read-only-boundary conversation model: mutable candidate copies are frame-local; a shared `BoundaryEvidence.boundary_value` is read by the in-memory patched scoring rule via each candidate's `derived_from_evidence` edge. Test 2, 4, and 8 frames, three fresh-process replicates, and three arms (full, mapped-required, omitted-owner), 27 workers total. Mutation sets are fixed by size: edge 0→4.0 for N=2; edges 0→4.0 and 1→5.0 for N=4; edges 0→4.0, 1→5.0, and 5→8.0 for N=8. Values are assigned simultaneously before any frame reruns.

Before mutation, derive each changed evidence node's readers by traversing live incoming `derived_from_evidence` edges to candidate copies, then map those candidates through live `has_concept` Microtheory ownership. Cross-check this result against the scorer's declared `c derived_from_evidence e` match and `Attr(e,boundary_value)` term, and against the authored chain endpoints. The union of those owner frames is the required schedule. Bump the epoch and reopen only those dependent frames. The full arm uses full closure; mapped-required runs the derived owner set to scoped fixpoint; omitted-owner skips frame 1; a final full catch-up tests recovery.

## Gates

Require 27 fresh unique PIDs, exact randomized schedule and lock; each modified boundary has exactly two reader-frame owners equal to its expected endpoints; the union owner map exactly matches expected mutated-edge endpoints; candidates remain uniquely owned; the scoring rule reads the mutated attribute; baseline projections are equal and expected; full and mapped-required post-mutation projections match exactly, with required closure followed by a zero-work full probe; every omitted arm differs from full before repair, performs positive catch-up work, then matches exactly; all final probes are full-graph fixed points; closure does not write the boundary attribute. Record mapping output, all stages, counters, and timing. Cost is descriptive.

## Claim boundary

This is an explicit Python-side graph/dependency walk over a single authored conversation chain, not native access tracing or automatic effect-to-frame notification. It changes a small, deterministic edge subset (at most three) and does not establish general dependency extraction, arbitrary effect coverage, dense/cyclic topologies, natural event prevalence, or scalable scheduling.

## Provenance

Lock this protocol, runner, analyzer, the single-boundary runner, conversation seed/materializer, and engine sources before execution. Keep this multi-mutation record separate from the prior one-edge wakeup capture.
