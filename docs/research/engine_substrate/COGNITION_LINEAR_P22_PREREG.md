# P22 registered checkpoint evaluation preregistration

**Status: DRAFT — NOT FROZEN. Do not run on held-out worlds.**

This file records the protocol choices that can be fixed before the final
checkpoint manifest exists. It is not a standalone freeze: it contains no
`P22_FREEZE_JSON`, commit identity, checkpoint manifest hash, or runtime
provenance. The held-out runner must continue to reject it until those fields
are completed, the manifest passes preflight, and this file is committed alone
immediately before the one permitted held-out run.

## Question and estimands

For the finite D4 and Loopover simulator families, does the full learner's
approved graph-authored process lineage improve solved-task outcomes over its
same-family unchanged ancestor from generation 1 through generation 3? Report
each family separately. This protocol does not support claims about general
intelligence or human-relative performance.

The primary paired outcomes are the generation-3 solved-rate difference
(`full` minus `unchanged`) and the linear slope of the paired solved-rate
difference over generations 1, 2, and 3. Resample whole world IDs so each
world's three generation measurements remain clustered. Use 10,000 bootstrap
draws and the fixed `bootstrap_seed` in the freeze. Compute each one-sided
bootstrap p-value at the zero-effect boundary as
`(1 + count(bootstrap_effect <= 0)) / 10,001`; Holm-adjust the four tests formed
by two outcomes in each of two families.

Each family passes the registered efficacy criteria only if its estimated
generation-3 gain is at least `+0.10`, its slope is at least `+0.05` per
generation, both one-sided 99% lower bounds are positive, and both Holm
adjusted p-values are at most `0.01`. Ceiling, floor, flat, negative, missing,
and failed outcomes remain in the analysis; no threshold changes or row
imputation are allowed.

## Arms and checkpoint panel

Use four arms: `unchanged`, `adaptive_only`, `invention_only`, and `full`.
Both families require a digest-verified generation-zero ancestor for each arm
and checkpoints at generations 1, 2, and 3: 24 scored checkpoints total.
Every checkpoint must descend from its family/arm ancestor through consecutive
verified parent digests. The unchanged and adaptive-only lineages preserve the
ancestor process and carry no adoption receipt. Every invention-only and full
descendant carries a candidate-specific approval and verified simulator
receipt. All four arms in a family use the same generation-zero process
ancestor.

The held-out panel has 200 independently seeded worlds in each family. Score
every generation checkpoint from all four arms on the same world in that
family, retaining failed tasks and native statuses: 2 families × 3
generations × 200 worlds × 4 arms = 4,800 rows. Restore each checkpoint in an
isolated native learner and use the same native world adapter, solver, task
input, and declared ceilings for every arm. The runner's fixed allocation also
contains separate 200-world training, selection, and validation panels per
family. Their split-specific world IDs and seeds come from
`linear_p22_v1.allocation()` and must be frozen by hash; do not reuse an ID or
seed across families or splits.

Current allocation audit: 1,600 world IDs and 1,600 seeds are unique across
both families and all four splits; each family/split has 200 worlds. The
canonical base allocation SHA-256 is
`ab8571b0d83c27b5704002910fd50dc7fa1022a3445287da6717f72ae28fc454`. This is
not the final freeze hash: the freeze adds the verified ancestor checkpoint
digests and all resource ceilings before hashing the complete analysis plan.

## Resource and integrity criteria

The efficacy panel is efficiency-comparable only when every member of
`analyze_linear_p22_v1.MATCHED_RESOURCE_FIELDS` is exactly equal across the
four arms for every family, generation, and world. Measured isolated wall time
is reported for every checkpoint and checked against a declared ceiling, but
is reported separately from exact per-world resource matching. Every
checkpoint resource field must have source-backed measured coverage and be
within its frozen ceiling before any held-out world is constructed. Missing
resource evidence or any mismatch blocks the registered phase pass; it cannot
be replaced by equal ceilings or an aggregate average.

Retain all 4,800 rows. Require all four structural controls to pass:

- checkpoint digest tampering is rejected;
- malformed permutation is rejected;
- broken lineage parent integrity is rejected;
- repeated scoring is deterministic.

Also require complete native runtime attestation, matching runner/analyzer,
source bundle, Python wrapper, loaded extension, build receipt, cognition-on
profile, world adapter, and dependency-closure hashes. The frozen checkpoint
manifest, allocation plan, resource ceilings, isolated wall times, and their
hashes must agree exactly with the runner and analyzer inputs.

## Freeze and execution gate

Before freeze, all of the following must be true:

- the 24-checkpoint manifest is complete and its root, parent, approval,
  receipt, and immutable checkpoint digests verify;
- every checkpoint has complete measured resource provenance, and the
  development panel establishes exact per-world resource matching;
- isolated wall-time values and all resource ceilings are fixed;
- the native runtime and complete source/dependency closure attest cleanly;
- the exact split allocation, criteria, controls, and analysis code are frozen;
- the pending registered-root candidate requests have been resolved by exact
  candidate-specific decisions, and no checkpoint is inferred from an
  unapproved proposal.

Then fill the machine-readable freeze, freeze its commit identity and hashes,
and commit this file alone. Only the immediately following held-out invocation
may construct the sealed worlds. Preserve raw output bytes and hash them before
analysis. Any implementation defect requires a versioned protocol and an
untouched split; historical allocations must not be rescored.

## Current readiness

The runner and analyzer implement the allocation, 24-checkpoint manifest,
resource-preflight, structural-control, and fail-closed held-out checks. The
current D4 and Loopover registered-root candidate packets are still awaiting
exact approval. Approved descendants, complete cross-family lineages, and an
exactly resource-matched development panel are not available, so this draft
must not be frozen and no held-out allocation may be accessed.
