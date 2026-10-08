# Full-seed GenMint held-out transfer preregistration

**Lock date:** 2026-09-26, before capture. **Question:** when the production `shape_decode_loop` acquires a linear generator from training relations, does it reuse that generator to recognize a new held-out base pattern, and how do residual shifts alter held-out behavior?

Use the same known matrix, eight points, predicate layouts, six-row training split, and perturbation conditions as [the direct held-out relation protocol](SUBSTRATE_GENINFER_HELDOUT_RELATION_PREREG_20260926.md). Each fresh full-seed substrate first receives only the six training base rows and a training Observation. Run the production closure path. Then add the two held-out base rows as a new `ShapeSignature` and present the corresponding clean or uniform-shift transformed two-row observation. Cross 3 layouts × 3 training conditions × 2 held-out conditions × 2 induction arms (`gen_infer_enabled` false/true) × 5 repeats: 180 independent sequences.

Capture both stages' status, residual, Transform nodes, generator graph data, CapabilityAxis count, graph size, closure wall time, and closure report. Independently score the held-out `Transform` by applying its referenced graph-resident generator to the held-out base rows and then applying its returned residual transforms. Exact held-out recognition requires status `recognized_transformed`, the expected minted generator matrix `[1,1,0,2]` in the enabling arm, and exact predicted-row equality. The paired disabled arm is a frozen-acquisition baseline. Clean-train/clean-heldout with induction enabled is the positive gate; other cells are reported without directional pass assumptions.

This is an authored 2-D family through full-seed rule closure, not natural-task capability evidence. It tests staged held-out base acquisition after the first closure; generator minting and held-out scoring remain distinct. Five repeats measure deterministic stability only.

Reproduction: `PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_heldout_transfer_probe_v1.py` and `python3 scripts/analyze_genmint_heldout_transfer_probe_v1.py`.
