# High-degree edge lookup replay v1.1 amendment

The first v1 run completed all 12 worker oracles and the semantic mutation probe, but failed its source-stability gate. The parent lock itself was stable. The reused v1 worker fingerprints three additional dependencies that v1's new lock list omitted: `runners/dsl/python/substrate_rs/__init__.py`, `runners/dsl/src/rewrite.rs`, and `runners/dsl/src/scale_audit.rs`. The worker snapshots were stable; the comparison failed because the runner tried to compare a strict subset fingerprint to the superset lock.

The v1 raw capture and lock are retained unchanged as a disclosed failed attempt. V1.1 adds the missing dependency paths to the lock and compares the worker snapshot as a projection of the complete parent lock, requiring every worker-hashed path and binary identity to match. No workload, graph, implementation, oracle, or analysis threshold changes. V1.1 uses distinct lock and raw paths and fresh workers.
