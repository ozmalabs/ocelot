# Scheduler checkpoint transfer v5 preregistration

V5 repeats the v4 incremental-deletion and predicate-retraction transfer with checkpoint schema V4, which records EvalCache entry counts, reachable-cache configuration, and retained-cache telemetry. Empty caches and their telemetry must restore exactly. The current implementation intentionally rejects a checkpoint with non-empty EvalCache maps rather than silently restoring a different state. The analyzer reports occupancy for every case; any non-empty state fails the transfer gate and becomes evidence for implementing full cache payload serialization.

The panel otherwise retains the two independent CAN and retinal fixtures, four states, deleted matched-edge control under `incremental_match`, dirty-node control under predicate retraction, and exact graph/rule/scheduler/counter/post-state comparisons. This evaluates two small synthetic families only.
