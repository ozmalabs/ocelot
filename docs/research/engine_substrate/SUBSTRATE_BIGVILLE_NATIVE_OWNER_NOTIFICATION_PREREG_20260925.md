# Bigville native owner-notification replay preregistration

Protocol amendment v1.1: [omission-arm scope clarification](SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_V1_1_AMENDMENT_20260925.md). It was applied before the locked run and is included in the locked inputs. The harness policy identifier `omit_evidence_notification` suppresses initial seeds for both link insertion and authored evidence.

## Question

Can Microtheory IDs reported by native scoped settlement replace the Python dependency queue's caller-supplied dependent-frame propagation on the authored 100-resident CAN workload, while preserving full closure state and zero full-graph residual after dynamic cross-frame link and evidence changes?

## Frozen design

- Reuse the v3.1 Bigville runtime builder and dynamic-link workload: 100 residents, 100 runtime-derived five-Concept components, one `can_native_update_3state` rule, and ring/star/seeded-random connected cross-resident links.
- Keep full round-robin closure as the reference. Replace only the event arm's dependent-frame computation with `run_rules_scoped_delta_report`: each scoped turn returns touched owner Microtheories, which are mapped to the fixture's runtime component frame IDs and enqueued. Host mutations seed directly affected endpoint/resident frames as in the existing workload.
- Keep the omitted-notification sensitivity arm. It suppresses initial seeds at link insertion and authored evidence; the evidence checkpoint must show positive independently recomputed residual, with link-insertion residual reported separately.
- Run three fresh-process replicates per topology and arm (27 workers), with identical graph construction and mutation sequence: baseline; insert all links; apply evidence at positions 0,10,…,90; delete one third; reweight remaining links; reinsert deleted links; remove all links.
- Record all checkpoints, state/field projections, exact residuals, frame IDs reported, queue turns, candidate/Term counters, mutation and settlement timings, deferred-queue flags, and engine provenance.

## Gates

- Runtime partitions must reconstruct to 100 components of five Concepts before injected links.
- Full and native-event arms must complete every checkpoint, have no scoped deferred queue pending or step-cap exit, reach independent full-graph residual zero, and match exact projected state at every checkpoint.
- The omitted evidence seed must produce positive residual at the evidence checkpoint.
- Every returned Microtheory must map to a known runtime frame; missing/unknown owner IDs fail the worker.
- Report event-queue work and full closure work separately. A passing result supports this authored workload only; it does not establish natural frame locality or general tractability.

## Claim boundary

This measures native owner notification feeding an event queue on one authored workload. Partition construction still comes from the v3.1 runtime graph, and external mutations still seed affected frames from their known endpoints. It does not test framebuffer/net/rule-edit effects, automatic partition rebuilding after ownership changes, or a general GALS scheduler.
