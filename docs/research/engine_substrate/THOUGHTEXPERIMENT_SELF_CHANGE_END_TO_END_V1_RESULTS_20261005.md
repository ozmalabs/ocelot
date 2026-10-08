# Graph-native self-change end-to-end repair v1 results

All gates pass in three source-locked workers, each paired across full-copy and shared-graph-page CoW rehearsal (six complete lifecycles). In each run, the graph-native seed generated the `threshold_adjustment` clause from the FaultProbe signals while `target_uid=0`. Branch rehearsal used actual task behavior: the candidate yields `[true,false]` on training inputs `[1,0]`; no-op and placebo both yield `[false,false]`. The graph proof gate selects the candidate.

After selection, the harness binds the RulePatch to the real target UID/revision/hash for CAS. The candidate produces `[true,true,true,false,false]` on disjoint canary inputs `[2,3,4,-1,-2]`; the graph requests commit and Rust commits once, advancing revision 0→1 and storing status `committed`. Fresh post-commit inputs `[5,-3]` yield `[true,false]`. Target revision remains 0 during proposal rehearsal; full-copy and CoW arms have exact semantic parity.

| Median phase | Full copy | Shared graph pages |
|---|---:|---:|
| Candidate, no-op, and placebo training rehearsal | 2.763 ms | 2.938 ms |
| Graph selection tick | 0.093 ms | 0.094 ms |
| Disjoint canary rehearsal | 2.801 ms | 2.070 ms |
| Commit tick | 0.197 ms | 0.143 ms |
| Fresh final verification | 1.350 ms | 1.075 ms |

The three-pair timing panel is too small and the fixture too small to support a speed claim. It does show that the full self-change path consumes the shared-page backend correctly and preserves exact outcomes. The measurement excludes process startup and uses one authored threshold task. Threshold sensitivity is supplied as an input cue, the candidate vocabulary/grammar is fixed in the seed, and the task oracle is harness-defined. Target UID is withheld during candidate generation/selection and attached only after a candidate is chosen. This establishes a narrow graph-generated proposal → measured branch rehearsal → proof gate → disjoint canary → guarded CAS lifecycle. It does not demonstrate target/cue-free diagnosis, open-ended candidate invention, natural-task generalization, or autonomous self-improvement.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_SELF_CHANGE_END_TO_END_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_self_change_end_to_end_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_self_change_end_to_end_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_self_change_end_to_end_v1_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_self_change_end_to_end_v1_20261005.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_self_change_end_to_end_v1_analysis_20261005.json)
