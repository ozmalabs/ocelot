# Unified five-family scoped/fallback queue work v1.1 amendment

Date: 2026-10-01

## Reason for amendment

The initial v1 run failed the preregistered multi-binding equivalence gates. Source inspection traced the discrepancy to the scoped non-batch cold path in `rewrite.rs`: it applied the first progressing binding and broke, while the live `Substrate::attempt_one_rule` path snapshots and folds every distinct binding. The initial analyzer summary was 228/300 checks, with all failures concentrated at `M=4` and `M=16`; a representative `R=1,M=4` final NetCollapse weight was 0.05 scoped-plus-fallback versus 0.17195 in full closure.

During the post-fix run, the runner reused its v1 raw-output path, replacing the initial raw worker capture and analysis JSON. That was an artifact-management error. The initial outcome was observed directly in the prior analyzer output and graph comparison, but its full raw capture is no longer available for independent replay. The initial lock fingerprint was emitted in the execution record but likewise was not retained under a separate artifact name. This limitation is disclosed; the initial run is not treated as independently auditable raw evidence.

## Source change

The scoped non-batch path now applies every distinct binding from its pre-mutation snapshot, in order, while undoing no-op probes. It uses canonical full-binding deduplication and passes no graph-dependent evaluation cache into effect application after matching. This follows the binding-fold structure of `Substrate::attempt_one_rule`; it does not alter the global path. The preregistered semantic expectations were retained.

## Confirmatory v1.1 capture

After rebuilding the native engine, the exact 27-worker factorial was rerun. All 300/300 checks pass, including full versus scoped-plus-fallback graph equality, scoped pending status, all five queue item counts, fallback drains, and operation-trace/counter reconciliation. A distinct copy of the post-fix lock, raw workers, and analysis is preserved as:

- `evaluation/substrate_capability/all_queue_scoped_fallback_v1_1_lock_20261001.json`
- `evaluation/reports/all_queue_scoped_fallback_v1_1_workers_20261001.json`
- `evaluation/reports/all_queue_scoped_fallback_v1_1_analysis_20261001.json`

The fingerprints in the capture lock the new `rewrite.rs` source and rebuilt native extension. The preserved raw SHA-256 is `33268ef96146d48ab1ba6a2c2f615999e4020b62c3e36a9071d5cd6743508c1b`; preserved analysis SHA-256 is `1cb2ddf616315d8ae3c6ff5c822e5676a4ef40e17ddf4e690cd3624572704d6e`.

## Claim boundary

The fix resolves the measured first-binding discrepancy on this workload. It does not validate projection-key deduplication, write-dependent later bindings, rule-to-rule scheduling equivalence, or arbitrary frame scopes. Those remain explicit parity gates before treating scoped closure as generally interchangeable with full closure.
