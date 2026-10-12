# Scoped snapshot clone cost preregistration

**ID:** `SUBSTRATE_SCOPED_SNAPSHOT_CLONE_COST_20260926`  
**Purpose:** measure the active-rule snapshot filter/clone/allocation/drop operation directly and compare it with full scoped no-match call cost on the same build and fixtures.

## Locked design

- Use diagnostic method `Substrate::profile_scoped_rule_snapshot`, which repeats the same `enumerate → active filter → (original slot, RewriteRule::clone) collect` used in scoped closure. Its timed interval includes snapshot allocation and destruction, but excludes matcher execution, frame ownership discovery, graph writes, and Python per-iteration overhead.
- Cross active rules `{64,256,512}`, match edges/rule `{1,8}`, and effects/rule `{1,8}`; unique absent edge types keep every rule from matching. Fixed two-node Microtheory graph.
- Five fresh fixtures per cell; 200 internal snapshot iterations and 30 scoped API calls per fixture after warm-up; global and per-rule audit off. Randomized cell order per repeat; profile/API measurement order alternates by repeat.
- Record source/native/build hashes, active/count totals, elapsed profile time, scoped wall/process CPU time, graph projections, and audit counters.
- Gates: profile reports exactly `active_count` and `active_count × 200` clones; scoped calls make zero progress; graph and rule store unchanged; exact active/slot counts; audit/candidate/Term counters remain zero; build current.

## Interpretation

Report medians and p10/p90 for clone snapshot ns/iteration and scoped ns/call. Report `clone_ns / scoped_ns` as a mechanism fraction with explicit caveat: profile allocation/drop timing may differ from clone lifetime within the live scoped closure, and instrumentation timings do not imply natural workload distribution. Compare effect and edge contrasts in both measurements. No optimization decision follows from a ratio alone; any reuse requires visibility of all rule-body mutation paths and parity/invalidation evidence.
