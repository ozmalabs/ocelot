# Resource-version and scoped invalidation comparison v1.1

## Question

Can an explicit graph revision make external `UseTool` data reevaluable, and does existing per-microtheory scoped closure reduce irrelevant callback work while preserving results?

## Design

- Three independent fresh workers; each measures frame counts N=4,16,64 in paired global and scoped fixtures.
- Load the minimal CAN seed rule vocabulary so scopes use real `Microtheory` nodes. Each fixture has N disjoint Microtheories, each owning a trigger source and target. One shared custom rule matches each trigger edge. Its predicate compares a file-backed `UseTool` result with `"1"`; the callback receives the source node's graph-resident `resource_rev` and reads that revision's file.
- Each frame has its own `r{i}_v0.txt` and `r{i}_v1.txt`, initially both containing `0`; initial graph revisions are `r{i}_v0`. First run closure (all predicates false), then change only frame 0's currently referenced `r0_v0.txt` to `1` and run again without graph mutation. Next publish `r0_v1.txt` as `1`, set frame 0's graph `resource_rev` to `r0_v1`, and settle either globally or with `run_rules_scoped(..., mt0)`.
- Record callback reads/counts, progress, elapsed time (descriptive), final `(frame, revision, accepted)` projection, static access declaration, and source/native lock.
- A caller explicitly updates the graph revision and supplies the affected microtheory. This tests a viable representation/dispatch seam; it is not an automatic watcher.

## Preregistered gates

1. All three workers complete all six N×execution-arm cells with identical locked code/native inputs.
2. Initial closure rejects every target; an external-only change yields zero callback calls and no new acceptance.
3. After the revision graph update, both arms accept only frame 0; paired final projections match exactly.
4. The selected `UseTool` rule declares wildcard graph access. Scoped callback count must be below global callback count for N≥16; report counts and timings at every N.

## Claim limits

The N axis is an authored collection of independent frames. The probe measures callback work for one rule family, not natural locality, general asymptotics, wall-time speedup, automatic event routing, graph rollback, or the full seed workload. Existing `run_rules_scoped` is per-microtheory, so this does not establish arbitrary rule-level invalidation.

## Pilot disclosure

Before this v1.1 freeze, a one-frame pilot confirmed that `Microtheory` must be admitted through the CAN seed vocabulary and that a four-frame scoped arm invokes fewer callbacks than global closure. That pilot used one size, was inspected during development, and is exploratory; only the source-locked v1.1 size sweep is confirmatory.
