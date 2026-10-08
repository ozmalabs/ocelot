# Thoughtexperiment journal mutation matrix v1.4 preregistration

Date: 2026-10-04

## Objective

Extend the fixed current-source journal matrix to all audited semantic writer
classes and verify mutation revision behavior alongside exact residual parity.

## Method and locked inputs

Run 20 fixed cases: node attribute set; direct mutable node access; node
attribute removal; node type change; live, fresh, and tombstoned identity
restoration; node deletion; node insertion; edge insertion, replacement,
mutable attributes, single and batch deletion; repeated writes; checkpointed
writes; a post-capture divergence control; identity-preserving edge restore;
a scope transition; and a derived-index control. The evaluator records the
complete journal residual and an independently computed whole-graph diff at
the capture point. The checkpoint case compares phase residuals. The
post-capture control verifies a later semantic write advances the revision
while the earlier journal no longer equals the global diff.

For semantic writers and the scope transition, require the mutation revision
to advance. For derived-index declaration, require no revision advance and no
serialized semantic diff. Require every case's journal residual to equal the
whole-graph diff at capture, including the scope transition's empty diff.

Before execution, lock this protocol, evaluator, capture runner, independent
analyzer, graph/persistence/value/interner sources, Cargo manifest, and
lockfile. The runner refuses source drift or existing output. Run the dev-profile
Cargo executable, then the independent analyzer over the raw capture. No timing
is collected.

## Claim limits

The matrix covers these fixed direct mutation paths in a single-threaded test
fixture. It does not establish concurrency safety, arbitrary caller-path
completeness, performance, or broad tractability. The source audit remains a
hook-presence audit; this matrix supplies finite runtime evidence for listed
operations only.
