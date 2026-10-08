# Thoughtexperiment shape-axis full-candidate admission v1 — results

**Result:** 12/12 independent integrity gates pass.

Four fresh worker processes scored all six unchanged-generator candidates on separate training and held-out shape contexts. Candidate label/digest sets were identical across all workers and splits. The signatures were disjoint; every rehearsal used a detached branch; the primary graph/rule revision was preserved. The independent reviewer verified the recorded utility against the four task-oracle fields, checked matrix completeness and source-lock parity, and found no primary-state mutation. It audited the capture; it did not independently execute a second copy of the domain oracle.

| Candidate | Training pass | Held-out pass |
|---|---:|---:|
| `dedup_identity_fix` | 4/4 | 4/4 |
| `swap_term_leaf:key->signature` | 4/4 | 4/4 |
| `add_match_guard(control)` | 0/4 | 0/4 |
| `swap_term_leaf:signature->key` | 0/4 | 0/4 |
| `swap_term_leaf:signature->name` | 0/4 | 0/4 |
| `swap_term_leaf:signature->residual` | 0/4 | 0/4 |

The second passing edit is a useful update to the earlier stop-on-success trace: the unchanged candidate generator contains two task-useful variants on this shape-axis task, not only `dedup_identity_fix`. This remains one authored rule and one family of synthetic observation signatures; workers replicate the same task shape, so the result does not show transfer to a new task family or autonomous candidate generation.

Median per-candidate end-to-end scoring time was 571.5 ms on training contexts and 582.4 ms on held-out contexts. Median detached branch creation was 54.1 ms and 56.0 ms, respectively; median native task-closure time was 1.485 ms in both splits. `context_setup_ns` includes candidate enumeration, so it is not additive with `enumeration_ns`; candidate total is the wall-clock measure. These timings include rebuilding the graph-authored correction context per candidate and are descriptive single-host results, not a commodity-scale cost estimate.

The candidate oracle directly checks that all three new observations settle, exactly one induced axis is present per signature, and native closure reaches a fixed point. A pre-capture adapter attempt using the checked Python edge API failed because the detached graph lacked a type declaration for the injected Agent endpoint; the final scorer inserts the test observations through the native unchecked edge API for the `observed` relation already present in the locked task graph. No failed attempt was counted as a candidate outcome.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_AXIS_FULL_CANDIDATE_ADMISSION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1.py)
- [Lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_axis_full_candidate_admission_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_axis_full_candidate_admission_v1_raw_20261002.json)
- [Independent review](../../../evaluation/substrate_capability/review_thoughtexperiment_shape_axis_full_candidate_admission_v1.py)
- [Review capture](../../../evaluation/reports/thoughtexperiment_shape_axis_full_candidate_admission_v1_review_20261002.json)
