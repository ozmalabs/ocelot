# Cognition Build Phase 3 — Results

**Execution date:** 2026-10-21
**Implementation commit:** `32143620`
**Pre-registration commit/hash:** `eb34efb394a50559be05f063d20467550b905795`
**Held-out report:** `evaluation/reports/extended_thinking_heldout_v1_eb34efb3_d0-200.json` (generated, not committed)
**Analysis:** `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/substrate_capability/extended_thinking_analysis_v1.py evaluation/reports/extended_thinking_heldout_v1_eb34efb3_d0-200.json`

## Outcome

The bounded executor solved all 200 Family-A grain instances and all 200 Family-B linear-generator instances with the policy on. It solved none of the 300 control instances. The registered H1, H2, H3, and H5 criteria pass. H4 fails for Family A and passes for Family B.

| Family | n | `et_on` solved (Wilson 95%) | `et_off` solved (Wilson 95%) | Paired gain | Exact McNemar p |
|---|---:|---:|---:|---:|---:|
| A | 200 | 200/200 (1.000; 0.981–1.000) | 0/200 (0.000; 0.000–0.019) | 1.000 | 1.24e-60 |
| B | 200 | 200/200 (1.000; 0.981–1.000) | 22/200 (0.110; 0.074–0.161) | 0.890 | 5.22e-54 |
| Random-cell control | 100 | 0/100 (0.000; 0.000–0.037) | 0/100 (0.000; 0.000–0.037) | 0.000 | 1.000 |
| Value-noise control | 100 | 0/100 (0.000; 0.000–0.037) | 0/100 (0.000; 0.000–0.037) | 0.000 | 1.000 |
| Quadratic-warp control | 100 | 0/100 (0.000; 0.000–0.037) | 0/100 (0.000; 0.000–0.037) | 0.000 | 1.000 |

The pooled control false-accept rate was 0/300 for both arms; the `et_on` Wilson upper bound was 0.0127. Family-A `et_on` needed one step on every first encounter and one step on every second encounter, so the registered “second encounter uses fewer steps in at least 90%” criterion failed (0/200). This is consistent with P3.A7’s specified cache behavior: a cached rung-1 entry begins at the cached winner and applies that rung in one funded step. Because the generated Family-A cases all have rung 1 as their winner, the cache has no lower rung count to save. Family B had zero second-encounter steps in 200/200 cases because the minted generator persisted.

Total recorded spend was 2,734 against a registered funding upper bound of 67,200. Every applied step was backed by an approved request. The outputs establish behavior on these randomized synthetic families only; they do not measure natural perception, language, planning, or human-level cognition.

## Hypothesis decisions

| Hypothesis | Result | Evidence |
|---|---|---|
| H1, Family-A gain ≥0.5 and McNemar p <0.01 | **Pass** | Gain 1.000; p=1.24e-60 |
| H2, Family-B gain ≥0.5 and McNemar p <0.01 | **Pass** | Gain 0.890; p=5.22e-54 |
| H3, control false-accept guard | **Pass** | `et_on` 0/300, upper bound 0.0127; `et_off` 0/300 |
| H4, second-encounter cache | **Fail overall** | Family A: 0/200 below first-encounter steps; Family B: 200/200 zero-step repeats |
| H5, budget accounting | **Pass** | No unfunded applied steps; 2,734 spend ≤67,200 bound |

The Family-A H4 failure is a design limitation in the registered instance family and criterion: all Family-A first encounters succeed at rung 1, and P3.A7 caches rung 1 for a one-step replay. The test therefore cannot demonstrate a lower second-encounter step count. The preregistered criterion is retained unchanged in this report.

## Verification and gate

- P3 evaluator, instance, executor, spike, ladder-recorder, cognition-profile, and orphan-lint tests: **26 passed**.
- Pinned baseline command, `.venv/bin/python scripts/failure_baseline.py verify --list results/cognition_gate_baseline.json`: **4 held baseline failures, 0 stale, 0 new**.
- Per-file gate sweep, `.venv/bin/python scripts/failure_baseline_sweep.py --files-from scripts/cognition_gate_suite.txt --workers 4 --timeout 420 --out /tmp/p3-cognition-gate-sweep.json`: **16 green, 2 baseline-red, 1 all-skipped, 1 NOT_ESTABLISHED**. The baseline-red files are `test_frozen_core_invariant.py` and `test_dual_process_core_migrated.py`; their failures are listed in the pinned baseline. `test_capability_control_fabric_migrated.py` exceeded 420 seconds, matching its prior NOT_ESTABLISHED classification. No new failures were found.
- Frozen core seed comparison from P3 start commit `ff689b30`: no changes to `shape_decode_loop`, `dual_process_core`, `default_mode_core`, or `generative_world_model` seeds.
- `extended_thinking` and `inference_ladder_record` classify as SLO. Default-profile integration verifies neither is installed by `WorldAdapter()`.
- The separate P2 gate evidence and known Cargo results are recorded in `COGNITION_BUILD_P2_RESULTS.md`.

## Quadratic and time rungs

**Quadratic default-feature decision: no.** Keep `geninfer_quadratic_map_solver` experimental and off by default. P3’s executor has no quadratic rung, the feature is not required for the supported DimInfer/linear-GenInfer ladders, and the quadratic-warp control remains unsolved in both arms. A feature build and dedicated solver benchmark belong in a separate engine decision; no Cargo defaults changed in P3.

The TimeInfer rung remains deferred to Track I / P4 because an `Observation` carries a single signature rather than the frame sequence required by `time_axis`.
