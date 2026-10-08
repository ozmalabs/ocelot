# Held-out polyomino v1 negative-control mint side-effect audit

**Date:** 2026-09-29. **Type:** post-hoc descriptive audit of the 12 distinct perceived added-cell control pairs in the sealed v1 capture.

## Question

When each distinct added-cell control is decoded once against a fresh held codebook, does graph status `minted` correspond to an actual new `CapabilityAxis` and `minted` edge, and what codebook epoch change accompanies it?

## Method

Read each negative control's exact saved base and goal signatures from the source-locked v1 capture. Verify that the 108 rows reduce to 12 distinct signature pairs, each occurring nine times. For each unique pair, boot a fresh graph, snapshot relevant node counts and the Agent's `codebook_epoch`, add one Observation, run the native rules once to fixpoint, and record final status, transform/DimInfer outcomes, minted-edge targets, axis attributes, counts, and epoch. Lock the protocol, runner, raw capture, Python/native source and binary inputs before execution and require an identical post-run lock.

This is a descriptive side-effect audit of the existing control distribution. It does not claim that the added-cell shapes are undesirable concepts to learn, nor does it measure recurrence handling in a shared graph, downstream reuse, rollback, or noise-induced mint frequency on a broader distribution.

## Reproduction

```sh
python3 evaluation/substrate_capability/audit_heldout_polyomino_v1_negative_mint_side_effects.py --lock
python3 evaluation/substrate_capability/audit_heldout_polyomino_v1_negative_mint_side_effects.py
```

Capture: `evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay/negative_mint_side_effects.json`.
