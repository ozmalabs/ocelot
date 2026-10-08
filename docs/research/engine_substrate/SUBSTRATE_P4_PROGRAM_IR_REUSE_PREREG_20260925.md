# P4 Program IR retention, verification, and reuse preregistration

**Question.** For one existing P4 string task with a successful accepted route, what are the costs of fresh P4 acquisition, post-acquisition verification through the production `ProgEval` path, graph-resident IR export/restore, and repeated use of the retained IR?

## Workload and path

Use the frozen `contrast_reverse_string_01` task from `tests/fixtures/substrate_string_pbe_contrast/tasks.json`: four revealed and three held-out string examples. Run standard `prog_synthesis_battery.boot(frozen=False)` and `domains.prog_synthesis.synthesize_from_request` without ablations or budget overrides. This is a known successful task from a generated contrast suite and is selected to exercise P4, not to estimate suite-level success. Perform three independent fresh-Substrate acquisitions. Record boot, route, and total wall/CPU costs separately, final status/construction, and `ir` fingerprint. All three must be accepted with identical IR and pass all seven rows when executed through `ProgEval`.

## Verification, retention, reuse

For each acquisition, time independent ProgEval verification over all four revealed and three held-out rows. Reflect the accepted IR with `add_term_subgraph`, export it using `term_subgraph_json`, remove the live root, restore from the exported JSON via `add_term_subgraph`, and require byte-stable re-export plus identical seven-row outcomes. Record serialized bytes, export/restore time, graph node delta before and after root removal, and application timing after 100 warm-up calls. Time 100, 1,000, and 10,000 repeated `ProgEval` calls, cycling across the three held-out rows, with every result checked. After application timing, measure fresh add/remove cycles of 1, 10, and 100 IR roots on the same adapter. At each cumulative point record graph node count, compact serialized whole-graph bytes, and current process RSS; this is a diagnostic for retained-subgraph cleanup, not a required semantic gate. Also retain the round-tripped graph root for per-call application after restoration; do not include JSON parsing in those hot calls.

## Gate and limits

Gate passes only if all three fresh routes accept the same IR, every route's seven examples and every repeated use match, and round-trip serialization is stable. Report raw repeats, not just medians. Setup/seed installation, route acquisition, explicit verification, IR graph retention/export/restore, and hot application are separate cost buckets. This is one known-success task; it does not measure broad P4 success, natural task prevalence, update maintenance, full-adapter checkpoint durability, or LLM comparative cost. No engine or default behavior changes are part of this experiment.
