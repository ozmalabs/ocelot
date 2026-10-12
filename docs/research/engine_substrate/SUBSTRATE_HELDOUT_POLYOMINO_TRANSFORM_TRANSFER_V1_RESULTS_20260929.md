# Held-out polyomino transform-transfer v1 results

**Status:** complete; all eight integrity gates pass. **Question scope:** zero-shot use of the graph-native transform recognizer on 12 new monochrome base-shape orbits, not learning new shapes or transforms. **Scoring boundary:** the reported exact-key outcomes are the `recognise_required_key` adapter's canonical labels, not a direct count of graph-level recognition/refusal states.

## Positive transform outcomes

The independent analyzer confirms that all 12 connected polyominoes (sizes 5–7) have trivial dihedral stabilizers and are orbit-disjoint from the six shapes in the current LS20 corpus. Each was evaluated under all six known operators. The clean task set yields 71/72 exact transform keys (98.6%; Wilson 95% interval 92.5–99.8%). Sigma 8 yields 284/288 (98.6%; 96.5–99.5%), and sigma 12 yields 273/288 (94.8%; 91.6–96.8%). **No wrong canonical key was returned.** The 20 positive canonical-key misses are not all refusals: graph replay identifies eight alternate-generator outcomes and twelve exact-identity outcomes after perception. Intervals for noisy rows are draw-level and conditional on these repeated shape/operator cases; they do not represent 288 independent shape families.

| Operator | Clean exact | Sigma 8 exact | Sigma 12 exact | Wrong keys across all arms |
|---|---:|---:|---:|---:|
| Rotate 90° | 12/12 | 48/48 | 47/48 | 0 |
| Rotate 180° | 11/12 | 44/48 | 42/48 | 0 |
| Rotate 270° | 12/12 | 48/48 | 45/48 | 0 |
| Reflect columns | 12/12 | 48/48 | 47/48 | 0 |
| Reflect rows | 12/12 | 48/48 | 47/48 | 0 |
| Recolour 9→8 | 12/12 | 48/48 | 45/48 | 0 |

The one clean canonical-key miss is repeatable: held-out shape `H06_C` under 180° rotation returns `None` from the task adapter on the clean image and all four sigma-8 and four sigma-12 draws. This is **not** an engine-level refusal. A graph-level replay sets `Observation.status=recognized_transformed` and selects the held `cycle4` generator at `k=1`; the adapter returns `None` because it has no `cycle4` to canonical-key mapping. Independent coordinate arithmetic confirms this is a valid alternate explanation for this particular case: adding one to each row modulo four maps the six H06_C cells exactly to the captured 180° target. Thus the shape/operator pair does not identify the intended `rot90:2` label under the current generator vocabulary. Graph replay shows four sigma-8 misses and three sigma-12 misses use this alternate generator; the other twelve sigma-12 positive misses are graph-level exact `recognized` outcomes after perception. Other H06_C transforms yield adapter keys. The counts and row-level replay are in the [graph replay results](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_GRAPH_REPLAY_RESULTS_20260929.md).

## Negative controls and integrity

Each shape also had a target with one extra adjacent relation. All 12 clean controls and all 48 noisy controls at each sigma returned no canonical key; there were zero adapter-level false acceptances. A source-locked graph replay shows all 108 controls reached `status=minted` with no transform edge. A side-effect audit over the 12 distinct perceived control pairs confirms each creates one `CapabilityAxis` in a fresh graph while `codebook_epoch` stays unchanged. The controls therefore test routing to novelty acquisition rather than graph refusal. See the [graph replay results](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_GRAPH_REPLAY_RESULTS_20260929.md) and [mint side-effect results](SUBSTRATE_HELDOUT_POLYOMINO_V1_NEGATIVE_MINT_SIDE_EFFECT_RESULTS_20260929.md).

All 84 groups and 756 recognition observations are present. The analyzer independently verifies connectivity, distinct D4 orbits, exclusion from the current six-shape corpus, all positive transformation targets, negative extra-cell construction, seed schedule, clean perception recovery, and seen-cell/signature correspondence. Pre-run, post-run, and live source/build/input locks match, and the native extension is fresh. The worker took 56.0 s wall, 55.4 s process CPU, and 111,996 KiB peak RSS. Per-observation timing is descriptive for this one host and warm process.

## Interpretation and next gate

The held basis transfers well through the task adapter for the sampled new shape orbits at clean and sigma-8 settings; at sigma 12, graph replay attributes the extra adapter misses to exact identity after perception. The exact-key score conflates engine recognition with adapter label coverage and does not account for multiple held generators that produce the same target on a particular shape. The H06_C/180° case is an observed alias: the graph recognizes it through `cycle4`, while the adapter cannot express that label. The extra-cell controls route to minting rather than refusal. The result does not establish arbitrary shape transfer, general negative discrimination, confidence calibration, acquisition quality, or natural-task prevalence. The next gate should measure equivalence-aware transform outcomes and mutation/persistence costs under one-off perceptual errors separately from true structural novelty.

The graph-level replay and independent equivalence check are documented in the [H06_C/180° alias audit](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_H06C_ALIAS_AUDIT_20260929.md) and [full graph replay results](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_GRAPH_REPLAY_RESULTS_20260929.md).

Artifacts: [preregistration](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_PREREG_20260929.md), [runner](../../../evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_heldout_polyomino_transform_transfer_v1.py), [execution lock](../../../evaluation/substrate_capability/heldout_polyomino_transform_transfer_v1_lock_20260929.json), [raw capture](../../../evaluation/reports/heldout_polyomino_transform_transfer_v1/capture.json), [independent analysis](../../../evaluation/reports/heldout_polyomino_transform_transfer_v1_independent_analysis.json).
