# Scoped NetCollapse fallback — 2026-09-26

## Result

The locked 18-worker experiment passed all ten independent gates across 1/2/4 reflex-net observations, two repeats, and `full`, `scoped_only`, and `scoped_fallback` arms. Scoped arms consistently returned `deferred_effects_pending=true` and hit the one-step progress budget. Full and fallback runs settled, and a terminal closure was zero-progress.

For each net, the deferred update changed graph-resident `WeightTensor.data` from zero readout to `W2=[[0.05]]`, `b2=[0.05]`, and recorded surprise. The fallback projection exactly matched ordinary full closure for all 6 paired cells. The scoped-only control demonstrates the hazard: it marks the first observation consumed while leaving its net weights unchanged because the queued collapse was not drained inside the one-step scoped call; remaining observations are still pending at larger sizes.

## Interpretation and limits

This confirms that the same explicit caller fallback policy works for a second and structurally different deferred effect family: `NetCollapse` writes numerical model state, rather than `TrackIdentity` writing identity attributes. It is a mechanism result on a deliberately simple single-ReLU net and at most four observations. It does not establish learning efficacy, arbitrary network behavior, interactions among deferred queues, fallback cost, or automatic notification delivery. The API's incomplete-notification contract remains unchanged.

## Reproducibility

- Protocol: [`SUBSTRATE_SCOPED_NET_COLLAPSE_FALLBACK_PREREG_20260926.md`](SUBSTRATE_SCOPED_NET_COLLAPSE_FALLBACK_PREREG_20260926.md)
- Runner: [`substrate_scoped_net_collapse_fallback_v1.py`](../../../scripts/substrate_scoped_net_collapse_fallback_v1.py)
- Independent analyzer: [`analyze_substrate_scoped_net_collapse_fallback_v1.py`](../../../scripts/analyze_substrate_scoped_net_collapse_fallback_v1.py)
- Source/build lock: [`scoped_net_collapse_fallback_lock_20260926.json`](../../../evaluation/substrate_capability/scoped_net_collapse_fallback_lock_20260926.json)
- Raw capture: [`substrate_scoped_net_collapse_fallback_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_net_collapse_fallback_v1_20260926.json)
- Independent analysis: [`substrate_scoped_net_collapse_fallback_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_scoped_net_collapse_fallback_v1_analysis_20260926.json)

The runner, analyzer, protocol, native rewrite/substrate/net-forward code, PyO3 binding, and native build manifest hashes all match the lock.
