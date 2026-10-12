# Route panel J graph-repeat diagnostic v1

Date: 2026-09-27

The complete-runtime route panel v1.2 reproduces the same route/reply for all three `what is organisation?` workers but reports two order-sensitive semantic graph digests. This diagnostic determines whether that discrepancy is only node/edge enumeration order or a true graph-state difference.

Run three new full boots of the same locked v1.2 snapshot with the same question. Hash full node records after removing the same volatile `SystemModel.ts` and `runtime_s` fields, sort node records by type/id, sort typed edges by source/type/target, and compare both canonical and original digests. Preserve node and edge fingerprints per worker so any changed IDs/types/attrs are locatable. No graph intervention or production edit is made.

Pass conditions: unique worker PIDs, stable full source/slab/script locks, identical route/reply/comprehension across workers, and complete canonical fingerprints. If canonical digests agree, classify the v1.2 discrepancy as enumeration-order sensitivity. If they differ, report exact changed node/edge fingerprints and leave graph determinism unresolved. This addresses only stimulus J.
