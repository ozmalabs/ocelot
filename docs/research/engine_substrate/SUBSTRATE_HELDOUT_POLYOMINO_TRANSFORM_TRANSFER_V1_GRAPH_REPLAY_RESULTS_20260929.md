# Held-out polyomino transfer v1 graph replay results

**Run:** 2026-09-29 post-hoc descriptive replay of the sealed 756-observation v1 capture. **All 85 distinct perceived-signature pairs were replayed and mapped back to all 756 observations; source and raw-input locks matched before and after.**

## Graph outcomes and adapter outcomes

The task adapter returned a canonical key for 628/648 positive observations. The graph-level view explains all 20 positive adapter misses:

| Arm | Positive observations | `recognized_transformed` | `recognized` (identity) | Adapter key returned | Alias via `cycle4`, no key |
|---|---:|---:|---:|---:|---:|
| Clean | 72 | 72 | 0 | 71 | 1 |
| Sigma 8 | 288 | 288 | 0 | 284 | 4 |
| Sigma 12 | 288 | 276 | 12 | 273 | 3 |

The clean and sigma-8 `H06_C`/180° rows, plus three sigma-12 repeats, are `recognized_transformed` through `cycle4`; the other sigma-12 alias repeat is `recognized` as exact identity after perception. Eleven other sigma-12 positive misses are also `recognized` as identity. The adapter's `None` therefore combines (a) a valid but unsupported alternate generator label and (b) inputs whose perceived goal became exactly the held base. These are not engine refusals. The exact counts are in the [analysis](../../../evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay_analysis.json), with row-level records in the [graph replay capture](../../../evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay/graph_replay.json).

All 108 added-cell controls (12 clean, 48 at sigma 8, 48 at sigma 12) have `status=minted`, no `has_transform`, and no adapter key. A dedicated source-locked side-effect audit finds 12 distinct perceived control pairs, each repeated nine times; replaying each once against a fresh graph creates exactly one `CapabilityAxis` linked by `minted`, with `source=concern_induction`. The Agent `codebook_epoch` remains 0.0 in all 12 cases. These controls were rejected as known transform labels but routed into graph mutation; they were not graph refusals. This is consistent with treating an extra-cell shape as novel, but it means these controls cannot support a general “negative refusal” or “no false mint” claim. The epoch result also distinguishes this low-level axis creation from Python-side `grow_part_library` codebook growth. The shared-graph recurrence and downstream consequences remain unmeasured ([side-effect results](SUBSTRATE_HELDOUT_POLYOMINO_V1_NEGATIVE_MINT_SIDE_EFFECT_RESULTS_20260929.md)).

## Interpretation and measurement correction

The original exact-key rates (71/72, 284/288, 273/288) remain correct at the task-adapter boundary, as does the observation that the adapter returned no wrong canonical key. They do not equal graph-level recognition rates. On positive observations, the graph classified 636 as `recognized_transformed`, 12 as exact `recognized`, and none as refused or minted. On the 108 added-cell controls it selected novelty minting. The `H06_C`/180° case is a genuine operator alias: both the expected half-turn and the selected `cycle4` step produce the captured target exactly; see the [alias audit](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_H06C_ALIAS_AUDIT_20260929.md).

The substantive next question now includes the acquisition cost of perception errors: under one-off noise and deliberate structural novelty, do minted axes persist or recur, and does later exact/transform behavior change? Preregister paired one-off-noise and true-novelty controls with graph mutation snapshots, codebook/epoch deltas, duplicate suppression in a shared graph, later replay, and rollback/recovery. Keep adapter compatibility, graph status, transform-equivalence, and mint behavior as separate outcomes.

## Reproduction and boundaries

Replay protocol: [diagnostic specification](SUBSTRATE_HELDOUT_POLYOMINO_TRANSFORM_TRANSFER_V1_GRAPH_REPLAY_DIAGNOSTIC_20260929.md). Runner: [graph replay runner](../../../evaluation/substrate_capability/diagnose_heldout_polyomino_transform_transfer_v1.py). Cross-tab analyzer: [analyzer](../../../evaluation/substrate_capability/analyze_heldout_polyomino_transform_transfer_v1_graph_replay.py). The replay uses saved perceived signatures, not regenerated pixel noise. It is a descriptive audit of this captured distribution. It does not establish correctness of every selected generator, natural prevalence of aliases, or the persistence and downstream effect of the 108 mint decisions.
