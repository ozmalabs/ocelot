# Frame topology cost attribution preregistration

**Lock date:** 2026-09-26, before capture.  
**Question:** Which graph-authored rules account for the topology-scale candidate, Term, and timing gap measured in [`SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_RESULTS_20260926.md`](SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_RESULTS_20260926.md)?

## Design

Reuse the exact N=64 chain, binary-tree, and star fixtures and four rules from the locked topology-scale runner. Enable both global and per-rule native scale audits. For each topology, run ten fresh event/full pairs, alternating order. Record separate activation/retraction global and per-rule counters (`rule_enumerations`, `candidate_pairs`, `candidate_tests`, `where_evaluations`, `term_evaluations`, `term_units`) and closure wall time. Check exact state parity after each transition, owner notification coverage, and fixed-point/empty-queue status. Verify graph/rule cardinality and all source/build hashes against this protocol and the existing base protocol/runner.

Per-rule audit adds measurement overhead, so counters are attribution data and wall times are descriptive only. Compare per-rule candidate and Term totals, and verify their sums against available global counters; do not attribute native setup/rule-vector clone time to a specific rule.

## Gates

1. Each fixture has 64 Microtheories, 64 Concepts, 63 dependency edges, and four active rules.
2. All 30 event/full pairs have activation and retraction projection parity; event queues settle and all touched frame owners are reported; full arms reach fixed points.
3. Per-rule counter data exists for every executed rule family, and per-rule sums match global totals for metrics whose audit definitions are additive.
4. Preregistered source, native artifact, base protocol, and base runner hashes match.

## Claim boundary

This attributes matching/evaluation work within one generated rule family at N=64. It does not measure rule-vector cloning in isolation, establish production workload distribution, or justify asymptotic extrapolation.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_frame_topology_cost_attribution_v1.py
python3 scripts/analyze_substrate_frame_topology_cost_attribution_v1.py
```
