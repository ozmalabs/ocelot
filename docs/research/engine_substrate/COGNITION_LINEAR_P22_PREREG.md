# P22 registered checkpoint evaluation preregistration

**Status: DRAFT — NOT FROZEN. Protocol feasibility amendment recorded 2026-10-24; do not run on held-out worlds.**

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

This requires 8 generation-zero roots plus 24 descendant checkpoints. The
12 unchanged/adaptive-only descendants are passive controls; the 12
invention-only/full descendants each require their own candidate-specific
approval and verified transition receipt. Two pending candidate packets are
bound to the invention-only generation-zero roots (D4 digest
`fe39a44242987c5c97404c8b0812c3928a7324aee2911f57133417ce2650236c`;
Loopover digest
`7308895927d5ca447ae80199e9ee369e881ed0effa223e166c65b88f51b40f2c`). If
both are approved and verified, they produce only invention-only generation
one descendants. A third candidate-specific request selects D4 full-arm g0
qualification `#12259`; if approved and verified, it produces full-arm g1.
After those three transitions, nine more invention/full transitions remain.
The 12 unchanged/adaptive-only descendants now have
training-only captures on shared worlds 0600–0602; the immutable parent-linked
records are in `p22_passive_control_training_lineages_0600_0602.json`. These
captures do not complete the resource-matched development gate. No checkpoint
may be copied across arms or generations.

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

Current allocation audit: all 1,600 world IDs match generated world
identities, and all 1,600 seeds are unique across both families and all four
splits; each family/split has 200 worlds. The
canonical base allocation SHA-256 is
`eb95801e0bd62b0702f559948611b791f256ad9e6dc0a59e9c7805fab68b6f22`. This is
not the final freeze hash: the freeze adds the verified ancestor checkpoint
digests and all resource ceilings before hashing the complete analysis plan.

## Resource and integrity criteria

The efficacy estimand is a paired capability comparison under identical
worlds, interfaces, and frozen per-field resource ceilings. Every checkpoint
resource field must have source-backed measured coverage and remain within its
frozen ceiling before any held-out world is constructed. Measured isolated wall
time is reported for every checkpoint and checked against its ceiling. Exact
equality of realized resources across all members of
`analyze_linear_p22_v1.MATCHED_RESOURCE_FIELDS` is required for an
efficiency-comparability claim, but is not a prerequisite for reporting the
registered capability estimand. If any realized resource differs, retain the
complete paired outcomes and report `CAPABILITY_ONLY`; efficiency is
`NOT_ESTABLISHED`. In particular, candidate approval time, approval events,
and simulator receipts must remain visible even though passive controls carry
none. Do not pad controls with sham approvals or receipts. Equal ceilings do
not imply equal realized cost, and an unmatched result must never be described
as efficiency evidence.

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
- every checkpoint has complete measured resource provenance and stays within
  its frozen per-field ceiling; the development panel verifies common world
  delivery and ceiling enforcement. Any exact realized-resource mismatches are
  retained and preclude efficiency claims, but do not block the capability
  analysis;
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
resource-preflight, structural-control, and fail-closed held-out checks. No
descendant manifest is complete. The 12 unchanged/adaptive-only descendants
are captured on shared training worlds 0600–0602; all 12 checkpoint digests
and parent links verify. Their six unchanged-versus-adaptive cumulative checkpoint snapshot pairs
all mismatch. A control-only common-world panel scored them on four fresh
training worlds per family and found 0/24 unchanged/adaptive pairs matched.
Six existing four-arm root panels cover 40 training-world rows. All 40 use the
same world across arms, respect the shared primitive-work and native-rule
progress ceilings, and report every contract resource dimension; 0/40 have
exact realized-resource equality, so they support development capability
comparisons only. They do not establish per-field frozen resource ceilings for
the final 24-checkpoint panel or the full multi-generation lineages. The D4
and Loopover invention-only requests and the D4 full-arm request for generation
one have each been approved and consumed once, with 12 reviewer-reported
seconds; their receipts and generation-one checkpoints verify. These complete
3 of 12 invention/full descendants. D4 invention-only generation two has now
also been approved and captured with a verified receipt; 4 of 12 descendants
are present, leaving eight separately approved invention/full transitions. Loopover full-arm still lacks a qualified
generation-one candidate, and nine further invention/full transitions remain,
each requiring its own approval. Fresh Loopover full-root training-only
searches on worlds 0800–0817 failed to qualify a candidate. Candidate `#11545`
had 16,236 residual independent-goal trials in the 0800–0803 and 0808–0811
panels; candidate `#31551` had no independent-goal trials in 0804–0807;
`#21545` had 10,824 residual trials in 0812–0814. The maximum configured
90,000-attempt, 120-tick panel on 0815–0817 found no candidate on any goal.
The D4 invention-only g1 continuation on 0818–0821 independently replayed
candidate `#9458` (`84854777d0e3b48f447ecd04236a794eff39a46546edb3f19e47f506492ce66a`)
and qualification `#15851` (0960/0818); its one-action packet awaits exact
approval. The approved D4 invention-only g2 search on worlds 0822/0823/0825
did not find an improving g3 candidate: its only formally qualified candidate
was an identity effect and was excluded; one other qualification record had a
missing kind and was rejected. Exact realized resource equality
is not a freeze prerequisite after the feasibility amendment; measured resource
coverage, common allocated ceilings, within-ceiling outcomes, and complete
development plumbing remain required. This draft still cannot be frozen
because the 24-checkpoint descendant manifest and per-checkpoint measured
resource/ceiling manifest are incomplete, and candidate-specific decisions
remain for the nine future transitions. No held-out allocation may be accessed.

At commit `d390d58383a48eb48a13a8da1e9206dc0a64ebe6`, the current native
provenance audit is `ATTESTED` with no issues after the 2026-10-24
analyzer/protocol amendment. The final freeze must recompute every provenance
hash and attest the runtime after all remaining implementation changes.

| Provenance item | SHA-256 |
|---|---|
| Runner | `14f911f6bbf8083a080eab868b77350b9c028f26b8f2e8d92dafebb228866ec7` |
| Analyzer | `10dce1e6e0b23f7a1f100ad3c7120829ab5335bf87f792b2a08408f5c4122643` |
| Source bundle | `52af8bdd7a91cd536a4a2c4b02322a7d67e4d8a56bff20a1d77bb2841108cde4` |
| Python wrapper | `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5` |
| Loaded native extension | `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07` |
| Native build receipt | `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66` |
| Cognition profile | `2034d2d4b67caf69d9c6da327895b468d8cb07942c58f031ee2a0f531ae725e4` |
| World adapter | `8dee84864837b4d6bc72ef4e06b6d5d7babad8a8f867f85221d0178bfee63c4d` |
| Dependency closure | `a1a6e531f12703e2f0de0bdcf7632072fb85af10a28e7a5f704eaf726ae66a15` |
