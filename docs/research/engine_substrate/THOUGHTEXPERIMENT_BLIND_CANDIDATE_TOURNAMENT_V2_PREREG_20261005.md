# Blind candidate tournament v2 (preregistration)

## Question

Does the generation → measured branch rehearsal → graph selection/abstention
→ canary → CAS path transfer from a boolean effect edit to a numeric
threshold edit, and does it refuse no-repair, ambiguous-training, and
irrelevant-relation proposals? Can the full measured lifecycle cost be
reported by phase?

## Panel and policy boundary

Six opaque cases cover boolean effect repair/no-repair, numeric threshold
repair/no-repair, an ambiguous threshold case whose training examples do not
separate the current threshold from the target, and an irrelevant relation
proposal. The boolean task family reuses the v1 rule shape; the threshold
family uses `signal >= threshold` with target labels specified per example.
The relation case exposes an observed `has_tag` neighborhood extension that
does not change the task outcome.

Candidate generation receives only the live rule and observed relation
signatures. The harness keeps task labels and splits for scoring. The graph
selector receives opaque candidate IDs, the candidate rule clauses, measured
gains, controls, resource values, and replication evidence; no operator name,
fault label, target UID, or corrected rule is attached. Target UID/revision/
hash are bound only after selection for CAS.

## Procedure

Three fresh workers run the six fixed cases. Candidate, no-op, and a
deterministic one-edit placebo each receive three independent shared-page CoW
rehearsals on the train split. Candidate gain is ten points per correct
training example. The graph-native seed mints obligations, rejects candidates
that fail the strict margins over both controls, and selects among passing
candidates by MDL. Selected candidates receive three canary rehearsals on a
disjoint split. Only an exact canary pass proceeds to RulePatch CAS. Final
examples are evaluated after commit. Cases without a selected candidate close
the evidence batch and must issue an explicit abort without changing the live
revision.

## Registered outcomes and measurements

The two repair cases (boolean and threshold) must select one unique
control-beating candidate, pass canary and final examples, and commit exactly
once. Boolean/threshold no-repair cases, the ambiguous-threshold case, and the
irrelevant-relation case must abstain and preserve revision. The relation case
must generate at least one `add_match_edge` candidate whose measured utility
does not clear the control margin.

Capture candidate generation, no-op, placebo, candidate-pool rehearsal,
selection, canary rehearsal, canary/commit tick, final verification, and
no-repair abort timing separately. Also capture candidate counts, complete
branch outputs, control and candidate gains, source hashes, replication
agreement, graph status, patch receipt, and revision before/after each stage.

This remains a six-case authored panel with harness-owned tasks and oracle.
Passing shows transfer between two local edit families and honest behavior
under three controls. It is not a natural-task or general learning estimate.
