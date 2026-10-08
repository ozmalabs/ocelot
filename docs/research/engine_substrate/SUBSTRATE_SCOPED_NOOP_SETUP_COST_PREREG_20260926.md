# Scoped no-op setup-cost preregistration

**Lock date:** 2026-09-26, before capture.  
**Question:** How does per-call cost of the scoped runner grow with active-rule count on a stable graph where no rule can match, and what portion is added by mutation reporting?

## Fixture and arms

Create a fixed graph with one Microtheory, one owned Concept, and no edges of any test-rule pattern type. Install N active rules for N ∈ `{0,1,4,16,64,256,512}`. Each has a unique absent edge type as its sole match pattern and a harmless node-attribute effect that cannot run without a binding. There are no `where` Terms. Warm each API once, then measure 50 consecutive stable no-op calls in each of seven fresh replicates.

APIs: `scoped_basic` (`run_rules_scoped` with the Microtheory ID), `scoped_report` (`run_rules_scoped_delta_report`), and `full_report` (`run_rules_report`). Cross each API with audit off/on, leaving per-rule mode disabled. Record per-call wall/cpu time, termination/zero-progress status, graph checksum/projection, global counter snapshots, and hashes. Audit is not enabled during setup or warm-up; reset counters immediately before each timed batch.

## Gates and analysis

1. All APIs report zero progress/fixed point after warm-up and leave the exact graph state unchanged.
2. Audit-off batches leave all scale counters zero; audit-on snapshots are present and consistent with the API's rule-attempt behavior.
3. Candidate enumeration remains zero for every count; no where-Term evaluation occurs.
4. All counts, repeats, and artifact fingerprints match this protocol.
5. Report medians, p10/p90, per-call slope versus active-rule count, and report-minus-basic cost. Do not attribute the slope exclusively to vector cloning: it includes rule iteration, term/graph setup, and matching dispatch on absent edge types.

## Claim boundary

This measures stable no-op calls with deliberately absent pattern edges. It isolates a lower-bound setup/dispatch envelope for repeated scoped calls but is not a changing workload, an end-to-end scheduler result, or a complete decomposition of cloning versus matcher overhead.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_noop_setup_cost_v1.py
python3 scripts/analyze_substrate_scoped_noop_setup_cost_v1.py
```
