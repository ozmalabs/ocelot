# Conversation task scope selectivity v2.1.1 results

Date: 2026-10-03  
Protocol and amendments: [selectivity preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_SELECTIVITY_V2_1_PREREG_20261003.md)  
Runner: [selectivity pilot](../../../evaluation/substrate_capability/conversation_task_scope_selectivity_pilot_v2_1_1.py)  
Analyzer: [independent analysis](../../../evaluation/substrate_capability/analyze_conversation_task_scope_selectivity_pilot_v2_1_1.py)  
Source lock: [v2.1.1 lock](../../../evaluation/substrate_capability/conversation_task_scope_selectivity_pilot_v2_1_1_lock_20261003.json)  
Capture: [v2.1.1 capture](../../../evaluation/reports/conversation_task_scope_selectivity_pilot_v2_1_1_20261003.json)  
Analysis: [v2.1.1 analysis](../../../evaluation/reports/conversation_task_scope_selectivity_pilot_v2_1_1_analysis_20261003.json)

## Result

The nine-worker matrix covers 81 paired cases and 954 checkpoints. All runner gates pass: source stability, exact fallback/anchor checkpoint and final states, goal lifecycle parity, trace-on/off parity, anchor-path use, verified fallback-arm isolation, cross-frame/orphan proof rejection, and nonempty traces with no drops. The full-fallback arm recorded zero declared-anchor attempts and zero anchor-proof rejections in every case; it recorded full-matcher calls as required.

Across the full matrix, declared-anchor matching uses 1,599,627 Candidate pairs and 6,011,472 Term evaluations, compared with 2,413,170 and 9,138,258 for verified full fallback. That is a 33.7% Candidate reduction and 34.2% Term reduction. Semantic-edge counters account for all Candidate pairs in both arms, with zero unassigned work. The anchor arm remains above monolithic closure on this panel: 2.61× its Candidate work and 2.80× its Term work.

For the two-goal selectivity cells, each dose contains nine paired runs (three schedule orders × three replicates):

| Unowned decoy Goal/Event pairs | Candidate reduction | Term reduction |
|---:|---:|---:|
| 0 | 29.4% | 18.1% |
| 32 | 32.1% | 32.5% |
| 256 | 32.3% | 33.2% |
| 1,024 | 32.3% | 33.3% |

The controlled workload supports a specific claim: when complete but lifecycle-ineligible pattern components are unowned by every frame, the declared Goal anchor avoids a material portion of their repeated matching and predicate work while preserving exact states. It does not show that natural task graphs have this distribution, that anchor discovery is free, or that the engine is cheaper than monolithic closure overall. Timing was not used as a success criterion.

The earlier v2.1 exploratory capture passed the runner gates but its independent analyzer retained the old six-cases-per-worker assertion. Its capture and failed analysis are preserved; v2.1.1 reruns the same matrix with the corrected nine-case assertion and is the reported result.

## Correction to v2.0 findings

The v2.0.1/v2.0.2 runner patched `substrate.seed_loader.manifest_for`, but `substrate.boot_core` retains a module-level imported reference. Consequently, the arms labelled `partition_fallback` also loaded anchor metadata and exercised the anchor/rejection path. Their state-parity and ownership-guard observations remain evidence about the anchor-enabled implementation; their anchor-versus-fallback work comparisons are invalid. In particular, v2.0.2's equal semantic-edge counts compare two anchor-enabled arms and cannot support a claim that clause reordering leaves the generic fallback search tree unchanged. The v2.1.1 runner patches both module references and includes a hard counter gate proving isolation. See the [v2.0 preregistration amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_DECLARED_ANCHOR_V2_PREREG_20261003.md) and [corrected overall status](SUBSTRATE_CAPABILITY_AND_TRACTABILITY_OVERALL_STATUS_20260929.md).

## Next gate

Retain the verified fallback-isolation gate and the 0–1,024 decoy dose response. Next vary degree skew and decoy relation structure independently, including decoys that share only selected pattern edges, so the evaluation distinguishes anchor pruning from complete-component filtering. Add controlled graph-size and memory measures, then test at least one naturally harvested task graph with independently labeled ownership. Require parity and work reduction at each workload family; do not extrapolate this authored case to natural-task prevalence.
