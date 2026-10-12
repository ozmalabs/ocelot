# Blind structural repair and selection v1 (preregistration)

## Question

Can the substrate, given only a live rule and observed input/output failures,
enumerate a bounded set of structural edits, select a useful edit through
isolated branch evidence, and preserve abstention when the evidence does not
identify a repair? This is the next capability gate after the graph-generated
threshold candidate lifecycle. It moves candidate enumeration and choice into
the substrate while keeping task construction and the external oracle in the
evaluation harness.

## Responsibility boundary

The harness may generate a task, introduce a fault, provide input/output
examples, execute branch candidates, and score outcomes against its oracle.
It must not provide the fault-family name, expected candidate family, live
target UID, corrected clause, task-specific candidate clause, or a diagnosis
flag. The candidate generator receives only the serialized live rule and
training examples with observed outputs. Candidate choice receives opaque
candidate IDs, branch outcomes, control outcomes, and resource costs. The
target UID/revision/hash may be bound only after selection for the mechanical
CAS commit.

## Candidate space and task panel

The initial candidate language is deliberately finite and stated in advance:
single local edits to a typed rule's `where` Term and effect list, using the
existing structural edit operators where possible. The enumerator must record
its full proposal count, rejected edits, duplicate canonical forms, and work
units. It may use type and shape constraints but may not use the hidden fault
label or oracle outputs outside the exposed training examples.

The panel will contain independently authored and source-locked cases across
at least three fault forms represented by the available edit language (for
example threshold/constant change, guard or relation change, and effect
change), plus no-repair and observationally ambiguous controls. A case is
eligible only when the oracle can distinguish the intended repair from the
faulty rule on a sealed finite input domain. Train, canary, and final sets are
disjoint. Task and fault generation are performed before candidate search;
the family label and corrected program remain sealed until analysis.

## Procedure

1. Freeze the runner, analyzer, edit-operator implementation, native binary,
   seed, task generator, and oracle specification in a source lock.
2. For each case, expose only the live rule and the registered training
   examples. Enumerate candidates without consulting the sealed labels.
3. Rehearse every candidate, no-op, and same-budget placebo in isolated
   shared-graph-page CoW branches. Capture full-copy parity on a counterbalanced
   subset. Charge enumeration, branch setup, rehearsal, and selection costs.
4. Let graph-native proof and evidence rules select at most one candidate or
   abstain. Apply a preregistered candidate cap; if enumeration exceeds it,
   report truncation and do not silently rank only a favorable subset.
5. Evaluate a selected candidate on the disjoint canary set. Commit only after
   the canary gate, by revision/hash-checked CAS. Evaluate committed behavior
   on the final sealed set.
6. Run at least three fresh workers. An independent analyzer verifies source
   locks, sealed split disjointness, proposal accounting, branch isolation,
   parity, selection/abstention, CAS receipts, and final outcomes.

## Primary measures and pass gates

- **Proposal coverage:** fraction of cases where the intended edit is present
  in the enumerated canonical candidate set.
- **Selection precision and recall:** correct selections among selected cases
  and correct selections among cases where a uniquely adequate edit exists.
- **Abstention quality:** no false commits on no-repair and ambiguous controls.
- **Held-out utility:** exact canary and final behavior, including protected
  regression count; training fit alone is not success.
- **Search cost:** candidate count, edit-expansion work, labels consumed, CPU
  wall time, peak RSS, and branch memory by phase.
- **Isolation and parity:** no primary mutation before CAS and exact semantic
  parity between full-copy and CoW arms.

The gate passes only if every source and accounting check passes, the exact
repair is proposed and selected for every uniquely identifiable panel case,
no-repair/ambiguous controls do not commit, all selected repairs pass both
sealed splits, and all primary graphs remain unchanged before CAS. Report
failure by stage (generation, evidence, selection, canary, commit, or
generalization); do not collapse failures into a single accuracy number.

## Interpretation limits

Even a pass establishes only bounded structural repair in the preregistered
finite edit language and authored task panel. The task generator and oracle
remain external. It would not show open-ended dimension induction, natural
task prevalence, self-directed benchmark creation, or general self-improvement.
If current graph rules cannot consume an enumerated candidate pool without
family-specific probe fields, record that as a failed integration gate and
measure the missing graph representation/API instead of restoring answer
fields to the probe.

## Relation to prior results

This protocol follows the source-locked blind family-selection baseline and
the end-to-end graph-generated proposal → CoW rehearsal → canary → CAS capture.
Those establish selection under supplied proposals and lifecycle execution
for one cued threshold task. This gate tests whether structural proposal
coverage and blinded multi-family choice can be connected. It is not a
reanalysis of those captures.

## Implementation check (2026-10-05, not a benchmark result)

`domains.edit_ops.enumerate_single_edit_candidates` now provides a deterministic
syntax-only pool over the available single-edit operations. A smoke invocation
on one two-edge rule with comparison and two referenced effect attributes
returned 17 unique candidates across comparison flip, match-edge deletion,
guard addition, and attribute-key swap, with no truncation. The function reads
only the rule JSON and derives guard keys/literals from its syntax; it receives
no task examples or oracle. Edge-identity guards are included when their
required emitted-edge structure exists.

This is not yet the registered evaluation: there is no source-locked panel,
independent analysis, task rehearsal, graph selection, canary, or commit. The
enumerator also exposes the current language boundary. It cannot add a missing
match edge, delete an existing guard, change a numeric constant, invent a new
attribute, or synthesize a new effect. Those gaps must be represented as
proposal-coverage misses rather than repaired by harness-supplied candidates.

### Proposal-coverage subgate

The first implementation subgate uses five fixed, sealed rule pairs covering
comparison flip, numeric constant shift, match-edge deletion, guard addition,
and effect substitution. The candidate function receives only each faulted
rule. The evaluation layer canonicalizes candidates and compares them with the
held-back target rule. Three fresh workers must produce identical candidate
IDs and coverage decisions, report no truncation, and reconcile proposal,
deduplicated, and unique counts. Candidate counts and enumeration wall time
are descriptive for this tiny panel; they are not general complexity or
throughput estimates. This subgate measures structural proposal coverage only:
it does not execute task examples or evaluate graph selection, canaries, CAS,
or transfer. Artifacts: [runner](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1.py),
[analyzer](../../../evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v1.py),
[fixture](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json),
and source lock/capture under `evaluation/`.
