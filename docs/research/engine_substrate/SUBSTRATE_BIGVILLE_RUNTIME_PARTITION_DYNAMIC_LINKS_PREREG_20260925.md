# Bigville runtime-partition dynamic-link replay preregistration

## Question

Do caller-notified event settlement and full round-robin closure both reach full-graph fixed points on the authored Bigville CAN workload when cross-frame links are repeatedly inserted, removed, and reweighted after runtime partitions have been derived?

## Frozen design

- Use the 100 residents from `bigville_cast100.json`, the `can_native_update_3state` rule, and the v3.1 builder that derives 100 five-Concept Microtheory partitions from live within-resident `causal_influence` adjacency before any benchmark links are added.
- Three deterministic link topologies: ring (100 pairs), star (99 pairs), and a connected random sparse graph (100 pairs) generated from three fixed seeds. Each link is a symmetric pair between the endpoint residents' `world_safe` Concepts, initially weight 0.2.
- Three fresh-process replicates per topology and policy (`full`, `event`, `omit_evidence_notification`): 27 workers. Full uses repeated round-robin scoped closure. Event uses the v3.1 Python dependency queue rebuilt from the current directed graph and receives explicit dirty-frame seeds for edge endpoints or input-mutated residents. The omission arm skips the evidence-update frame seeds at one checkpoint only.
- Sequence: settle the original partitioned graph; insert the topology's links; apply authored scenario evidence once to resident positions 0,10,…,90; remove one third of injected pairs; replace the remaining pair weights from 0.2 to 0.35; reinsert removed pairs at 0.35; remove all injected links. At each checkpoint update cross-edge lists and independent equation weights before settlement.
- Require all full/event checkpoints to complete and have independently recomputed zero residual under the current full graph. Compare exact states separately because schedule order may select another fixed point. The omission control must have positive full-graph residual after the evidence update.
- Record dynamic links, endpoint frames, runtime node-to-frame mapping, edge/weight projections, state/field snapshots, residuals, queue/round-robin turns, candidate/Term counters, mutation/settlement time, and native/build provenance.
- Lock runner, protocol, base replay, cast, seed, world builder, and Rust scheduler/binding sources before execution.

## Claim boundary

This tests a project-authored 100-resident workload whose partitions are derived from runtime membership and internal causal edges, with benchmark-injected cross-frame links and caller-provided dirty-frame seeds. It does not measure native effect-to-frame notifications, automatic partition maintenance, natural cross-resident link prevalence, or production GALS. A passing event arm is evidence for this explicitly updated dependency queue only.
