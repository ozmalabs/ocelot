# Held-topic trace semantic-parity v1.1 post-capture provenance audit

Date: 2026-09-28  
Applies to: [v1.1 paired replay](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_RESULTS_20260928.md)

## Input identity

The raw capture and run lock are preserved unchanged. The lock records protocol SHA-256 `e45f7d0b56ecfe47389cb4cac3c541859dc34fa3a06c06ebe359d7eda8d2a8de`, amendment SHA-256 `bea369d7e7eb01225844f67a97a7a52c54fcf1b1b25385c8b3725aa23fe9b0a3`, original analyzer SHA-256 `caf34d3bee554389fb009c61fb58497cde644144a798b3c8614aacedbccae58a`, and commit `8bac3e90b39ca7eca12e88f856a9bc4b350add87`. The current preregistration matches the locked protocol hash. The current amendment does not match the locked amendment hash (current SHA-256 `94fad0b8df4144d6bc64af3d3876ba30fef38ebb00d74654b86185ac80a2cf48`). The isolated snapshot's amendment copy also does not match the locked value. Therefore the exact locked amendment bytes are not presently available alongside the capture; the lock preserves their digest, not their contents. Treat the capture's amendment text as hash-identified but not byte-recoverable from the retained files.

The amendment currently in the workspace contains post-capture explanations about the missing runtime corpus and analyzer correction. Those statements are not themselves part of the hash-identified amendment. This audit separates them from the captured-input record. It does not modify or re-hash the paired raw capture or lock.

## Execution context and interpretation

The recorded invocation was run from `/home/matt/ozmadev/ocelot` with `OZMA_NO_LLM=1`, `OZMA_SEED_PERSIST_DISABLED=1`, and `SUBSTRATE_NATIVE_PACKAGE=/tmp/ocelot-overhead-v3-wheel/substrate_rs`. The lock records Python 3.13.5, platform `Linux-6.8.0-142-generic-x86_64-with-glibc2.39`, native extension/build hashes, the source closure, and the complete `data/` tree digest. The environment variables and working directory are available from the execution record, not serialized as fields in the lock; future capture drivers should record them directly.

The capture remains useful evidence for the recorded source/runtime-data state and fixed workload. Its paired raw output is unchanged, and the separate corrected analyzer remains the source of the 24-check analysis. The amendment-byte discrepancy is a provenance limitation on reconstructing the full preregistration package, not evidence that worker data changed. Future runs should copy every preregistered input into an immutable run bundle before execution and verify those exact bytes after analysis.

## Follow-up controls

1. Add `cwd`, selected environment variables, executable, and native package path to the lock schema.
2. Make the runner stage immutable copies of the protocol, amendment, driver, analyzer, and source/runtime manifests into a run directory before workers start.
3. Validate lock-to-bundle byte equality before analysis; preserve any corrected analyzer as a separately hashed post-capture artifact.
