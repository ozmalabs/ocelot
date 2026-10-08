# Bigville dynamic boundary profile — secondary structural analysis

## Scope and provenance

This is a secondary, post-hoc structural analysis of the locked 27-worker Bigville runtime-partition dynamic-link capture. It does not rerun native closure or change the source experiment. The analyzer validates the raw lock digest and embedded locked-input set, confirms all 27 workers have 100 runtime-derived five-Concept owner frames, then independently reconstructs each frame's cross-boundary Concept set and the frame-quotient interaction graph from saved edge weights at all seven checkpoints (63 event-arm profiles). Every derived directed crossing-edge count agrees with the source record. Profiles are identical across full, event, and omitted-notification arms.

The recorded frame assignment is the live `has_concept` owner mapping derived at baseline. Cross-resident links were then injected while that owner partition stayed fixed. Thus these are dynamic boundary profiles for an owner-based partition, not a recomputation of connected components after every mutation. The analyzer reports a min-fill treewidth **upper bound** for the 100-vertex quotient graph; it does not report exact treewidth of the 500-Concept graph.

## Boundary and fan-out results

At the initial baseline, all three topologies have no crossing links. Insertion yields the following per-checkpoint structure (replicate ranges are shown where random topology varies):

| Injected topology | Undirected resident links | Active owner frames | Boundary Concepts | Max cross-link incidences on one frame | Frame-quotient width upper bound |
|---|---:|---:|---:|---:|---:|
| Ring | 100 | 100 | 100 | 2 | 2 |
| Star | 99 | 100 | 100 | 99 | 1 |
| Random connected | 100 | 100 | 100 | 5–9 | 2 |

Every active frame exposes exactly one boundary Concept because all injected links use the resident's `world_safe` Concept. This shows why a boundary-size statistic alone is insufficient: the star has one exposed Concept per frame and quotient width upper bound 1, yet its center frame has 99 crossing-link incidences. Boundary aperture, quotient width, and interface fan-out need separate fields.

Deleting one third of the links reduces the ring to 66 links and 99 active boundary frames (width upper bound 1); the star to 66 links and 67 active frames (maximum incidence 66, width upper bound 1); and random connected graphs to 66 links and 81–84 active frames (maximum incidence 4–6, width upper bound 1). Reweighting leaves boundary structure unchanged. Reinsertion restores the original profile, and removal of all links returns every topology to zero crossing links and zero exposed boundary Concepts. The raw-derived full 63-row profiles retain each frame's boundary size and incidence, not just these summaries.

## Update-cost and execution interpretation

The source runner timed graph-edge changes and its Python fixture arrays separately from settlement, but did not time initial partition construction or recomputation/maintenance of a partition. Across event-arm replicates, the seven recorded edge/evidence mutation blocks sum to a median 20.8 ms for ring, 20.2 ms for star, and 20.7 ms for random connected topology. This includes graph and caller-side array edits; it is not an isolated partition-index cost. These mutation blocks are comparable in scale to the source study's accumulated event-settlement medians (12.0–14.9 ms), so settlement-only savings should not be presented as end-to-end savings without those caller costs. The sample has three replicates and timing is descriptive.

The structural result adds a useful interpretation to the original semantic evidence: a small quotient width bound can coexist with highly skewed fan-out, and dynamic edge changes alter the interface profile even when owner membership is fixed. The original event/full result still establishes exact state and full-graph residual parity for the selected injected-link traces, with omitted notification detected at the evidence-update checkpoint. It does not measure automatic native frame notifications, learned frame discovery, general Bigville task prevalence, or exact runtime complexity.

## Next measurement

A confirmatory C2 run should start timing before graph and partition construction, separately time owner/component discovery and boundary-index creation, then time incremental update and full recomputation of those structures after edge insertion/deletion/reweighting. It should include skewed hubs and disconnected controls, retain boundary-node and fan-out distributions, and compare total partition-aware execution cost with monolithic closure. The existing raw capture does not contain partition-build timing, so this analysis cannot fill that field retrospectively.

## Reproduction artifacts

- [Source runtime results](SUBSTRATE_BIGVILLE_RUNTIME_PARTITION_DYNAMIC_LINKS_RESULTS.md)
- [Source preregistration](SUBSTRATE_BIGVILLE_RUNTIME_PARTITION_DYNAMIC_LINKS_PREREG_20260925.md)
- [Independent structural analyzer](../../../scripts/analyze_bigville_dynamic_boundary_profile_v1.py)
- [Structural profile JSON](../../../evaluation/reports/substrate_bigville_dynamic_boundary_profile_v1_20260926.json)
- [Source raw capture](../../../evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_20260925.json)
- [Source lock](../../../evaluation/substrate_capability/bigville_runtime_partition_dynamic_links_lock_20260925.json)
