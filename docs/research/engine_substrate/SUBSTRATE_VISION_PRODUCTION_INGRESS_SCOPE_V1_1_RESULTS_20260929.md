# Production visual ingress and frame-scope pilot v1.1 results

## Result

The source-locked v1.1 repeat completed all 32 workers across three independently adapted checkpoints: 30 seed × blank/orientation × scope conditions and two deliberate ownership omissions. The corrected independent analyzer passes 12/12 integrity checks. All 32 workers retained the locked source/native fingerprints; every one of the 256 adapter calls delivered `lum_raw` pixels exactly, and every worker recorded all four temporal phases.

At each phase, the target sheet received one known grating image through `WaveWorld.step(frame=...)`; the sibling sheet received a blank image through the same adapter. Under root-scoped settling, the sibling's `act`, `act_next`, and `rate` vectors were exactly invariant to the target orientation/phase in all 24 comparisons (maximum absolute difference 0). Under global settling, all 24 comparisons changed; the largest sibling-state difference was 43.2315. This is direct evidence that the global rule transfers visual-sheet state and the root-scoped variant blocks that transfer on this workload.

The phase-averaged target rate-sum had the same dominant orientation under both scope variants within each seed: 45° for seed 20260935, 135° for 20260936, and 0° for 20260937; 90° did not dominate. This is a descriptive readout of three adapted checkpoints, not held-out classifier accuracy. The dominant orientation is seed-sensitive, so the panel does not establish reliable orientation recognition.

Across the 15 non-omission workers per scope, median worker wall time was 0.390 s global and 0.309 s root-scoped; median process CPU time was 0.390 s and 0.309 s. These include eight sequential adapter calls and state capture. Process peak RSS reached 130.3 MiB global and 130.9 MiB root-scoped. The medians are descriptive; the first blank worker per seed includes a 2.2–5.5 s outlier, and this small panel is not a scaling estimate.

The owner-edge omission control removed the target unit at index 0 from its root in both scope arms. Its `act_next` stayed at its checkpoint value (19.38995) across all four phases and differed from the matched fully owned unit in every phase. The global scan also requires an owner-root match to bind its output; the type-wide SUnit fold does not make an unowned unit an output binding. This control confirms that declared ownership participates in rule output coverage.

## Readout limitation

The adapter returns after the complete `tick`, so this capture does not expose the exact internal rate-write phase. The post-hoc final snapshots contain 4,096 unit samples whose `act_step` and `rate_step` agree; 1,208 have `abs(rate - max(act - theta, 0)) > 1e-9`, with a maximum residual of 22.9869. Equal update stamps do not prove that the values were observed at the same internal phase, so this discrepancy is a diagnostic and the registered same-phase equation oracle remains unverified. A follow-up needs phase-local state capture or an instrumented adapter that is first shown equivalent to the default `WaveWorld.step` path.

## Censored first capture and analysis correction

The initial v1 raw capture is retained but censored because `rewrite.rs` changed during the run and the native extension became stale. The current engine was rebuilt through `scripts/engine_build.sh`; v1.1 then passed two identical source-lock probes 20 seconds apart and remained stable through all workers.

The first v1.1 analyzer compared a row's prepared-graph digest to the hash of its checkpoint file. That gate failed for the wrong reason. The corrected analyzer verifies the checkpoint file against the source lock, recomputes the canonical graph digest, and compares it to the worker's prepared-graph digest. The initial analyzer and output are retained unchanged; the corrected output passes all 12 checks. See the [analysis amendment](SUBSTRATE_VISION_PRODUCTION_INGRESS_SCOPE_V1_1_ANALYSIS_AMENDMENT_20260929.md).

## Claim boundary and next gate

This advances the visual evidence from a synthetic `st_settle` graph to image-valued inputs through the production `WaveWorld.step` adapter, on a two-sheet shared substrate and three frozen adapted states. The roots are supplied by the fixture, the stimuli are synthetic gratings, the sheets are stepped sequentially, and no frame-discovery cost is measured. It is not natural-image recognition, learned cheap-cut discovery, or a general CPU complexity result.

Next instrument exact per-rule phase snapshots and closure termination for the production adapter, checking that the instrumented path preserves the default final graph. Then use that trusted measurement path for a larger multi-frame and image-family panel, with frame discovery charged separately. General tractability still depends on the untested prevalence of low-width learned cuts; rung 3/4 induction and minting remain open.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_VISION_PRODUCTION_INGRESS_SCOPE_V1_PREREG_20260929.md) and [v1.1 source-drift amendment](SUBSTRATE_VISION_PRODUCTION_INGRESS_SCOPE_V1_1_AMENDMENT_20260929.md).
- [Runner](../../../scripts/substrate_vision_production_ingress_scope_v1_1.py), [locked initial analyzer](../../../scripts/analyze_substrate_vision_production_ingress_scope_v1_1.py), and [corrected analyzer](../../../scripts/analyze_substrate_vision_production_ingress_scope_v1_1_corrected.py).
- [Source lock](../../../evaluation/substrate_capability/vision_production_ingress_scope_v1_1_20260929_lock.json), [raw capture](../../../evaluation/reports/vision_production_ingress_scope_v1_1_20260929_raw.json), [initial analysis](../../../evaluation/reports/vision_production_ingress_scope_v1_1_20260929_analysis.json), and [corrected analysis](../../../evaluation/reports/vision_production_ingress_scope_v1_1_corrected_analysis_20260929.json).
- [Censored v1 raw capture](../../../evaluation/reports/vision_production_ingress_scope_v1_20260929_raw.json) and [censored v1 lock](../../../evaluation/substrate_capability/vision_production_ingress_scope_v1_20260929_lock.json).
