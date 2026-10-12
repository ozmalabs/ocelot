# Polyomino concern-key identity comparison v1 preregistration

**Date:** 2026-09-29. **Question:** does replacing predicate-multiset identity with a canonicalized structure identity preserve exact-repeat suppression while separating distinct structures on the same 15-sequence panel?

## Motivation and scope

The preceding locked panel found `minted`→`recognized_duplicate` for five exact repeats and ten distinct D4-orbit shape pairs. Every seven-cell input received the same predicate-derived key. This follow-up compares that production default with a canonical D4 shape key supplied through the existing `induce_concern(..., name_hint=...)` hook. It changes only the deduplication key between paired arms; it does not modify the engine, seed rules, or key-generation behavior used by ordinary callers.

## Frozen paired design

Reuse the exact five six-cell shapes, deterministic appended-cell construction, and 15 two-observation sequences from `SUBSTRATE_POLYOMINO_CONCERN_KEY_RECURRENCE_V1_PREREG_20260929.md`. Run every sequence in two fresh graphs:

1. **Predicate arm:** call `induce_concern` without `name_hint`, using the current sorted-predicate key.
2. **Structure arm:** call it with a deterministic `shape_d4_<sha256>` name hint, where the hash is over the lexicographically minimal normalized coordinate set among the eight D4 transforms of the seven-cell target.

All other source, shape signatures, sequence order, base codebook, and closure calls remain identical. Record signature identity, D4 identity, supplied/returned key, terminal status, mint/dedup/transform edges, axis deltas, codebook epoch, native steps, key-computation time, and per-call wall/CPU time. Each sequence starts from a fresh boot in each arm.

## Primary measures and gates

- Verify 15 sequences × 2 variants × 2 observations = 60 calls, exact input pairing, identical source lock, five exact repeat pairs, ten distinct-shape pairs, one shared predicate key, and five distinct canonical D4 keys.
- Compare second-call duplicate classification and axis delta between arms, stratified by exact-repeat versus distinct-shape sequences.
- Report canonical-key computation and total-call costs separately. Do not treat the `name_hint` arm as a production change or assert semantic benefit beyond this frozen shape family.
- Preserve every row, including status disagreements and failures. No exclusion or key redesign follows from this measurement without a separate review of other `induce_concern` callers.

## Reproduction

```sh
python3 evaluation/substrate_capability/polyomino_concern_key_identity_comparison_v1.py --lock
python3 evaluation/substrate_capability/polyomino_concern_key_identity_comparison_v1.py
python3 evaluation/substrate_capability/analyze_polyomino_concern_key_identity_comparison_v1.py
```
