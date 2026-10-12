# Thoughtexperiment concurrent receipt adoption v1 — results

**Result:** all preregistered gates pass (9/9 gates).

## Outcome

Three fresh workers executed 30 races and 90 receipt submissions. Three independently forked branches created nonempty attribute-change receipts from the same base revision in every race. Barrier-synchronized threads submitted the receipts concurrently. The guarded primary accepted exactly one receipt and rejected two as stale in every race; the winning receipt varied freely. The complete final graph matched an independent oracle containing exactly the winner's write, so rejected branch values did not leak into primary state.

Race wall time from barrier setup through all submissions had a median of 0.950 ms (range 0.591–3.728 ms). This includes thread scheduling and is descriptive only.

## Interpretation and limits

This demonstrates strict single-winner stale-base rejection and atomic graph publication for concurrent same-revision receipt calls through the Python/Rust API. It does not demonstrate parallel native execution under the Python GIL, merge semantics for disjoint receipts, fairness, production throughput, or protection of state outside the tracked revision contract. A losing branch must be rerun or explicitly regrounded against a fresh primary revision before another adoption attempt.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CONCURRENT_RECEIPT_ADOPTION_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_concurrent_receipt_adoption_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_concurrent_receipt_adoption_v1_raw_20261001.json)
