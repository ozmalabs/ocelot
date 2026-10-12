# Conversation task-scope deletion-safe ordering v1.9 results

Date: 2026-10-03

## Change and validation

V1.9 replaces the no-deletion EdgeIdx-order assumption with a lexicographic key made from each match clause's position in the live candidate index selected by the unseeded matcher. The key follows `edges_by_type` when both variables are new, outgoing adjacency when the source was already bound, and incoming adjacency when only the target was already bound. Because it uses current bucket positions, it is designed to preserve traversal order after deletion and slot reuse. The same method enables the one-edge local path after deletion.

Nine source-stable workers pass the existing three frame-order schedules and four authored cases. Independent amended analysis verifies 36/36 final graph parity, 594/594 checkpoint parity, goal-state parity, and trace-on/off parity. Per-rule path counters show 34,920 local-pattern calls and zero full fallbacks; this is the first run in this sequence where the graph-global deletion guard no longer sends the multi-edge rules back to full matching.

## Work result

| Measure | Monolithic | v1.8 local-key baseline | v1.9 deletion-safe key |
|---|---:|---:|---:|
| Candidate visits | 18,072 | 170,853 (9.45×) | 226,227 (12.52×) |
| Term evaluations | 51,552 | 654,438 (12.69×) | 1,166,004 (22.62×) |

The more broadly used seeded path increases candidate work 32.4% and Term work 78.2% versus v1.8, despite eliminating fallback. The likely cause is repeated full-pattern expansion for each owned node and pattern variable, compounded by per-binding candidate-position lookup. These work counters do not measure the CPU cost of sorting and rank reconstruction, so they cannot support a wall-time claim. The intended ordering repair passes the current panel but fails the work-reduction objective; do not adopt it as an optimization.

The first v1.9 analyzer run reported one error because it asserted that some full fallback must remain. That expectation was stale after the deletion-safe path was introduced. The raw capture is unchanged; amended analyzer v1.9.1 changes only that assertion to require zero fallback and independently rechecks the capture. Both the original analysis and the correction are retained.

## Next direction

Do not run all-variable seeding on each scope as the default strategy. The next candidate should reduce repeated expansion: declare one scope anchor variable per eligible rule and define scope membership through that anchor, with cross-frame and unowned-anchor controls; keep the generic fallback for rules lacking that contract. Alternatively, reorder a single unseeded join around the ownership-relevant edge, then restore legacy effect order using live candidate ranks. Require exact parity and lower candidate/Term counts; measure wall time separately.

## Provenance

- [v1.9 runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_9.py)
- [Original analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_9.py)
- [Amended analyzer v1.9.1](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_9_1.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_9_lock_20261003.json)
- [Capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_9_20261003.json)
- [Original analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_9_analysis_20261003.json)
- [Amended analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_9_1_amended_analysis_20261003.json)
