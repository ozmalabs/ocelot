# Native residual-to-composer cue derivation v1 results (2026-10-03)

## Result

The source-locked 13-case CoW panel passed the corrected independent analysis. A candidate-only native graph rule consumed raw `actual`/`expected` action fields plus a fixed cardinal-action ontology and created a `CapabilityAxis` cue. All four opposite-action cases produced the expected `flip_comparison` proposal for `hop_descend_gradient` and passed both held-out directions. Eight orthogonal, same-direction, unknown, missing, or zero-displacement controls produced no cue and no proposal. The absent-target control derived the cue but emitted no proposal. Baseline branches using the ordinary generic residual path proposed nothing in all 13 cases.

Exploration remained isolated in both branches for every row. Primary graph, rules, and revision stayed unchanged until return; each primary received exactly one `ExperimentResidual`, with no exploratory rule or graph changes copied back. Candidate branches grew by 25–30 rules and 31–72 nodes, which stayed branch-local. Median time was 0.279 ms for the two snapshot forks, 5.891 ms for induction/settlement, 0.245 ms for candidate grounding, and 0.231 ms for raw baseline grounding. These timings exclude fixture setup and held-out scoring and do not establish an end-to-end speedup.

Artifacts: [protocol](RESIDUAL_TO_COMPOSER_NATIVE_CUE_V1_PREREG_20261003.md), [runner](../../../evaluation/substrate_capability/measure_residual_to_composer_native_cue_v1.py), [original analyzer](../../../evaluation/substrate_capability/analyze_residual_to_composer_native_cue_v1.py), [corrected independent analyzer](../../../evaluation/substrate_capability/analyze_residual_to_composer_native_cue_v1_1.py), [source lock](../../../evaluation/substrate_capability/residual_to_composer_native_cue_v1_lock_20261003.json), [capture](../../../evaluation/reports/residual_to_composer_native_cue_v1_20261003.json), and [corrected analysis](../../../evaluation/reports/residual_to_composer_native_cue_v1_1_analysis_20261003.json).

## Interpretation and limits

This demonstrates that the native graph-rule engine can derive a bounded operator cue from a raw task residual when the relevant action relation is already represented in the graph. It moves the per-trial mapping out of Python and into branch-local substrate execution, then uses the existing composer and isolated held-out scorer. The cue rule, action-pair ontology, cue vocabulary, and target class are all authored inputs; the substrate did not learn the rule or relation table. This is a staged integration result, not autonomous self-improvement or evidence about natural task frequency.

The original v1 analyzer's gate result was correct, but its summary read a nonexistent top-level fork field and printed 0.0 ms. The raw capture contains both fork timings. The separately hashed v1.1 analysis recomputes the fork median from those branch records without modifying the capture or acceptance criteria.
