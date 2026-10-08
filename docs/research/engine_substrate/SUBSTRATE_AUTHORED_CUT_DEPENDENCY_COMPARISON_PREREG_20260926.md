# Authored-workload dependency-derived cut comparison preregistration

**Lock date:** 2026-09-26, before confirmatory capture.  
**Stage:** Functional Substrate Establishment Plan, Stage 2 (structural
locality).  
**Grade:** structural and execution-safety diagnostic; not a natural-task
prevalence estimate or a general locality result.

## Question and claim boundary

On two already frozen authored workloads, do cuts derived from concrete
execution dependencies recover the task's authored ownership better than a
balanced-ID baseline, and can the resulting partition be maintained under
boundary mutation without losing full-closure behavior? The workloads are the
100-frame Bigville CAN cast (positive ownership control) and the connected
mixed-act discourse task (shared-state/negative control).

This experiment tests candidate-cut quality and whether existing execution
contracts permit scoped closure. It does not establish how common such cuts are
in natural workloads, infer sound dependencies from an incomplete trace, or
authorize default scheduler changes.

## Frozen workload ownership

1. **Bigville CAN:** use the existing 100-resident cast and builder. An
   authored frame is the five-Concept component owned by one resident
   Microtheory, as resolved through live `has_concept` membership. Preserve the
   existing causal edges and the task-access census mutation at resident 40.
2. **Connected discourse:** use the ten-event `phase3_mixed_act_dialogue.v1`
   fixture in fixture order. Every `origin` starts a frame, `unsolicited`
   starts a standalone frame, and `continuation`, `response`, and `repair`
   remain in the current frame. A Goal inherits its origin event's frame.
   DiscourseState, CommonGround, participants, and all other unassigned nodes
   remain explicit boundary/global nodes. Do not change ownership after
   examining dependency results.

Run each workload in fresh processes with tracing off, tracing on, and an
independent full-closure control. Freeze fixture, builder/materializer, rule
seeds, source tree, native extension/build manifest, Cargo lock, and protocol
hashes in the input lock before confirmatory capture. The earlier Bigville
resident-0 no-op and the connected discourse census are development evidence,
not confirmatory runs; retain them and do not relabel them.

## Dependency graph and candidate cuts

Keep dependency evidence typed and distinguish observed from conservative
potential dependencies:

- **Concrete graph dependencies:** every extant directed edge whose endpoints
  have different assigned task frames; separately count edges incident to a
  global/boundary node.
- **Observed runtime accesses:** concrete read/write endpoint pairs from the
  partial native access trace, attributed to active rule and checkpoint. A
  missing trace pair is unknown, never evidence of independence.
- **Static rule dependencies:** native read/write declarations, including
  wildcard flags. Report their potential coupling separately; do not invent
  concrete node pairs where the declaration does not identify endpoints.

Compare exactly three deterministic partition arms over the assigned task
nodes, leaving globals explicit in every arm:

1. **Authored ownership** as frozen above.
2. **Balanced-ID baseline:** sort task nodes by stable native ID and split into
   the same number of non-empty frames with sizes differing by at most one.
3. **Dependency-derived cut:** build a weighted undirected graph from the
   union of concrete graph dependencies and observed runtime access pairs;
   assign unit weight to each pair and run deterministic min-fill ordering,
   breaking ties by stable native ID, then make contiguous groups matching
   authored frame sizes. Also report the min-fill ordering's induced-width
   upper bound. This is a candidate heuristic, not an optimal partition or a
   proof of omitted dependencies.

For each arm report frame-size distribution, cross-frame concrete-edge count,
cross-frame observed access count, authored-owner pair recall, global-boundary
incidence, cut-boundary size, and dependency-derived induced-width bound.
Report direct edges, observed accesses, and static potential coupling in
separate columns; do not collapse them into one completeness score.

## Mutation and execution protocol

At each workload's existing mutation seam, perform three frozen boundary
operations in separate replay branches: insert a cross-frame dependency,
retract it, then change its weight/value without changing identity. For
Bigville use the resident-edge mutation harness. For discourse, use the
existing task-graph boundary-link mutation harness; if no valid discourse
mutation seam can preserve the fixture oracle, record that cell unsupported
and do not substitute a synthetic result.

Recompute candidate cuts after every mutation and compare them with the
frozen-cut arm. Capture cut-maintenance work and complete graph identities,
types, and attributes at every checkpoint. Run scoped closure only when the
workload's native ownership/boundary contract passes a predeclared audit:
every mutable task node has one owner, every cross-owner effect is surfaced to
all affected owners, and global mutable state has an explicit boundary update
path. Otherwise the arm must return `refused_shared_state` before executing;
this refusal is a valid safety result, not a parity pass. For any admitted
scoped arm, compare complete semantic state against fresh monolithic closure
after every mutation. Include an omitted-boundary negative control that must
diverge from the monolithic projection when the omitted dependency is
semantically active.

The discourse shared-candidate failure at N>=2 is a known negative control:
it must not be hidden by repartitioning or counted as a locality success.
Bigville's previous fixed-partition replay is development evidence only; the
new analysis must exercise cut recomputation after mutation.

## Gates and stop rules

- All input/source/build fingerprints match the lock; fixture/task oracles
  pass; every task node has exactly one owner and every global node is
  accounted for.
- Trace-on/off semantic projections match and no trace events are dropped;
  trace coverage remains explicitly partial.
- All dependency classes and candidate-cut metrics are emitted for each
  checkpoint, including refusal and unsupported cells.
- Any scoped arm either passes the ownership/boundary audit and exact full-state
  parity at all checkpoints, or refuses before execution. A parity failure
  blocks that partition family and triggers no parameter search on the same
  capture.
- Omitted-boundary sensitivity control produces the preregistered divergence;
  otherwise the selected mutation did not test the boundary contract and the
  affected result is inconclusive.
- Preserve raw per-run records, including failed/unsupported arms; no
  post-hoc fixture, partition, or threshold changes.

If no dependency-derived partition improves cut metrics without violating the
owner/boundary contract, report that negative result and revise the locality
claim. Do not optimize the scheduler or alter default execution in this study.

## Required outputs

Preregistered runner and independent analyzer; pre-run input lock; raw
per-process capture; analysis with all gates and exclusions; source/build
fingerprints; and a concise Stage 2 plan update. Report structural and
semantic results separately from timing. Any performance follow-up requires a
new lock with instrumentation overhead, cold/warm setup, CPU, wall time, and
RSS gates.
