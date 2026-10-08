# Unified five-family scoped and fallback queue work v1 preregistration

Date: 2026-10-01

## Question

Can Microtheory-scoped closure expose pending work across all five deferred queue families, and does one subsequent global closure produce the same settled graph as direct global closure as join multiplicity and writer count grow?

## Design

Reuse the locked positive two-edge join workload from unified five-family work trace v1: writer counts `R={1,8,32}`, join multiplicities `M={1,4,16}`, and three fresh-process replications per cell. Add one `Microtheory` owner per fixture with each writer anchor as a directly owned concept. Compare three independently constructed arms: direct full closure; scoped closure only; scoped closure followed by global fallback if scoped reports pending deferred effects. Capture operation-work traces and scale-audit counters separately for every closure phase.

The scope extractor owns the Microtheory and its direct `has_concept` neighbors. This deliberately makes each writer anchor in-scope while the join targets and other graph objects remain reachable through the writer pattern. It tests the existing generic binding-touches-scope behavior, not recursive ownership. Inputs lock the native binary, engine sources, runner, analyzer, protocol, and build record.

## Expected invariants

- Direct full closure and scoped-plus-fallback closure reach fixed point and have byte-for-byte equal final graph dictionaries.
- Scoped-only reports deferred work pending; it does not claim a settled fixed point.
- Scoped-only enqueues the same five queue-family item totals as the full arm, with no queue drains. The RulePatch queue deduplicates once per writer; the other four families enqueue once per successful join binding.
- Scoped-plus-fallback enqueues in the scoped phase and drains in the fallback phase; cumulative family totals equal direct full closure.
- The final settled graphs contain exactly `R` target `seen_i` edges, `4R` frame cells per expected world count, and no trigger edges.
- Every operation trace has zero dropped rows and its queue enqueue/drain/batch units reconcile to the corresponding scale-audit counters.
- Report wall time and candidate counts are descriptive; the key outcome is exact state parity plus correct pending/drain semantics across `R×M`.

## Limits

This is one authored join family and one direct-owner scope shape. It does not establish scope completeness for cross-frame rules, recursive ownership, natural workloads, or a complexity bound. The full arm is an oracle only for this fixture. A global fallback can erase any runtime benefit of scoped execution; this protocol measures the cost and correctness of that path without presuming it is faster.
