# Thoughtexperiment correction candidate surface v2 — preregistration

**Date:** 2026-10-02  
**Question:** Does the current checkout reproduce the previously captured default self-correction candidate inventory, and how much of that syntactic surface is currently task-shaped?

## Design

Run three fresh Python worker processes against the standard core fixture. Each worker enumerates `_default_candidates` for every active rule and records ordered labels/counts. Before and after enumeration, capture graph state and the active rule export to ensure the inventory operation is read-only. The parent records current source hashes, the loaded native binary hash, host/Python identity, process IDs, and a semantic engine fingerprint. Compare the exact per-rule inventory with v1's raw capture as a historical comparison; v1's source hash is known to differ, so it is not treated as the lock for this run.

The pre-capture lock covers this protocol, runner, independent analyzer, the candidate generator and edit operators, the fixture builder, boot path, engine provenance helper, relevant native source/build manifests, and the loaded native extension. The runner refuses capture if the current checkout differs from that lock or if its raw capture already exists.

## Gates

- Three fresh workers have distinct PIDs and the same active-rule inventory.
- Every worker's graph/rule state is identical before and after candidate enumeration.
- Source fingerprints are stable across workers and match the pre-capture lock.
- The loaded native extension is current according to the engine provenance checker and matches the lock.
- Candidate-family counts sum exactly to the total candidate instances.
- The current per-rule inventory is compared exactly with the v1 raw record, with any differences preserved and reported.
- Report separately: syntactic candidates, task-shaped candidate count, and the task families for which a held-out utility oracle has actually been measured.

This is an inventory audit, not a candidate utility or safety evaluation. It cannot establish that any generic edit is useful. No code or candidate generator change is part of this run.
