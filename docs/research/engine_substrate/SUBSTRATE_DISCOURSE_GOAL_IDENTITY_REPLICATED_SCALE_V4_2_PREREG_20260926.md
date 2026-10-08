# Replicated same-addressee Goal identity scale v4.2

**Question:** are the v4.1 operation-count and caller-queue overhead observations repeatable across fresh processes, and what current-RSS growth accompanies workload construction/settlement?

## Frozen workload and arms

Use the exact v4.1 same-addressee workload at N=16/32/64 and the same five arms: temporal-only full, recipient-guarded full, explicit-link full, explicit-link owner queue, and explicit-link omitted-wakeup with final full recovery. Run three fresh-process replicates per size/arm (45 workers), in deterministic shuffled order. Preserve v4.1 rule variants, event order, partition, task oracle, scope queue, progress cap, and no-deferred contract. No production rule changes.

All existing semantic gates remain per replicate: explicit full and owner queue match every expected goal transition; owner queue matches the full graph digest at every event checkpoint; temporal and recipient-only controls fail the task oracle; every result notifies its origin frame; omitted notifications leave receipts stale and full recovery restores parity; reports have no cap/deferred exits. Record candidate and Term counts, progress, scoped turns, wall/CPU, frame setup, unique PIDs, and peak RSS.

## Memory observation

Record current resident set from `/proc/self/status` after Python/runtime imports, after rules/state/owner frames are initialized but before event workload construction, and after final closure. Report within-process deltas and `ru_maxrss` separately. This is process RSS, not allocator-level object attribution; no allocation completeness claim follows.

## Analysis

Report per-replicate values plus medians and ranges for operation counts, wall/CPU time, RSS baselines/deltas, and owner/full ratios. Interpret semantic parity and cost separately. The size points are 16/32/64 on one generated fixture; they remain unsuitable for natural-workload or formal complexity claims.

## Limits

This is replication of one generated identity-link family, not an independent task family or production producer integration. Do not change code or gates after viewing outcomes except under a dated amendment preserving the failed capture.
