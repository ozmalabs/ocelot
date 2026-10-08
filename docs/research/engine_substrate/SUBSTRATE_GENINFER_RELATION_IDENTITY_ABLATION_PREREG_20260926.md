# GenInfer stable-relation-identity ablation preregistration (2026-09-26)

## Question

Does a stable identity field in each relation prevent the geometry-sensitive alternate-matrix outcomes seen when repeated-predicate relations are paired only by sorted tuple position?

## Design

Repeat the three-layout, four-condition, five-repetition sweep from [`SUBSTRATE_GENINFER_REPEAT_PREDICATE_ROBUSTNESS_PREREG_20260926.md`](SUBSTRATE_GENINFER_REPEAT_PREDICATE_ROBUSTNESS_PREREG_20260926.md) in two paired arms: `no_identity` reproduces its four-slot signatures; `stable_identity` inserts a unique unchanged ID field immediately after predicate and before the two coordinate slots, with `dim_types=[pred,id,coord:r,coord:c,val]`. The coordinate perturbations still increment only the first relation's target row coordinate by +1/+2/+3. Use the same `[1,1,0,2]` map, layouts, predicates, five repeats, and read the same six evaluator fields; no timings.

The existing 60-observation no-identity capture is the locked reference arm. The runner repeats that arm and records its checksum so the analyzer can require exact parity. The identity arm is a new 60-observation capture.

## Hypothesis and gates

Positive cases in both arms recover the exact generator with no residual. With stable IDs, corruptions should be refused: the unchanged IDs fix each held/observed pair, and the p0 pair's coordinate displacement becomes inconsistent with the unperturbed p1 relations for each layout. The key contrast is corrupted cases that were previously accepted with an alternative matrix; the prediction is that stable identity eliminates these acceptances. Verify complete 120-observation paired factorial, exact reproduction of the locked no-identity arm, all positive semantics, refusal in every stable-identity corruption cell, stable repeated outputs, correct candidate counts, and source/native/reference hashes. Any prediction failure remains reported, not silently excluded.

## Claim boundary

This tests one 2-D generator and three small repeated-predicate layouts. Stable IDs are an authored extra signature field and do not model every substrate relation or natural observation. Results would isolate a matcher representation factor in these fixtures; they do not establish general recovery or the desirability/cost of identity-bearing schemas.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_relation_identity_ablation_probe_v1.py
python3 scripts/analyze_substrate_geninfer_relation_identity_ablation_probe_v1.py
```
