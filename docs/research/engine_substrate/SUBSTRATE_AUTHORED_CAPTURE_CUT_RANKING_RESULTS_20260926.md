# Authored-capture cut ranking: retrospective diagnostic

**Date:** 2026-09-26. **Grade:** post-hoc structural development diagnostic.
This analyzes existing captures and does not pass the separate confirmatory
mutation/partitioned-execution preregistration.

## Result

An independent analyzer checks the Bigville digest against its accepted
trace-off parity record (the full graph is not in that capture), recomputes the
dialogue digest from its captured full graph, and independently recomputes the
min-fill orders, widths, ownership coverage, and partition metrics. Every
integrity and case check passes. The dependency-derived order, authored
ownership, and balanced-ID grouping preserve the same authored within-frame
pairs in both workloads, and the structural metrics are identical across the
three partitions:

| Capture | Task nodes / authored frame sizes | Task dependency pairs | Min-fill width | Authored cross-frame captured dependency edges | Global-boundary incidences | Observed trace |
|---|---|---:|---:|---:|---:|---|
| Bigville task-access capture | 500 / 100 × 5 | 500 | 2 | 0 causal-influence edges | Not captured; source retained causal edges only | 243 events; 5 task-to-task pairs |
| Connected mixed dialogue census | 12 / 5, 1, 6 | 17 | 2 | 2 | 40 | 26 events; 8 task-to-task pairs |

For Bigville, all three partitions have zero cross-frame edges in the captured
causal-influence dependency graph. Its raw capture did not retain all graph
edge types, so global-boundary incidence and total cut-boundary nodes are
unavailable; they are not zero. For dialogue, every partition has two
cross-frame concrete edges, all 12 task nodes touch a cut or global boundary,
and 40 graph edges connect task nodes to global nodes. All three dialogue
partitions retain 25/25 within-authored-frame pairs. The balanced-ID and
min-fill heuristics therefore add no cut improvement on these captures.

This is not evidence that dependency-derived partitions are generally no
better: the captures are already structured around contiguous/low-width
ownership, Bigville's target rule declares `reads_any` but its captured static
metadata does not cover every active rule, the Bigville edge inventory is
incomplete, and both runtime traces are partial. It demonstrates
that these two existing captures cannot show a partition-ranking advantage.
The dialogue's 40 shared-state incidences also make its local frame assignment
insufficient to admit scoped execution under the preregistered shared-state
contract.

## Scope boundary

No task was rerun; no graph was changed; no candidate partition was executed.
There are no mutation-time rebuild costs, omitted-boundary controls, or
partitioned-vs-monolithic semantic results. The original confirmatory protocol
still requires fresh trace-on/off/control runs, three mutation branches,
partition maintenance measurements, and an audited delivery contract or
explicit refusal. Do not use this diagnostic as a locality, speed, or natural
task distribution claim.

## Reproducibility

- Diagnostic protocol: [`SUBSTRATE_AUTHORED_CAPTURE_CUT_RANKING_DIAGNOSTIC_20260926.md`](SUBSTRATE_AUTHORED_CAPTURE_CUT_RANKING_DIAGNOSTIC_20260926.md)
- Runner: [`substrate_authored_capture_cut_ranking_v1.py`](../../../scripts/substrate_authored_capture_cut_ranking_v1.py)
- Independent analyzer: [`analyze_substrate_authored_capture_cut_ranking_v1.py`](../../../scripts/analyze_substrate_authored_capture_cut_ranking_v1.py)
- Input lock: [`authored_capture_cut_ranking_v1_lock_20260926.json`](../../../evaluation/substrate_capability/authored_capture_cut_ranking_v1_lock_20260926.json)
- Raw results: [`substrate_authored_capture_cut_ranking_v1_20260926.json`](../../../evaluation/reports/substrate_authored_capture_cut_ranking_v1_20260926.json)
- Independent analysis: [`substrate_authored_capture_cut_ranking_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_authored_capture_cut_ranking_v1_analysis_20260926.json)
- Preserved first harness failure: [`harness failure record`](../../../evaluation/reports/substrate_authored_capture_cut_ranking_v1_harness_failure_20260926.json)

The raw records and source captures remain unchanged. The runner and analyzer
are fingerprinted by the analysis lock. The prior source analyses establish
that their accepted source gates passed; this analyzer independently verifies
the source hashes and recomputes the cut ranking from those captured inputs.
