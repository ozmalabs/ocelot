# Scoped rule snapshot attribution preregistration

**ID:** `SUBSTRATE_SCOPED_RULE_SNAPSHOT_ATTRIBUTION_20260926`  
**Purpose:** separate the cost associated with active-rule cloning from slot scanning and rule-body size in scoped no-match calls. This follows the measured 180–210 ns/active-rule slope in the prior [no-op setup probe](SUBSTRATE_SCOPED_NOOP_SETUP_COST_RESULTS_20260926.md).

## Fixed design

- Current native build and the source/native hashes are captured before measurement; refuse stale builds.
- Six active/tombstone layouts: active rule counts `{64, 256, 512}` crossed with tombstoned slot counts `{0, active_count}`. Tombstones are made by `remove_rule`, retaining the slots.
- Two rule-body shapes: `small` has one absent typed match edge and one harmless `SetAttr` effect; `large` has eight disconnected absent typed match edges and eight `SetAttr` effects. Unique absent edge types ensure zero candidates and effects never execute.
- One two-node Microtheory fixture; one warm-up; 30 timed `run_rules_scoped` calls; five fresh fixtures/repeats per cell; audit off for timing. Randomized cell order within each repeat. Record wall and process CPU nanoseconds, graph/rule-slot state, and audit counters.
- Gates: all calls fixed-point with zero progress; graph unchanged; installed slot count equals active+tombstoned; active count is as specified; candidate and Term counters are zero. Timings are descriptive; no clone-only causal attribution is permitted from this contrast alone.

## Analysis

Report median and p10/p90 latency per call. Contrasts: (a) tombstones versus no tombstones at fixed active count/body size; (b) large versus small body at fixed active/slot count; (c) active-count slope within each layout. If large bodies materially increase slope, clone payload is implicated; if tombstones raise cost, scanning inactive slots is implicated. These are mechanism indicators, not a decomposition into exact instruction costs.

## Decision gate

Use the result to select a prototype: an active-slot index if tombstone count matters; a reusable cloned snapshot if repeated clone payload dominates and mutation invalidation is tractable; otherwise retain the current path and profile matcher dispatch. Any optimization must preserve active order, original slot attribution, tombstone semantics, and rule-mutation visibility, then pass matched scoped/full parity and invalidation tests. This experiment does not establish natural workload scale or frame locality.
