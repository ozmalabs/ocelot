# Thoughtexperiment residual adoption v1 results

**Status:** all preregistered gates pass (9/9).

## Result

The native `Substrate.apply_experiment_graph_delta(expected_revision, delta)` now adopts the `conclusions` graph-diff receipt atomically. Across 15 fresh workers at 0, 10k, and 50k unrelated nodes, every accepted receipt produced exact canonical full-primary graph parity against an independent Python application of the delta. The check preserves unrelated primary edges outside the branch's scoped aperture, as well as node identities, node attributes, and edge facts.

All 15 stale-base attempts rejected on the revision mismatch and left the primary graph unchanged. All 15 corrupted before-image attempts rejected before publication and left the graph unchanged. Branch execution itself left primary unchanged in every worker. After closing the downstream mutable-field bypass, the native artifact was rebuilt and the complete 15-worker panel rerun. Source fingerprint is `9ac9777bd64e43e375e05e4046f1e9da9bbe4e39ced0893b7a38725fe2291196`; extension hash is in the raw capture.

Median apply/rejection times were:

| Unrelated nodes | Accepted apply | Stale rejection | Before-image rejection |
|---:|---:|---:|---:|
| 0 | 0.380 ms | 0.164 ms | 0.213 ms |
| 10,000 | 0.791 ms | 0.306 ms | 0.415 ms |
| 50,000 | 1.474 ms | 0.316 ms | 0.472 ms |

The increase in accepted apply cost is consistent with staging a CoW graph/interner and validating the sparse receipt; these three sizes do not establish a complexity law. Rejection cost remains sub-millisecond in this host/fixture because revision and before-image checks stop publication early.

## Receipt dependency and aperture finding

`derived_only` is not necessarily a self-contained adoption receipt: the productive fixture's added `yields` edge references the injected hypothesis node, which `derived_only` omits. The successful adoption therefore uses `conclusions`, which includes both hypothesis and derived structure. Also, the detached branch has an edge aperture: its serialized edge list contains only the visible scoped edges. The exactness oracle accordingly applies the receipt to the complete primary graph and compares canonical full graph facts, rather than comparing the scoped branch serialization with the full primary graph.

## Scope

This validates exact adoption, strict revision rejection, and malformed before-image atomicity for one authored productive-rule family. It does not prove safe concurrent merges, arbitrary external receipt behavior, internal crate mutation discipline, or natural-task usefulness. Public downstream callers cannot directly mutate the semantic stores participating in the revision token; see the [revision-token audit](THOUGHTEXPERIMENT_REVISION_TOKEN_AUDIT_20261001.md). A follow-up now covers edge attributes; assumption and dependency handling is now explicit for the mediated additions/edge-update path; deletion proposals and concurrent/lifecycle ownership remain open.

## Edge-attribute delta follow-up (source-locked, 2026-10-01)

The original graph-diff wire form omitted edge attributes. `graph_diff` now emits complete attributes on added edges and sparse before/after attribute maps for changed edges; `apply_graph_delta` validates changed-attribute before-images and stages edge add/change/remove operations atomically. The sparse Thoughtexperiment mutation journal now retains edge attribute before-images as well, so its conclusions and derived-only receipts can represent attribute edits.

The post-implementation source-locked probe runs five fresh workers. Every worker exercises one changed edge (value replacement, key removal, and key addition), one removed edge, one added edge with attributes, exact adoption, journal round-trip equality for both receipt projections, and a corrupted-before-image rejection with unchanged primary state. All five worker checks pass. This is a mechanism probe on a constructed graph, not evidence that natural tasks produce useful edge-attribute changes. The adoption panel was rerun after the wire-format change; all 9/9 gates pass over 15 workers. The latest apply medians are 0.380/0.791/1.474 ms at 0/10k/50k nodes.

The first panel run after the format change failed one analyzer gate because it incorrectly required the new optional `edges_changed` category to be nonempty in a fixture with no such edits. The gate was corrected to require only the five mutation classes prescribed by that fixture, then the full fresh-worker panel passed. The first run remains in the raw capture history only as a failed exploratory capture; the corrected source-locked rerun overwrote the authoritative capture.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RESIDUAL_ADOPTION_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_residual_adoption_v1.py)
- [Analyzer](../../../scripts/analyze_thoughtexperiment_residual_adoption_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_residual_adoption_v1.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_residual_adoption_v1_analysis.json)
- [Revision-token audit](THOUGHTEXPERIMENT_REVISION_TOKEN_AUDIT_20261001.md)
- Edge-attribute probe: [runner](../../../evaluation/substrate_capability/thoughtexperiment_edge_attr_delta_v1.py), [capture](../../../evaluation/reports/thoughtexperiment_edge_attr_delta_v1.json)
- [Epistemic commit results](THOUGHTEXPERIMENT_EPISTEMIC_COMMIT_V1_RESULTS_20261001.md) and [capture](../../../evaluation/reports/thoughtexperiment_epistemic_commit_v1.json)
