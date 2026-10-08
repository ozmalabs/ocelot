# Held-out polyomino transfer v1: graph replay diagnostic

**Date:** 2026-09-29. **Type:** post-hoc descriptive audit of the already sealed v1 capture; no new inferential claim or decision-rule change.

## Question

Among the 756 v1 observations, what graph-level `Observation` status and selected transform does the current native rule loop produce for each exact pair of perceived signatures? How do those outcomes relate to the task adapter's saved canonical key, especially for the 128 adapter-level key misses and the 108 added-cell controls?

## Method and limits

Replay the exact saved `seen_signatures` from the v1 capture, bypassing rendering, pixel recovery, and noise generation. Run each distinct base/goal signature pair once through a fresh graph/native rule loop and map the recorded graph result back to every matching observation. Preserve the original adapter key beside graph status, selected `has_transform` attributes, latent-dimension attributes, and the `dim_infer` result. Lock the v1 raw capture, protocol, runner, Python modules, seed, native extension, and native build metadata before execution; require the same lock after execution.

This replay describes the current local implementation and only the input pairs in the prior capture. It is post hoc and descriptive, not a preregistered estimate of deployment performance. A graph status of `recognized_transformed` records the engine's classification; by itself it does not establish that the selected generator is semantically correct. The H06_C coordinate alias is independently verified in the companion audit. Other generator/target equivalences and all negative-control graph outputs require separate semantic checking before correctness claims.

## Outcomes to report

Report complete counts for (a) graph status × adapter key presence, (b) selected generator on adapter misses, (c) added-cell controls by graph status and adapter output, and (d) deduplicated signature pairs versus observation count. Retain row-level graph outputs and original task labels. Do not modify source, adapter, or winner selection as part of this diagnostic.

## Reproduction

```sh
python3 evaluation/substrate_capability/diagnose_heldout_polyomino_transform_transfer_v1.py --lock
python3 evaluation/substrate_capability/diagnose_heldout_polyomino_transform_transfer_v1.py
```

Outputs are retained under `evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay/`.
