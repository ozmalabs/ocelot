# Adequacy receipt persistence/replay v1.1 amendment

The first source-locked capture successfully persisted the candidate and loaded
it in a separate process, but replaying the same accepted receipt created a
second live `ShapeSignature` with identical attributes. The seed file remained
deduplicated and the codebook epoch did not change, so the original live-state
idempotence gate correctly failed in all three reader processes. The capture is
preserved as [`initial diagnostic`](../../../evaluation/reports/substrate_adequacy_receipt_persistence_v1_initial_diagnostic_20261002.json)
and is not treated as a passing result.

The generic `teach()` facility now searches the requested node type for an
exact attribute match and reuses its NodeID before adding a live node. The
existing persistence path still runs, so a held item can still be written to
disk if needed. The preregistered expectations and workload are unchanged;
the implementation change is included in the active-source lock and the full
writer/reader process panel is rerun. This change makes the documented
`teach()` idempotency contract true for live graph state as well as seed files.
