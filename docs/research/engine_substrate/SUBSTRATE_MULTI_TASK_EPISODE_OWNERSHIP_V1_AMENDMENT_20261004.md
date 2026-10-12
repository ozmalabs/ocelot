# Multi-task episode ownership v1 amendment

Date: 2026-10-04

The preregistration's exact whole-graph digest reproduction gate was not met:
two initial workers had identical graph node/edge counts and task behavior, but
their raw hashes differed. A field-level comparison found eight diagnostic
nodes with differences only at `attrs.ts` and `attrs.runtime_s`. No node
identity, edge, task output, or owner projection differed.

The retained initial capture records this falsification of raw-hash
reproducibility. For the final v1 capture, the gate is therefore narrowed to an
explicit structural digest that recursively removes only those two observed
diagnostic timing keys, while preserving both raw graph hashes. Independent
analysis verifies the normalized digest and recomputes ownership and crossing
edges from each complete graph. This amendment does not claim that these fields
are universally nonsemantic; it reports the measured difference in this run.
The result remains limited to two workers and one fixed prompt order.
