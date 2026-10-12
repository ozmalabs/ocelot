# Live runtime closure-entry replay v2 results

## Question

Does exact preservation of match-clause order and `mutation_protected` metadata improve per-rule counter reproduction when replaying captured primary closure calls?

## Result

The v2 exact-import API was added to the native binding and compiled into the source-matched engine. It restores the ordered rule list and protection metadata without changing ordinary `import_rules` behavior. The v2 runner confirms graph and rule round-trips for all 15 captured calls (10 for request 1, 5 for request 2), including 35,340 protected-rule instances across the call states, and its before/after source lock is stable.

It does **not** close the counter gap. Only 6,760/13,389 metric cells match exactly (50.49%). Request 1 candidate tests are 82,009 replay vs 74,175 live (+7,834; +10.6%); Term evaluations are 887,620 vs 803,675 (+83,945; +10.4%). Request 2 candidate tests are 43,650 vs 36,021 (+7,629; +21.2%); Term evaluations are 452,204 vs 373,832 (+78,372; +21.0%). Rule-enumeration totals also differ: 29,247 vs 26,619 in request 1 and 13,808 vs 12,521 in request 2. These aggregates reproduce the v1 mismatch exactly.

## Interpretation and next gate

Loss of `mutation_protected` metadata was not the cause. The replay remains procedure-valid, but is not a faithful runtime replay because the capture has graph and rule definitions, not scheduler state. Next capture and restore per-rule dirty bits and dirty-node sets, per-edge-type cursor positions and deletion versions, global deletion version, and `any_mutation`; then compare again. If deltas remain, extend the checkpoint to closure-affecting configuration and cache state. Do not interpret these route-specific deltas as evidence against the instrumented live counters; they show that graph/rule snapshots alone are insufficient to reproduce the live scheduler's work.

## Scope and artifacts

This is one authored route through the primary adapter and 15 native `run_rules` calls. It says nothing by itself about natural-task prevalence, rung-3 learning, or scale. The preregistration is [here](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V2_PREREG_20261004.md); source-locked runner and independent analyzer are [here](../../../evaluation/substrate_capability/live_runtime_closure_entry_replay_v2.py) and [here](../../../evaluation/substrate_capability/analyze_live_runtime_closure_entry_replay_v2.py). Raw replay and analysis are [here](../../../evaluation/reports/live_runtime_closure_entry_replay_v2_20261004.json) and [here](../../../evaluation/reports/live_runtime_closure_entry_replay_v2_analysis_20261004.json); the source lock is [here](../../../evaluation/substrate_capability/live_runtime_closure_entry_replay_v2_lock_20261004.json).
