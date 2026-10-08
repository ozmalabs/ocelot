# Thoughtexperiment A8 proposal bridge v1.1 — censored source-attribution result

**Date:** 2026-10-02  
**Status:** Order-stage gate failed; held-out scoring was not run.

## Frozen artifacts

- Protocol: `THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_PREREG_20261002.md`
- Amendment: `THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_1_AMENDMENT_20261002.md`
- Runner and analyzer: `evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_1.py` and `evaluation/substrate_capability/analyze_thoughtexperiment_a8_proposal_bridge_v1_1.py`
- Lock: `evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_1_lock_20261002.json`
- Frozen order capture: `evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_1_orders_20261002.json`

The lock covered 33 source entries plus the loaded native binary. Four workers completed with stable source fingerprints. Each produced the expected `flip_comparison` proposal targeting `hop_descend_gradient`, and the target remained unchanged during proposal construction. However, every prompted and no-cue call reported `served_by: python`. The proposal is therefore not attributable to the graph composer. The runner's pre-scoring gate rejected the capture; no held-out candidate scores were collected.

The v1.1 code change fixed the initial multi-rule seed-loader exception: `_ensure_graph_composer_seed` now accepts uniquely named mint, judge, and adopt rules with clause parity checks. Direct runtime probing confirms the graph seed can load and its individual judge meta-rule can fire. Further tracing isolated why the full mint-plus-judge route falls back: after a graph mint fires, native active-rule export changes the composer rule effects into a normalized wire shape (tuple wrappers and omitted container discriminants). The new strict parity check compares this representation directly with the source manifest and rejects the equivalent active judge rule before its graph dispatch. This is a parity-adapter defect, not evidence that held-out proposal scoring failed. v1.1 remains censored because the source-attribution and no-cue gates failed. The v1.2 amendment permits canonical clause comparison only if it preserves source-significant distinctions and adds negative parity controls; the held-out gate remains closed until a fresh order capture passes.

## Interpretation

This result establishes that the proposal utility demonstrated by the host-candidate panel cannot yet be credited to the graph-authored A8 route. It measures a working Python fallback and target preservation, not graph-authored proposal generation, held-out proposal utility, autonomous improvement, or self-improvement. The v1 source-attribution failure and this v1.1 integration failure remain separate, source-locked records.
