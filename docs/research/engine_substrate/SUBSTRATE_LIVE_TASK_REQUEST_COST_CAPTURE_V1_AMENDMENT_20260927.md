# Live task request-cost capture v1 amendment: concurrent source change

Date: 2026-09-27 local

The first three-worker execution was invalidated before analysis. The initial worker started under the locked source fingerprint, but `substrate/world_adapter.py` changed before that worker's final fingerprint and before later workers started. The raw output therefore failed the preregistered source/native stability gate and was not evidence for request-cost comparisons. The subsequent valid rerun overwrote that raw file; the invalid attempt is identified by its recorded raw SHA-256 `2e841f1164fe509eb543e4742dca89012d97f0c36cd19dcf14e20b322ccae377`, but its worker payload is no longer retained. Do not use that invalid run’s values.

The updated `world_adapter.py` contents are treated as the current worktree state. The capture will be re-locked against the current state and rerun only after the driver confirms a stable fingerprint. No source change is inferred to have been caused by this capture; the mismatch is simply disclosed. This amendment does not change the task, counters, gates, or claim boundary.
