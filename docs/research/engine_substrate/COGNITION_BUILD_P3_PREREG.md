# Cognition Build Phase 3 — Held-Out Executor Evaluation Pre-Registration

**Protocol:** `extended_thinking_heldout_v1`
**Date:** 2026-10-21
**Plan:** `COGNITION_BUILD_P3_EXTENDED_THINKING_PLAN.md` §P3.H9
**Frozen before any held-out draw.**

## Why

Phase 3 adds a graph-rule executor that can widen two inference settings after a default explanation fails: the DimInfer grain ladder and the GenInfer linear-generator rung. This evaluation measures whether that mechanism solves held-out synthetic instances, preserves its control guards, and reuses its learned result on a second encounter. It does not measure human-level reasoning.

## What changed

The evaluated arm enables `ExtendedThinkingPolicy` and `ThinkingBudget`. Each widening step creates an `ExtendedThinkingStepRequest`, and the shared budget approves or denies it. The executor re-decodes one observation, verifies the result through the existing inference machinery, and restores the original setting at a terminal outcome. A successful DimInfer rung is cached by observation key; a GenInfer generator persists in the codebook.

The `et_off` arm uses the same seeds, instances, clock samples, tick limit and base codebook with the executor policy disabled. Each arm receives a fresh agent for the first encounter. The second encounter uses the same agent and the same instance key.

## Frozen at this commit

- `seeds/extended_thinking.json`
- `seeds/inference_ladder_record.json`
- `scripts/gen_extended_thinking_seed.py`
- `scripts/gen_inference_ladder_record_seed.py`
- `evaluation/substrate_capability/extended_thinking_instances_v1.py`
- `evaluation/substrate_capability/extended_thinking_heldout_v1.py`
- `evaluation/substrate_capability/extended_thinking_analysis_v1.py`
- `tests/test_extended_thinking_migrated.py`
- `tests/test_extended_thinking_instances_v1.py`
- `tests/test_extended_thinking_analysis_v1.py`

Changes to any frozen file invalidate this registration and require a new preregistration before further draws.

## Procedure

1. Let `h` be the full Git commit hash of this document. Draw `i` uses `seed = int(h[:8], 16) + 7919*i`.
2. Run `evaluation/substrate_capability/extended_thinking_heldout_v1.py <h> 0 200`. Draw indices 0–199 produce one Family-A and one Family-B instance each; indices 0–99 also produce one instance for each control family. This yields 200 Family-A, 200 Family-B, and 100 instances for each of the three controls (random-cell, value-noise, quadratic-warp). Each instance is paired across `et_on` and `et_off`.
3. Each instance starts with a fresh agent per arm. The runner feeds at most 20 `NetworkModeSample` epochs to reach a terminal status. The budget begins with capacity 16 and refills by 2 per epoch. It records solution status, applied steps, budget spend, relaxed-acceptance provenance, controls' false accepts, and a same-agent second encounter.
4. Analyze the resulting report with `evaluation/substrate_capability/extended_thinking_analysis_v1.py <report.json>`. The exact McNemar test is paired by instance; every reported rate includes a Wilson 95% interval.
5. Commit the results document with the preregistration hash, the report path, analysis command, all hypothesis outcomes and the observed measurements. Reports under `evaluation/reports/` are generated artifacts and are not committed.

## Hypotheses

- **H1 (Family A):** The `et_on` solve-rate gain over `et_off` is at least 0.5 and the exact two-sided McNemar p-value is below 0.01.
- **H2 (Family B):** The same thresholds hold for Family B.
- **H3 (guard):** Across all controls, the `et_on` false-accept rate is at most 0.05, its Wilson 95% upper bound is at most 0.10, and its rate is no more than 0.02 above `et_off`.
- **H4 (cache):** Among solved `et_on` Family-A instances, second-encounter steps are lower than first-encounter steps in at least 90%. Among solved Family-B instances, second-encounter steps are zero in at least 95%.
- **H5 (budget):** No applied step exceeds the count of approved requests, and total spending does not exceed the upper bound on total funding.

## What this does and does not test

This tests a bounded synthetic mechanism on randomized shapes, integer-linear transforms, and explicit controls. A Family-A false accept means coarse-grain relaxation explained a random set, dissolving a real residual; that is the motivated-relaxation failure this guard hypothesis is intended to detect. Results do not establish performance on natural perception, language, planning, people, or human-level cognition.
