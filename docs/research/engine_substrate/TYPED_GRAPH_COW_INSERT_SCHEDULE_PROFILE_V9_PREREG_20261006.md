# TypedGraph COW insert schedule profile v9 preregistration

Date: 2026-10-06

## Question

Does the v7 small-graph insert-plus-query timing anomaly reproduce when its
exact ordered mutation schedule is rerun and `insert_node` is separately
timed from the post-insert indexed lookup?

## Workload

The v9 worker is a source copy of the v7 graph mutation worker with nested
timers around the insert operation and the exact lookup. It retains v7's
fixture, the 21-repeat per-process set-attribute, insert, delete, retype order,
alternating shared/eager arm order, semantic/index/order checks, sibling
isolation checks, and compaction/NodeID-reuse control. Run N=7,164 and 50,771,
three fresh processes per cell, and 64/128/256/512 shard configurations in
rotated order.

## Gates and analysis

All existing v7 semantic and isolation gates must pass. For the insert row,
report fork, outer insert-plus-query time, nested `insert_node` time, and
nested exact lookup time separately for shared and eager branches. Compare
three fresh-process medians with v7 and v8, keeping the workload/schedule
difference explicit. This is a diagnostic replication, not a production
default decision or an end-to-end Substrate result.
