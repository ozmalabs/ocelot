# RatioInduce capability audit — 2026-09-26

## Scope and evidence class

This audit checks the native population-level `RatioInduce` Term and its current integration. It is an operator-level re-execution of the existing draft probes, not a new confirmatory population study, and it does not establish automatic acquisition or general concept learning. The three commands below ran against engine `f5543ca01527` (`runners/dsl/python/substrate_rs/_native.abi3.so`). No test suite was run. A post-run semantic correction is also recorded in [`RATIO_INVARIANCE_SEMANTICS_CORRECTION_20260926.md`](../../../drafts/ratio_invariance/RATIO_INVARIANCE_SEMANTICS_CORRECTION_20260926.md).

## Source and integration status

- The native implementation is in `runners/dsl/src/shape_decode.rs::eval_ratio_infer`; `TermNode::RatioInduce` and evaluation/serialization registration are in `runners/dsl/src/term.rs` and adjacent codec/reflect code.
- A recursive search of `seeds/*.json` found no `RatioInduce` invocation. The existing `shape_decode_loop` seed instead has fixed `DimensionGenerator` entries and its mint rule invokes `GenInfer`.
- The Term is therefore directly callable and can produce ratio parameters, but the available evidence does not show that routine seed closure calls it, promotes its output into the live codebook, or reuses that learned ratio on a later task.
- Existing probes are `drafts/ratio_invariance/hr1_synthetic.py`, `hr2_price.py`, and `hr3_audio.py`; the original protocol and results are in `drafts/ratio_invariance/RATIO_INVARIANCE_PREREG.md` and `RATIO_INVARIANCE_RESULTS.md`.

## Re-execution

| Probe | Observed result | What it supports | What it does not support |
|---|---|---|---|
| `PYTHONPATH=.:runners/dsl/python python3 drafts/ratio_invariance/hr1_synthetic.py` | 5/5 planted ratios recovered; scale cancellation true for each; extent-breaking and independent-axis controls return `explained=false`; translation invariance holds | Exact recovery on the five authored integer fixtures; the operation rejects these two mismatched populations | Robustness prevalence, random-distribution generalization, automatic minting, or broad noisy recovery |
| `PYTHONPATH=.:runners/dsl/python python3 drafts/ratio_invariance/hr2_price.py` | P1–P4 pass: integer ratio relation, no input mutation, float coordinates refused, integer map parameters, repeated evaluation gives same ratio | The tested operator stores/applies a relation without continuous in-frame coordinates | Full wire round-trip / codebook promotion / learned-rule persistence (the script re-evaluates JSON; its own comments describe the stronger round-trip structurally) |
| `PYTHONPATH=.:runners/dsl/python python3 drafts/ratio_invariance/hr3_audio.py` | Harmonic-series case recovers 2:1 across six synthesized signals; mixed-ratio and different-vowel controls floor; formant case returns `explained=false` | Transfer to a clean signal-derived feature population and honest rejection of these controls | Natural speech, speaker-invariant formant learning, or robust DSP front ends; waveforms are synthesized and feature extraction is a narrow fixture |

The formant negative result matters: the operator depends on stable integer extents/ratios. The authored LPC features span F2/F1 ratios from 1.757 to 1.850, and the inducer refuses the population. This is a useful limitation report, not evidence that the inducer solved the formant task.

## Capability assessment

**Solution present:** a native population-level ratio detector/parameter inducer exists; tested exact synthetic cases yield reduced integer ratios, choose the scale2 specialization for power-of-two ratios, and refuse tested non-common-scale controls. Its output respects the integer-coordinate representation in the exercised path.

**Gap:** no shipped seed calls the Term, and no end-to-end trace demonstrates induction → durable generator/codebook insertion → subsequent recognition/transformation. Accordingly, RatioInduce does not yet close the rung-3 acquisition gap in the operational substrate. Operator existence must not be reported as substrate learning capability.

**Measurement gap:** the current probes use five planted ratios, hand-authored controls, six synthesized harmonic signals, and four synthesized-vowel cases. They do not sweep sample size, ratio magnitude, missing/duplicate/degenerate frames, quantization, nuisance distributions, runtime/memory, or unseen task reuse. The reported success rate is fixture coverage, not an estimate of natural-task frequency.

## Correction: detected relation is not yet an executable ratio map

Source tracing found a correctness gap in the original H-R2 interpretation. `eval_ratio_infer` reports the full reduced ratio `(num, den)`, but for non-power-of-two ratios its `matrix` stores only `num` on the target diagonal (`runners/dsl/src/shape_decode.rs`, matrix construction after the `all_pow2` check). `apply_linear_once` applies that integer matrix to origin-normalized coordinates and has no access to the denominator (`shape_decode.rs::apply_linear_once`, around line 836). The [source-semantics runner](../../../scripts/substrate_ratioinduce_semantics_probe.py) and [raw output](../../../evaluation/reports/substrate_ratioinduce_semantics_probe_20260926.json) show the 3:2 detector output, matrix `[1,0,0,3]`, and resulting extent ratio 9:2 after applying that matrix. H-R2 P3 establishes integer-shaped params, not semantic equivalence between those params and the recovered ratio; P4 also repeats evaluation rather than exercising serialization encode/decode. The earlier draft's “applied on read” and “full wire round-trip” wording overstates what those checks establish.

There is a second, conceptual mismatch. In this fixture the population has within-frame aspect ratio 3:2 and between-frame scale factors 1, 2, 3, and 5. `RatioInduce` returns the former as a per-coordinate ratio set; it does not report the latter scale factors, a canonical frame, or a generator taking one population member to another. It currently detects a stable within-frame proportion, not a learned reusable operator that factors out population-level scale. The output name and dispatch path are not evidence of a scale-invariant representation until held-out reconstruction or intervention demonstrates that behavior.

Therefore the audit's operator result is **within-frame ratio detection with candidate parameter emission**. Functional non-power-of-two transform/mint/reuse is contradicted by the source-semantics replay. Power-of-two cases need a test that proves they learn between-frame scaling rather than confusing aspect ratios with a common-scale generator. Before seed integration, define the intended task and representation. If the goal is a rational map, retain the full relation as a first-class generator parameter and define integer-observable application; if the goal is common-scale invariance, infer the inter-frame scale relation and canonical representation. Unsupported cases should be refused rather than silently mapped to a different operation.

## Work plan

1. **Representation correctness gate:** define semantics for the full rational relation, or narrow supported ratios. Add an apply/read oracle proving the candidate transform preserves the inferred relation; include 3:2 and an explicit ×3 counterexample. Do this before any mint path.
2. **Promotion contract:** trace the corrected output into a `DimensionGenerator`/`LatentDimension`, codebook registration and epoch/status updates. Add population collection to the production path (currently absent) and define its scope, lifecycle, and duplicate policy.
3. **End-to-end acquisition gate:** present a multi-frame population with an unknown planted ratio to the production seed path. Require the induced structure to appear in live state without harness-side minting; then present a held-out member and require recognized transformation. Include no-common-ratio, single-frame, duplicate, missing-axis, zero-extent, and inconsistent-scale controls.
4. **Robustness matrix:** preregister ratio families, population sizes, integer scale ranges, quantization resolutions, noise and missingness. Use independent seeds and workers, keep all failures, and compare recovery, false induction, and abstention against explicit baselines.
5. **Cost envelope:** separately time feature preparation, direct induction, graph closure, mint/redecode and reuse. Record peak RSS and structural counters alongside wall time; vary frames, dimensions, and ratio magnitude. Do not infer CPU tractability from a handful of sub-millisecond calls.
6. **Capability-map update:** after integration and a confirmatory gate, update rung-3 status to distinguish direct operator evidence from autonomous acquisition and transfer. Until then keep it marked as available mechanism / unintegrated path.

## Decision

The audit upgrades the inventory from “no population ratio inducer found” to “native direct-call within-frame ratio detector with narrow positive and negative evidence; emitted non-power-of-two map semantics are contradicted; population-scale learning and seeded integration are absent.” It does not change the broad tractability conclusion: application of held structure has several measured bounded regimes, but acquisition of new structure remains a distinct and incompletely integrated capability.
