# Thoughtexperiment deletion commit v1 — results

**Date:** 2026-10-01  
**Status:** bounded mixed-residual mechanism probe; all 20 checks pass in five fresh workers.

The mutation receipt now includes exact before-images for removed nodes (ID, type, attributes) and removed edges (endpoints, edge type, attributes). The imagination layer turns those records into pending `node_removed` and `edge_removed` conclusions, removes cascade-edge duplicates when a node deletion already covers them, regrounds against the current primary graph, and offers the surviving proposals to the existing commitment gate. The default gate refuses the fixture's deletions; an explicit reviewer approval allows the edge and node removals.

The source-locked runner uses five fresh worker processes. All 20 checks pass in each worker. The approved batch combines a node attribute change, new node and edge, explicit edge removal, and node removal with a cascading edge removal. Added-node IDs are remapped around live trace/commitment nodes. Other checks verify isolation during imagination, default refusal, stale node/edge rejection without any of the other batch writes leaking through, an intervening writer rejected by the expected-revision check, and injected late before-image corruption rejected without applying any part of the mixed batch.

Representable node/edge additions, changes, and removals now share the native expected-revision graph-delta transaction: the primary revision is checked under the native lock, before-images are validated against staged graph/interner copies, and the staged graph is published only after validation succeeds. The gate runs before the transaction and remains an explicit authorization step. The result reports authorization (`gate.allowed`) separately from application (`writeback.applied`): an authorized batch can still be rejected if its revision or before-images conflict. The probe covers one constructed mixed batch; protected-operation policy integration, native deletion-hook parity, attributes containing detached identity references, all effect combinations, transaction-level property tests, and natural-task proposal usefulness remain open. The lower-level graph-delta API itself still has no commitment-gate semantics and must not be treated as an authorization surface. The prior full-graph incident-edge scan has since been replaced by an O(degree) native accessor; see the separate [incident-edge results](THOUGHTEXPERIMENT_INCIDENT_EDGE_REGROUND_V1_RESULTS_20261001.md). Full reground latency remains unmeasured.

## Artifacts

- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_deletion_commit_v1.py)
- [Raw five-worker capture](../../../evaluation/reports/thoughtexperiment_deletion_commit_v1.json)
- [Related residual adoption results](THOUGHTEXPERIMENT_RESIDUAL_ADOPTION_V1_RESULTS_20261001.md)
- [Epistemic commit results](THOUGHTEXPERIMENT_EPISTEMIC_COMMIT_V1_RESULTS_20261001.md)
