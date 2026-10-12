# Response-priority residual-continuation v1.2 candidate: diagnostic result

Date: 2026-10-06  
Status: one-worker-per-arm source-locked diagnostic; initial graph-parity gate failed, then passed after a second measured fix. Three-worker confirmation and the separate cost panel completed.

## Implementation correction

The Python binding represented the canonical default area as `"global"` when listing rule areas, but converted a selected `"global"` label into a newly interned symbol. That symbol did not equal `Sym::default()`, so selected settlement silently omitted default-area rules. The same conversion affected `set_rule_area`. Both paths now map the canonical label to `Sym::default()` in [py.rs](../../../runners/dsl/src/py.rs). `cargo check --manifest-path runners/dsl/Cargo.toml --lib` and release `maturin develop` completed successfully.

The v1 and v1.1 selected-arm captures therefore did not exercise the intended selected global rules. Their specific claims about missing composer execution and the unexplained global residual are superseded. Their captured lifecycle evidence about recurrence consumers versus duplicate retirement remains useful for the rules explicitly reassigned to named non-default areas; do not treat the earlier runs as validation of complete selected-area semantics.

## Candidate result

After rebuilding, the preregistered v1.2 one-worker-per-arm pair selected `response_critical` and the canonical `global` area. Dynamically authored composer rules ran; `conceptualize_reply` returned a committed intent. Replies matched on all seven turns. Both arms reached zero residual without hitting the round cap after continuation.

The first corrected pair still failed graph parity by one `RuleFiringHistory` node and its `has_rule_firing_history` edge. Source tracing found that the global fixpoint records its last progressing rule for the host ledger, while `run_rules_settle_inner` did not. The selected scheduler now records that same turn-scoped progress evidence. A second source-locked pair then matched normalized graph fingerprints, node/edge cardinalities, replies, and zero-residual completion on all seven turns. The ledger recorded `conceptualizer_output_candidate_commit` and matching settlement sequences in both arms. This finite pair passes its candidate gates; it is not yet confirmatory.

| Gate | Result |
|---|---|
| Source and worker inputs stable | Pass |
| Canonical `global` selected | Pass |
| Composer intent/commit present | Pass |
| Replies match all seven turns | Pass |
| Both continuations converge with zero residual | Pass |
| First corrected pair graph parity | Failed by one firing-history record and edge |
| Pair after firing-history capture fix | Pass: graph fingerprints and cardinalities match on all seven turns |
| Confirmatory multiworker panel | In progress under a separate preregistration |

This remains one exploratory pair. Instrumented timing is not a speed estimate, and the result says nothing about how often the candidate partition helps on natural tasks. The source-level cause is closed for this path: selected settlement now supplies the same last-progress datum to the turn-scoped firing-history ledger. The separate three-worker-per-arm confirmation passed; it supports finite semantic parity only for this workload. The later uninstrumented cost panel is reported separately in [cost results](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_COST_RESULTS_20261006.md). Keep response utility, residual work, graph parity, and timing as separate gates.

## Artifacts

- [Preregistration](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_PREREG_20261006.md)
- [Runner](../../../scripts/substrate_response_priority_residual_continuation_v1_2_candidate_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/response_priority_residual_continuation_v1_2_candidate_20261006_lock.json)
- [Compact capture](../../../evaluation/reports/response_priority_residual_continuation_v1_2_candidate_20261006/capture.json.gz)
- [Analysis](../../../evaluation/reports/response_priority_residual_continuation_v1_2_candidate_20261006/analysis.json)
- [Confirmatory preregistration](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_CONFIRMATORY_PREREG_20261006.md)
- [Confirmatory runner](../../../scripts/substrate_response_priority_residual_continuation_v1_2_confirmatory_20261006.py)
