# Residual-to-composer cue derivation v1 results

The 13-worker source-locked capture passes all preregistered semantic gates. Four faulted navigation directions produce the expected opposite action. A deterministic action-vector check emits the held `flip_comparison` cue in each case; `ground_concern` proposes `flip_comparison` on `hop_descend_gradient`; and each proposal passes both held-out navigation cases with verified candidate receipt and the active target rule preserved. Four synthetic valid non-inverted residuals and four synthetic malformed/underdetermined residuals abstain. In the absent-target control, cue derivation succeeds but composer grounding emits no candidate. There are zero false proposals across nine controls.

Median induction time is 5.86 ms and median grounding time is 0.285 ms on this host. These timings omit task/bootstrap setup and are not an end-to-end latency estimate.

## Interpretation and limits

This closes one narrow handoff: an authored action-vector decoder can translate a known polarity error into the exact composer vocabulary already used by A8. The decoder explicitly contains the action geometry and operator cue schema; neither was induced by the substrate. This is not open-ended diagnosis, new-operator learning, broad transfer, or autonomous self-improvement.

The complete graph rule-store changed during the operation even when no proposal was returned. Every trial added 24 active reflective/shape-decode rules when `induce_concern` initialized its loop. Cue-positive and absent-target trials added five more rules, including two residual-key-specific experiment/judgment rules. The target repair rule remained unchanged in the four successful proposal contexts. This is evidence that the operation is isolated only because each worker used a fresh experimental context; target-rule preservation alone is not a sufficient mutation-safety check. The next gate should run induction and proposal inside a copy-on-write Thoughtexperiment branch, compare full graph/rule deltas, and explicitly test which residual artifacts can be returned without merging exploratory rules.

## Artifacts

- Protocol: [preregistration](RESIDUAL_TO_COMPOSER_CUE_DERIVATION_V1_PREREG_20261002.md)
- Runner: [measurement script](../../../evaluation/substrate_capability/measure_residual_to_composer_cue_derivation_v1.py)
- Analyzer: [independent gate checker](../../../evaluation/substrate_capability/analyze_residual_to_composer_cue_derivation_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/residual_to_composer_cue_derivation_v1_lock_20261002.json)
- Raw workers: [capture](../../../evaluation/reports/residual_to_composer_cue_derivation_v1_20261002.json)
- Analysis: [gate results](../../../evaluation/reports/residual_to_composer_cue_derivation_v1_analysis_20261002.json)
