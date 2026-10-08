# Active-rule node-deletion invalidation v1 preregistration

**Question:** after a fixed point, does deleting a node refresh a surviving rule whose `Term` reads an incident edge type, in the default dirty mode and with `precise_dirty` enabled? How much matcher/scheduler work does refresh require?

## Fixture and paired conditions

Each fresh worker independently builds two identical graphs. Both have `Root -trigger-> Target` and `Root -watched-> Doomed`. One rule matches `trigger` and sets `Target.watched_count` to `Count(Edges(Root, watched))`. Settle each graph to a fixed point (expected count 1), then remove `Doomed` and settle again. The default arm leaves precise dirty mode off; the second enables it before rule registration. Capture closure reports and native scale-audit counters separately for initial closure and post-delete settlement.

## Gates and interpretation

Require three fresh worker processes, a stable source/native lock, identical starting graphs, exact rule access declaration for `edge:watched`, correct initial fixed points, successful node removal, terminal post-delete reports, independent graph count zero, and per-condition counters. The preregistered behavioral hypothesis is that the default arm may fail to refresh while precise dirty mode does; this is a measured failure outcome, not a runner failure. The analyzer checks source integrity and independently classifies each arm as refreshed or stale. No timing gate is imposed; operation counts and wall time are descriptive.

This isolates one typed `Edges` term and one deletion. It does not establish behavior for all Term variants, more complex rule networks, rule-authored deletion, or natural workload frequency. A default-mode stale value is a correctness gap requiring follow-up, not a tractability result.
