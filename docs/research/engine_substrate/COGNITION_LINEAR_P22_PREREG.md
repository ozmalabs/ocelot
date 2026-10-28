# P22 registered checkpoint evaluation preregistration

**Status: DRAFT — NOT FROZEN. Protocol feasibility amendment recorded 2026-10-24; do not run on held-out worlds.**

**Continuation review (2026-10-24):** The canonical plan now schedules diagnostic P23 and prerequisite remediation P24–P26 before any further P22 freeze decision. P27 will explicitly select justified original-protocol re-entry or a separately versioned scheduled-checkpoint study. This draft is retained unchanged in its outcome/approval criteria by the planning decision; it is not frozen, completed, or replaced by development results. See [continuation decisions](COGNITION_POST_P22_CONTINUATION_REVIEW_20261024.md).

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
the final 24-checkpoint panel or the full multi-generation lineages. The prior D4 invention-only g1 and D4/Loopover full-arm requests were each
approved and consumed once; D4 invention-only g2 was also approved and
captured. Two later full-arm packets were then approved with 12
reviewer-reported seconds each: D4 full-arm g1 candidate `#9440` produced a
verified g2 checkpoint, and Loopover full-arm g0 candidate `#1611` produced a
verified g1 checkpoint. These bring captured invention/full descendants to
6/12; six further transitions remain, each requiring its own exact approval.
The consumed packets and raw results are recorded in
[`COGNITION_P22_APPROVAL_REQUEST_D4_FULL_G1_0002_0003.md`](COGNITION_P22_APPROVAL_REQUEST_D4_FULL_G1_0002_0003.md),
[`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G0_0034_0035.md`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G0_0034_0035.md),
and the plan's dated ledger. No validation or held-out allocation was used.

Earlier training-only branches remain unchanged: D4 invention-only g2 found
no improving g3 candidate, while the Loopover invention-only g1 continuation
did not qualify a g2 candidate. Exact realized resource equality is not a
freeze prerequisite after the feasibility amendment; measured resource
coverage, common allocated ceilings, within-ceiling outcomes, and complete
development plumbing remain required. This draft still cannot be frozen
because the 24-checkpoint descendant manifest, per-checkpoint measured
resource/ceiling manifest, and final isolated wall-time panel are incomplete.
No held-out allocation may be accessed.

**Current checkpoint resource snapshot audit (2026-10-24):** The two registered
family root artifacts, the passive-control lineage artifact, and four exact
approved-action results contain 24 digest-valid checkpoint records: 8 roots,
12 unchanged/adaptive descendants, and 4 invention/full descendants. The native
resource snapshots for all 24 records pass digest validation and report measured
values for all 20 analyzer resource fields. This is 16 of the required 24
descendant checkpoints; the other eight require later arm-specific lineage
actions and, where applicable, exact user approval. The audit does not supply
the final development scoring panel's isolated wall-time measurements or freeze
the per-field ceilings. Raw input SHA-256 values: D4 roots
`bb88741136b5c2dc88daa33cdd0bbe6dbb94b261c45292b2cdef0b79c1661aee`, Loopover
roots `3cbcc409fb0572dc6cfb0cc3d013f0084c2ae21ab12e3705dca181bb9818e346`,
passive lineages `11478f6b590f5923464c7ec2f1b4f04c0c9dd2bdbd601f02bf9c00905ed2d0b3`,
D4 invention g1 `50e54f9b6decd864abab66d3138be9b8c91c949b7379da0ae13823d838a988b4`,
D4 invention g2 `f72db827c1e05f382ae7fd84c1655f4f0c4d1cac61dbe57823438d092feb1bc7`,
Loopover invention g1 `f1b709141893c88975ebc09356e81ea28873a2638c634c05e8e784b2aaf5dbb9`,
and D4 full g1
`2355279174397e964cfb66a960696f69e27764c2c8c7fd4911616005ddafba2c`.

The captured D4 invention-only g2 checkpoint
`p22-d4-g2-84854777d0e3` has digest-bound cumulative primitive work `487906`,
above the runner/scorer's original `120000` implementation limit. Before any
preregistration freeze, a resource-feasibility amendment raised the supported
maximum to `1000000`; this leaves the final shared ceiling to be fixed only
after the full checkpoint manifest and development resource panel are complete.
A one-world training-only feasibility probe scored this checkpoint under a
`600000` cumulative ceiling on unused registered draw `p22:d4-v2:train:0607`.
It solved the task, ended at 487,911 cumulative work, respected the ceiling,
added no approval or receipt, and did not access held-out data. The isolated
worker took 21.128 seconds and peaked at 2,796,838,912 bytes RSS. Raw artifact
SHA-256: `47b7f80ae417b27ec638ed27822e029cf0cefbbe5f973ad59ec9789c84548b18`.
This single cell establishes feasibility at 600,000 only; it does not complete
the common-world development panel, choose the final resource ceilings, or
establish efficacy. Preserve the earlier checkpoint and run as historical
evidence. The final shared ceiling must be at least 487,911 and no greater than
the supported maximum, and every other checkpoint must pass the same preflight.

**Existing-checkpoint isolated resource panel (2026-10-24):** All 24 currently
captured root/descendant checkpoints were scored in separate workers on one
common fresh registered training world per family: D4 draw 0608 and Loopover
draw 0621. These IDs were absent from prior P22 result artifacts before use.
All 24 cells completed under a shared `600000` cumulative primitive and `20000`
native-rule-progress ceiling, with verified resource snapshot digests and
measured values for all 20 analyzer fields. No approvals or receipts were added;
no validation or held-out allocation was accessed. All 24 scores were zero on
this one-world diagnostic, so it is not efficacy evidence. Maximum realized
wall time was 21.303 seconds, peak RSS was 2,882,777,088 bytes, and cumulative
primitive work was 487,910, all on D4 g2. The raw [artifact](../../../evaluation/process_mastery/results/p22_resource_panel_existing_checkpoints_0608_0621.json)
SHA-256 is `2ca76c0de136df6ebb617b5c1952b9630381b5c7dfe5484eecb1c0801fc144da`. This
panel supplies initial isolated resource measurements for the 16 extant
descendants; it does not replace the required complete development panel or
provide measurements for the eight unbuilt descendants.

**Four-world existing-checkpoint resource follow-up (2026-10-24):** Repeated
the isolated resource panel on four distinct common registered training worlds
per family, using draws 0609–0612 for D4 and 0622–0625 for Loopover. The 24
currently captured checkpoints produced 96/96 completed cells; all respected
the 600,000 cumulative primitive and 20,000 rule-progress ceilings. All resource
snapshot digests verify and every cell has measured values for all 20 analyzer
fields. Outcomes include 35 solved and 61 unsolved rows; these are development
training diagnostics, not efficacy evidence. No approvals or receipts were
added, and no validation or held-out allocation was accessed. Maximum observed
maximum isolated cell wall time was 21.159 seconds; maximum cumulative
`wall_time_seconds` was 1,651.274 seconds, which includes lineage work. Peak RSS
was 2,884,263,936 bytes and cumulative primitive work 487,911 (D4 g2). The
compressed [artifact](../../../evaluation/process_mastery/results/p22_resource_panel_existing_checkpoints_0609_0612_0622_0625.json.gz)
has SHA-256 `147462e7e21039c2ebb89d790c39248ae1e1e44efd50cefa15b583e06a947779`;
decompressed JSON SHA-256 is
`cffd355b7803b415798b5b4ee676f0a940c6fdd397a725a3da7abb3c950069e8`. This
extends isolated measurements for the 16 present descendants but leaves the
eight missing descendants, final per-field ceilings, and the complete
development panel outstanding.

At source revision `10af7d389051b3ca3bf249173064e5e0b7c12623`, after the native
identity-effect qualification guard, the current provenance audit is `ATTESTED`
with no issues; source-bundle/build-source match and native symbol binding are
true. Runner and analyzer self-checks pass with `heldout_accessed=false`. The
final freeze must recompute every provenance hash and attest the runtime after
all remaining implementation changes.

| Provenance item | SHA-256 |
|---|---|
| Runner | `14f911f6bbf8083a080eab868b77350b9c028f26b8f2e8d92dafebb228866ec7` |
| Analyzer | `10dce1e6e0b23f7a1f100ad3c7120829ab5335bf87f792b2a08408f5c4122643` |
| Source bundle | `fb648693eb50024b4e240c0a7877a361826c048a2f1eb793a538bc62b6f39c52` |
| Python wrapper | `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5` |
| Loaded native extension | `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07` |
| Native build receipt | `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66` |
| Cognition profile | `2034d2d4b67caf69d9c6da327895b468d8cb07942c58f031ee2a0f531ae725e4` |
| World adapter | `8dee84864837b4d6bc72ef4e06b6d5d7babad8a8f867f85221d0178bfee63c4d` |
| Dependency closure | `a1a6e531f12703e2f0de0bdcf7632072fb85af10a28e7a5f704eaf726ae66a15` |

**Latest development provenance refresh (2026-10-24):** Recomputed from
checkout `3e3ef32f6b34f3c5030ccf09114d22a0d3348bd8`. Runtime attestation is
`ATTESTED` with no issues; the native extension is loaded from
`runners/dsl/python/substrate_rs/_native.abi3.so`, its digest matches the build
receipt, build sources match the checkout, and native symbol bindings verify.
This refresh supersedes the older snapshot above for current-checkout
readiness, but is not the freeze provenance because the preregistration is not
frozen and source changes may still occur.

| Provenance item | SHA-256 |
|---|---|
| Runner | `fb65b52691a51b0d258a5bed9ae916b322516f151a6a9df1282add22f4dcce4d` |
| Analyzer | `10dce1e6e0b23f7a1f100ad3c7120829ab5335bf87f792b2a08408f5c4122643` |
| Source bundle | `633a01942426ec17adf605b2898b5d6e7150c5e1ebe8cfc6c5cc6939949ee39a` |
| Python wrapper | `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5` |
| Loaded native extension | `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07` |
| Native build receipt | `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66` |
| Cognition profile | `2034d2d4b67caf69d9c6da327895b468d8cb07942c58f031ee2a0f531ae725e4` |
| World adapter | `375a8ed6c008ff710855bca23ef5f2b86281fa36c35fdd696f03ccfb048950d0` |
| Dependency closure | `a1a6e531f12703e2f0de0bdcf7632072fb85af10a28e7a5f704eaf726ae66a15` |

**Current-checkout gate refresh (2026-10-24):** The seven-module P22 regression
bundle listed in the build plan passes 86 tests. Runner and analyzer self-checks
pass, the runner verifies all 24 structural lineage links and the four required
structural controls, and it reports `heldout_accessed=false`. A separate
read-only audit confirms the four-world resource artifact has 96 unique
checkpoint/world cells, all 96 resource digests verify, and every recorded
cell respects its 600,000 primitive and 20,000 native-rule-step limits. This
does not make the draft freeze-ready: the 24-checkpoint manifest still lacks
eight invention/full descendants, and final isolated wall-time measurements,
per-field ceilings, exact candidate decisions, and refreshed final provenance
remain outstanding. No validation or held-out allocation was accessed.

**D4 invention-only generation-three search update (2026-10-24):** A
proposal-only continuation from the digest-valid g2 checkpoint used fresh
distinct training worlds 0924–0926, reserving 20,000 attempts per world and
60,000 total. All three tasks remained stuck. The seven recorded proposals
yielded no valid improving qualification: one qualification record lacked its
required kind, and identity-effect candidates received no qualifications.
The run inherited its two approvals and two receipts but added none; it created
no child checkpoint and used no validation or held-out allocation. Resource
and native-rule-work digests verify, with complete rule identity coverage.
The [raw training artifact](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0924_0926_ticks60_depth3.json)
SHA-256 is `583e31d86471d5a032284f2a5a894bcb255c8418827b56599076924db628e24b`;
the resource snapshot SHA-256 is
`a57af5f61107cc70d352a731961b9ae874af511e65072f403fd68b7cc7f716c0`, and the
native-rule-work SHA-256 is
`daaf7de53df49757bedb03a4f77a748954ce364002a8c14b09059b9109ea03f4`. This
negative search does not satisfy the missing D4 invention-only g3 lineage or
change the draft/freeze disposition.

**Loopover invention-only generation-two search update (2026-10-24):** A
proposal-only continuation from the digest-valid generation-one checkpoint
`p22-loopover-g1-2638da0f23ae` used fresh distinct training worlds 0924–0926.
Each task reserved 20,000 attempts, for 60,000 new attempts; all three remained
stuck, and none of the three proposals qualified. The parent snapshot recorded
20,000 reserved attempts, bringing the recorded lineage total to 80,000 against
the run's 120,000 ceiling. The run inherited its one
approval and one receipt but added neither, created no child checkpoint, and
used no validation or held-out allocation. Resource and native-rule-work
digests verify with complete native identity coverage. The [raw training
artifact](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0924_0926_ticks60_depth3.json)
SHA-256 is `355a1976960782789b2a6b87474b6d70c2d1002ddb9e5db045ba66230330a7d7`;
the resource snapshot SHA-256 is
`73c409c9f41334cc673c61a84baa8145cb3ebc6937da53772043dc1327b6f53e`, and the
native-rule-work SHA-256 is
`d26ec03630aa6e8e9898d0139564a969a244126f3c7c9bae999f42ce96781c7c`. The
generation-two lineage gate remains unmet; this does not change the draft or
held-out disposition.

**Loopover invention-only generation-two follow-up (2026-10-24, draws 0994–0996):** A separate proposal-only branch restored the digest-valid g1 checkpoint and searched three fresh distinct training goals at 20,000 attempts each. All tasks remained stuck and two new candidates received no qualification. The branch added 60,000 attempts to the checkpoint's 20,000-attempt snapshot, for 80,000 under its 120,000 graph ceiling. It inherited one approval and one receipt, added neither, and created no child checkpoint. Validation and held-out allocations are empty. Resource and native-rule-work digests verify with complete identity coverage and zero unresolved rules. Cumulative wall time increased 541.803 seconds, peak RSS was 2,029,113,344 bytes, and native rule steps increased by 33. The [raw artifact](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0994_0996_ticks60_depth3.json) SHA-256 is `feffb435d1b24298a0e4ffe7c205a2c199a99779a305dd0b9af1abfafce33d96`; resource snapshot SHA-256 is `2970f935a04341cc64c5553c02eaea50ea61daaaf8ef6bddd5144da3c43d12c6`; native-rule-work SHA-256 is `e0d424633afe1f78536305080fb35c3a9913bb48f4ac5dff19dff50fb97f000c`. No invention-only g2 candidate resulted.

**Loopover invention-only generation-two second follow-up (2026-10-24, draws 0997–0999):** A further uncheckpointed branch restored the same g1 checkpoint, used three fresh distinct training goals at 20,000 attempts each, and produced one new candidate (`#81578`, digest `654e6febbdb00a40016bc5e03dccd0e1093a14457347a379190415438d036d6b`) with no qualification. All tasks remained stuck. It added 60,000 attempts to the parent snapshot's 20,000, for 80,000 under the 120,000 graph ceiling. One approval and one receipt were inherited; no approval, receipt, or checkpoint was added. Validation and held-out allocations were empty. Resource and native-rule-work digests verify with complete coverage and zero unresolved rules. Cumulative wall time increased 539.080 seconds, peak RSS was 2,030,215,168 bytes, and native rule steps increased by 32. The [raw artifact](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0997_0999_ticks60_depth3.json) SHA-256 is `f505b7565a5cab06e1b989066f3576c2683566d81640393540ff1eb741dab027`; resource snapshot SHA-256 is `a39c7758fc576854e05086503ced137ffb1066f79ae39f5f4b2982fe1ee2c6e9`; native-rule-work SHA-256 is `5653c744485f3fb1d26a172989954d40e26282d40227c45d25ac3c8d5b54d4e0`. No invention-only generation-two checkpoint resulted.

**Loopover invention-only generation-two deeper follow-up (2026-10-24, draws 0980–0983):** A separate branch from the digest-valid g1 checkpoint used four distinct training goals, 15,000 attempts per goal, and 120 search ticks. All four tasks remained stuck and three new candidates received no qualification. It added 60,000 attempts to the parent snapshot's 20,000, for 80,000 under the 120,000 ceiling. One approval and one receipt were inherited, with no new approval, receipt, or checkpoint. Validation and held-out allocations were empty. Resource and native-rule-work digests verify with complete identity coverage and zero unresolved rules. Cumulative wall time increased 718.929 seconds, peak RSS was 2,029,752,320 bytes, and native rule steps increased by 44. The [raw artifact](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0980_0983_ticks120_depth3.json) SHA-256 is `918577599c88c5dc533eed0af99ba1e434522b01690e10c1674244ec74a6fbe6`; resource snapshot SHA-256 is `44fba4bedd15bbf3acfe1fd80b3068c7db78fc7067e580477e7b2202aa6eb607`; native-rule-work SHA-256 is `a05ec5525d9463030feaa135822abad9fae2b0becb90445e8cbb5aaa5c33e9e0`. No invention-only generation-two checkpoint resulted.

**Loopover invention-only g1 branch attempt audit (2026-10-24):** Across the g1 checkpoint's 20,000-attempt source run and nine completed restored proposal branches, recorded search work totals 520,000 attempts. The branch additions were 20,000, 40,000, 60,000, 100,000, 40,000, 60,000, 60,000, 60,000, and 60,000; each individual graph respected its 120,000 ceiling, with the 0016–0019 branch reaching that maximum including inherited work. A separate interrupted invalid-allocation preflight has no completed attempt record and is excluded. The aggregate is total development effort across restored graphs, not a single graph counter. No branch yielded an invention-only g2 checkpoint. This aggregate records actual search effort; every run remains subject to its own graph-wide ceiling, and none of these training-only panels is efficacy evidence.

**D4 invention-only generation-three second follow-up (2026-10-24, draws 0992–0993):** A second uncheckpointed branch from the immutable g2 checkpoint used two fresh, distinct training goals with 10,000 attempts each. Both tasks remained stuck and neither of the two new candidates qualified. The inherited malformed candidate `#9459` qualification remains rejected because its `kind` is missing. The branch added 20,000 attempts to the restored graph's 44,280-attempt counter (64,280 total under the configured 120,000 ceiling); it is separate from the 0924–0926 and 0989–0991 searches, which likewise produced no child checkpoint. Two approvals and two receipts were inherited; none were added, and no child checkpoint was created. Validation and held-out allocations are empty. Resource and native-rule-work digests verify with complete identity coverage and zero unresolved rules. Cumulative wall time rose 1,949.954 seconds, peak RSS was 3,123,765,248 bytes, and native rule steps rose by 33. The [raw artifact](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json) SHA-256 is `01efe7b4720f79f951190fbc2665aac92aa32f3aa1655efd9156b40eeb821ed1`; resource snapshot SHA-256 is `da20346083e36a2e589889205f4023ffbaad943610c69f30dc52418878e97a42`; native-rule-work SHA-256 is `9f0ca1b7203020979ebca99a980cdf13893fe3fc197b2b5d53cf62f98ded210c`. No improving g3 candidate resulted, and the draft/freeze disposition is unchanged.

**D4 invention-only generation-three follow-up (2026-10-24, draws 0989–0991):** A
fresh training-only branch restored the digest-valid g2 checkpoint and used
three globally unused pairwise-distinct goals, reserving 5,240 attempts per
task. All three tasks remained stuck and the three new candidates received no
independent-goal qualification. The inherited candidate `#9459` qualification
record remains malformed because its `kind` is missing; it was not accepted.
The branch added 15,720 attempts, taking the restored graph counter from 44,280
to 60,000 under the configured 120,000 ceiling. This is a separate
uncheckpointed branch from the earlier 0924–0926 search; the latter's attempts
are not embedded in the immutable parent checkpoint. It inherited two
approvals and two receipts, added none, and created no child checkpoint. There
were no validation worlds or held-out access. Resource and native-rule-work
digests verify, native-rule identity coverage is complete, and unresolved rule
count is zero. Cumulative wall time rose by 2,568.982 seconds, peak RSS was
3,244,118,016 bytes, and native rule steps rose by 45. The [raw artifact]
(../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0989_0991_ticks60_depth3.json)
SHA-256 is
`356b388fdae7d6ac7b64c97b6dd7776a6b0609ec04eddea8504e1fd7b861c266`; the
resource snapshot SHA-256 is
`bb12c2f52d8938bd3b19c9081bb044da7ff4eeda7743cff546ca99a41b0aeb82`, and the
native-rule-work SHA-256 is
`138483f4685927bfa5bccc9c12574848d231b4e470a606a234837beafbc9ccae`. No
qualified generation-three candidate resulted, so the draft and held-out gates
remain unchanged.

**Approved full-arm lineage updates (2026-10-25):** The exact D4 full-arm g1 candidate `#9440` and Loopover full-arm g0 candidate `#1611` requests described in the plan were approved with 12 reviewer-reported seconds each and consumed exactly once. They created D4 full-arm g2 and Loopover full-arm g1 checkpoints with verified receipts; six of the 12 required invention/full descendants remain. The raw outputs and hashes are in the plan and development ledger. These are training-only transitions. The 24-descendant manifest, shared per-field ceilings, final resource preflight and standalone freeze remain incomplete; do not use held-out worlds.

**D4 full-arm g2 P26 proposal continuation (2026-10-25):** Four fresh distinct training goals 0210–0213 were searched from the new full-arm g2 checkpoint with exact-effect deduplication, 10,000 discovery attempts and a 5,000-attempt transfer reserve per request. All tasks remained stuck; no reserve was used and no new candidate, qualification, approval, receipt or checkpoint resulted. The run added 40,000 attempts to the parent's 30,703, within its unchanged 120,000 graph ceiling. The resource snapshot and complete native-rule-work capture verify; the process peak is PID/timestamp attributed. This remains negative training-only search evidence. P22 is still `DRAFT — NOT FROZEN`, and held-out access remains closed.

**Loopover full-arm g1 P26 proposal continuation (2026-10-25):** Fresh distinct training goals 0214–0217 were searched from the new g1 checkpoint with the same fixed discovery/transfer reserve and exact-effect deduplication. All four tasks remained stuck. The branch added 55,000 attempts to 40,000 inherited attempts, for 95,000 under the unchanged 120,000 graph ceiling. Candidate `#51571` received 15,000 independent-goal trials, all residual, so it did not qualify and cannot be submitted for approval. No new approval, receipt or checkpoint was created. The resource and complete native-rule-work captures verify; process RSS is attributed. No validation or held-out worlds were accessed. The preregistration remains draft, and held-out access remains closed.

**Loopover full-arm g1 P26 follow-up search (2026-10-25):** A second branch from the same immutable g1 checkpoint searched fresh distinct goals 0218–0221. It added 60,000 reserved attempts to 40,000 inherited attempts, for 100,000 under the 120,000 graph ceiling. Candidates `#71577` and `#71671` received 20,000 independent-goal trials in total, all residual; neither qualified. No new approval, receipt or checkpoint was created, and validation/held-out allocations remained empty. Resource and native-rule-work digests verify with complete identity coverage and attributed process RSS. This remains negative training-only evidence; this file remains `DRAFT — NOT FROZEN` and held-out access remains closed.

**Loopover full-arm g1 second follow-up search (2026-10-25):** The third fresh-goal branch from this checkpoint searched 0222–0225, adding 55,000 reserved attempts to the 40,000-attempt parent total (95,000 under the 120,000 graph ceiling). Candidate `#81580` received 15,000 independent-goal trials, all residual, so it did not qualify. No approval, receipt or checkpoint was added. Resource and native-rule-work digests verify with complete identity coverage and attributed process RSS. Validation and held-out allocations remain empty; this file remains `DRAFT — NOT FROZEN`.

**Loopover full-arm g1 second follow-up search (2026-10-25):** The next fresh-goal branch searched 0222–0225 from the same g1 checkpoint, adding 55,000 reserved attempts to the 40,000-attempt parent total. Candidate `#81580` received 15,000 independent-goal trials, all residual, and did not qualify. No approval, receipt or checkpoint was added. Resource and native-rule-work digests verify, with complete native identity coverage and attributed process RSS. Validation and held-out allocations remain empty; this preregistration is still `DRAFT — NOT FROZEN`.

**Captured-checkpoint resource audit (2026-10-25):** The read-only auditor [`audit_p22_checkpoint_resources.py`](../../../scripts/audit_p22_checkpoint_resources.py) inspected eight registered roots, 12 passive descendants, and six approved invention/full descendants. It reports `PASS_PARTIAL_INCOMPLETE`: 26 distinct checkpoint IDs, valid checkpoint and resource-snapshot digests, all 20 registered resource fields measured for every checkpoint, and no issues. It reports observed minima/maxima and checkpoint identities for each field; these are provisional development ranges, not frozen ceilings. The [machine-readable audit](../../../evaluation/process_mastery/results/p22_checkpoint_resource_audit_20261025.json) SHA-256 is `1ed9933f0ae1b5769ea736c1d31e2fe2f82754c582427a5c9f852e82114d0a79`; it embeds SHA-256 identities for all nine source artifacts. The six missing invention/full descendants are D4 invention-only g3, D4 full g3, Loopover invention-only g2/g3, and Loopover full g2/g3. Per-field ceilings are not frozen, the isolated final wall-time panel is incomplete, and held-out access remains disallowed. Reproduce with `.venv/bin/python scripts/audit_p22_checkpoint_resources.py`; this audit is resource provenance only and does not satisfy the manifest, freeze, or efficacy gates.

**Supplementary isolated resource panel for the two later checkpoints (2026-10-25):** The reproducible runner [`run_p22_new_checkpoint_resource_panel.py`](../../../scripts/run_p22_new_checkpoint_resource_panel.py) filled the only checkpoint gap in the earlier 96-cell resource panel: D4 full-arm g2 `p22-d4-g2-2d2cb9ecda29` and Loopover full-arm g1 `p22-loopover-g1-c9f470ba1639`. It rescored each checkpoint in an isolated worker on the same four registered training worlds per family used by that prior panel (D4 0609–0612; Loopover 0622–0625), for 8/8 completed cells. All 20 resource fields were measured; all resource snapshots validate; all cells respected 600,000 cumulative primitive work and 20,000 rule-progress limits. Maximum isolated cell wall time was 28.563 seconds and maximum observed isolated-worker peak RSS was 3,518,881,792 bytes (Loopover g1, draw 0624). Maximum cumulative primitive work was 275,274 (D4 g2) and 192,295 (Loopover g1). Scores were 1/4 and 2/4 respectively; these reused-world training diagnostics are not efficacy evidence. No approval or receipt was added, and validation/held-out access remained false. Compressed [artifact](../../../evaluation/process_mastery/results/p22_resource_panel_new_approved_checkpoints_0609_0612_0622_0625.json.gz) SHA-256 `5683a2e475ec5f9821f9dc1df3cc02c743d928b66fb5eca6e0ff79d96362f6dc`. The six missing descendants still prevent the final complete panel, ceilings, manifest, freeze, and E2/E3.

**Supplementary resource panel refresh after Loopover approvals (2026-10-27):** The same runner now includes the two approved Loopover g2 checkpoints on registered Loopover training worlds 0622–0625, alongside a repeat measurement of the prior supplementary checkpoints. All 16 cells completed with 20/20 fields and valid snapshots; no approval/receipt events were added and validation/held-out access remained false. The [current manifest](../../../evaluation/process_mastery/results/p22_current_resource_manifest_20261025.json) now covers 28/32 checkpoints and 112 cells with zero issues. Four g3 descendants remain missing, so the resource ceilings/freeze and E2/E3 gates remain open. Supplement SHA-256 `b60d59c9b477f6709856bbeba54d2f05835224eb0ca9a3f421b0035f76f483b3`; manifest SHA-256 `ff0a7cff640b84cf710f2d5e47e09179b5948a30db16e0560b55c651c9671095`.

**Current captured-lineage resource manifest (2026-10-25):** The reproducible reconciliation script [`build_p22_current_resource_manifest.py`](../../../scripts/build_p22_current_resource_manifest.py) combines the digest-checked checkpoint audit, prior 96-cell panel, and eight-cell supplement. It verifies 104 completed isolated cells—four distinct training worlds per each of 26 captured checkpoints—with all 20 resource fields measured and all snapshot digests valid. For `wall_time_seconds`, ranges use the isolated worker time that the freeze preflight checks, not the cumulative runtime snapshot. Of 32 expected checkpoints (eight registered roots plus 24 descendants), it reports 26 captured (eight roots and 18 descendants), leaving six invention/full descendants. The manifest contains zero issues, zero approvals/receipts, and no validation or held-out access; it remains `PASS_PARTIAL_INCOMPLETE`, with final per-field ceilings still unfrozen. The machine-readable [manifest](../../../evaluation/process_mastery/results/p22_current_resource_manifest_20261025.json) SHA-256 is `b82e4e36d89861f081a46c93874a1edd053f2ef61a393adbb5176e09b05ac53c`. The artifact includes provisional per-field ceilings and per-checkpoint wall-time values under the ceiling derivation rule below; it is not the complete final manifest or efficacy panel.

**Pre-freeze resource-ceiling derivation rule (2026-10-25):** After all 32 checkpoints are present and the complete four-world-per-checkpoint common training resource panel passes, set each `checkpoint_wall_time_seconds[key]` to the maximum isolated worker wall time among that checkpoint's four cells. For each `RESOURCE_FIELDS` field, set the shared resource ceiling to the maximum measured value across all 32×4 cells, except `primitive_work` and `cumulative_primitive_work`, which remain at the already exercised shared ceiling of 600,000, and `native_rule_steps`, which remains at the registered 20,000 rule-progress limit. For the wall-time resource field, use isolated worker time, never cumulative lineage time. This no-margin rule is deterministic and makes no efficiency claim; any observed resource mismatch remains visible and precludes efficiency claims. If any final panel cell exceeds the fixed primitive/rule limits or lacks a measured field, do not freeze or access held-out worlds; retain it and complete preflight under a reviewed draft update. Current values in the partial manifest are provisional and must be recomputed from the complete panel before the standalone freeze.

**Current native runtime provenance recheck (2026-10-25):** `linear_p22_v1.provenance()` returned runtime attestation `ATTESTED`, `native_symbols_bound=true`, `build_sources_match=true`, and no issues. Current digests: runner `fb65b52691a51b0d258a5bed9ae916b322516f151a6a9df1282add22f4dcce4d`, analyzer `10dce1e6e0b23f7a1f100ad3c7120829ab5335bf87f792b2a08408f5c4122643`, source bundle `0d4cd15a5734e38e532bd1cf062b6996d2c080cca61ec51321952752b1e658ea`, dependency closure `a1a6e531f12703e2f0de0bdcf7632072fb85af10a28e7a5f704eaf726ae66a15`, loaded extension `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`, build receipt `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`, and build-source fingerprint `a525aa2d8ffcb430e1268c368cad6c97f59092e16b048ee397e73cc1a71e34e3`. This is a current mechanism/provenance check only; recompute the attestation after the complete manifest and before the standalone freeze, whose commit binding is still absent.

**Current P22 regression verification (2026-10-25):** The combined native runner, analyzer, resource accounting, development-probe CLI, isolated checkpoint panel, development adapter, arm, and four-arm integration test selection passed 79 tests in 267.02 seconds. Command: `.venv/bin/pytest -q tests/test_linear_p22_v1.py tests/test_analyze_linear_p22_v1.py tests/test_p22_resource_accounting.py tests/test_run_p22_development_probe_cli.py tests/test_p22_checkpoint_panel.py tests/test_p22_development.py tests/test_p22_arms.py tests/test_p22_four_arm_development.py`. This verifies regression coverage only; it does not complete the six missing descendants or authorize a freeze or held-out run.

**Loopover invention-only g2 proposal search (completed 2026-10-25; recorded 2026-10-26):** Continued from registered generation-one checkpoint `p22-loopover-g1-2638da0f23ae` (digest `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on fresh distinct training goals 0230–0233. Four tasks remained stuck. The restored graph reserved 75,000 attempts total, including 20,000 inherited and 55,000 new, below the 120,000 graph ceiling. Candidate `#31572` (expression digest `3c0a20692e54736e7a312e51e6ba8bed2251552fd4fd0258bacbfe4eb4394f4d`) received 15,000 independent-goal trials, all residual; it has no qualification. Candidates `#16551` and `#21555` had no independent-goal trials. The attempt projection covers 75,000 unique attempts (74,994 residual, six verified) across eight requests/eight tasks. No new approval, receipt, adoption, or child checkpoint was created; one approval and one receipt were inherited. Validation was empty and held-out access was not available to the runner. Resource snapshot `5659891479b93b7991a75731e2081a3cb5a2cae765b502517cf30054d9a1edd3` and native-rule-work snapshot `fb5ddc3ca70082f5465c39870960ea8d2c73b04cac3adee80b580a546a68d137` validate, with complete identity coverage and zero unresolved rules. The snapshot records 104 cumulative native rule steps, 1,748.355 seconds cumulative wall time and 2,030,084,096-byte peak RSS; that peak is attributed to PID `3113132` at Unix time `1792933082970182318`. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0230_0233_p26.json) SHA-256 `c83a58d06272532e261e0a332a069d23d4864e0cc9e6fbaeb3b1747ddb19c266`; [attempt projection](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_g2_0230_0233.json) SHA-256 `8297b13bfb058f920c8bab46f5ba9b3ad442cb502059d848da26cec05611677a`. This is negative training-only evidence; Loopover invention-only g2/g3 and P22 freeze/held-out gates remain open.

**Loopover full-arm g1 proposal search (completed 2026-10-25; recorded 2026-10-26):** Continued from registered full-arm generation-one checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) on fresh distinct training goals 0246–0249. Four tasks remained stuck. The restored graph reserved 95,000 attempts total, including 40,000 inherited and 55,000 new, below the 120,000 graph ceiling. New candidate `#51571` (digest `d41dcad91da32d852691c71b3957b34086fe3015ed3ec4df7b9adbb61d644d03`) received 15,000 independent-goal trials, all residual, and did not qualify. Inherited candidate `#16963` had no new qualification. The attempt projection covers 95,000 unique attempts (94,956 residual, 44 verified) across eight requests/eight tasks. One approval and one receipt are inherited; no new approval, receipt, adoption, or checkpoint was created. Validation was empty and held-out access was not available to the runner. Resource snapshot `714e828486c4d83f610739633826b810cf186090b5b8508d90fd3a82a2b140ec` and native-rule-work snapshot `122e5c764a6d2ec1eb85d42063e129f9b78b353f3ab3d93c9dfbe70e78926da3` validate, with complete identity coverage and zero unresolved rules. The snapshot records 128 cumulative native rule steps, 2,803.355 seconds cumulative wall time and 3,958,304,768-byte peak RSS, attributed to PID `3122448` at Unix time `1792933145775032795`. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0246_0249_p26.json) SHA-256 `0d228ddf4ab12467da7b64f024b26e8fd9803ef26808a18190bc905fcd55fb92`; [attempt projection](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g1_0246_0249.json) SHA-256 `61c28dcc21d5b633797c693d607170ded9864c13288afd7e9ad620fa34000d13`. This is negative training-only qualification evidence; Loopover full-arm g2/g3 and the P22 final panel/freeze/held-out gates remain open.

**Loopover full-arm g2 P26 continuation (completed 2026-10-26):** Continued from registered full-arm g1 checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) on fresh distinct training goals 0262–0265. The search graph contains 100,000 reserved attempts (40,000 inherited plus 60,000 new), below its 120,000-attempt ceiling; all four tasks remained stuck. New candidates `#71577` and `#81581` received 10,268 and 9,732 independent-goal trials, with zero qualifications; inherited candidate `#16963` received no new trials. No new approval, receipt, adoption, or checkpoint resulted; the graph's single approval and receipt are inherited. Validation and held-out allocations are empty. The 100,000-attempt read-only projection has unique attempt IDs, 99,958 residual and 42 verified attempts, and 8,997 distinct exact effects. Resource snapshot `ae70e0d2c8c25e99fb261cf1e956e923e490b38b5dbb4332a8acac0b628f14fb` and native-rule-work snapshot `8d24205e3e11a66420287145b1a9231173176e037cb6c6554583785dfd4630fc` both pass digest validation; native rule identity coverage is complete with zero unresolved rules. Cumulative accounting is 122 native rule steps, 2,802.964 seconds wall time, 3,958,513,664-byte peak RSS, and 467,288 declared primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0262_0265_p26.json) SHA-256 `ea41d9187e462bff479e8ac8d5ba20545171d96c18c24e5ae5f3e95f8a7440bc`; attempt projection SHA-256 `be80bf84f51822c855708c89b59a8bc9fc0ea5e9771d4f8b5d571352dbb43dff`. No new full-arm g2 descendant was created; the remaining lineage, resource-manifest, freeze, and held-out gates stay open.

**Loopover invention-only g2 P26 continuation (completed 2026-10-26):** Continued from registered invention-only g1 checkpoint `p22-loopover-g1-2638da0f23ae` (digest `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on fresh distinct training goals 0254–0257. The graph contains 80,000 reserved attempts (20,000 inherited plus 60,000 new), below the 120,000 ceiling; all tasks remained stuck. New candidates `#41575` and `#61582` received 10,268 and 9,732 independent-goal trials, respectively, with zero qualifications. No new approval, receipt, adoption, or checkpoint resulted; one approval and receipt are inherited. Validation and held-out allocations are empty. The 80,000-attempt read-only projection has unique IDs, 79,990 residual and 10 verified attempts, and 9,336 distinct exact effects. Resource snapshot `a6b14e21b6d185ad77bbf3bcfdc2f5d1c1b3e04f0db257aca6cbc016c9deda5f` and native-rule-work snapshot `9e28de7b310940c2a480a1a17587e8a45a837c468b63b6f65631e0d6bcc33f7e` both pass digest validation; native identity coverage is complete with zero unresolved rules. Cumulative accounting is 98 native rule steps, 1,936.115 seconds wall time, 2,030,542,848-byte peak RSS, and 412,716 declared primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0254_0257_p26.json) SHA-256 `fa9419bea42f86f318255f81380940743c2cf43558f8fdb6772bc0c2f2d7086b`; attempt projection SHA-256 `b3785cf4fb2d954d839260f6cf75d18c3960285d2ff1c7930c63d000d42df296`. No new invention-only g2 descendant was created; lineage, resource-manifest, freeze, and held-out gates remain open.

**D4 invention-only g3 proposal search from g2 (completed 2026-10-26):** Continued from registered g2 checkpoint `p22-d4-g2-84854777d0e3` (digest `d8a916474c8e3bafd44dda0082fd7c71ccb3dac1c0a2daf9bbe7f759c70fb4df`) on distinct training goals 0226–0229. All four tasks remained stuck. The attempt projection covers 87,808 unique attempts (44,280 inherited plus 43,528 new; below the 120,000-attempt ceiling), 76,717 residual and 11,091 verified attempts, and eight distinct exact effects. No eligible new candidate qualified. The inherited candidate `#9459` qualification remains excluded because its `kind` is missing; candidate `#25873` is identity and unqualified. No new approval, receipt, adoption or checkpoint resulted; the two approvals and receipts are inherited. Validation and held-out allocations are empty. Resource snapshot `97c240acb7b23618644b834aee3f8004271d53cc1aaa4a565ab627b86ca57059` and native-rule-work snapshot `0a2d1dbada6d016341403fe3a091a6e94f6a221e198bd1066c27979d480582b9` both pass digest validation, with complete rule identity coverage and zero unresolved rules. However, cumulative declared primitive work is 903,701, exceeding the fixed 600,000 ceiling; this branch cannot yield an admissible checkpoint or be used as freeze evidence. It records 258 cumulative native rule steps, 13,978.718 seconds cumulative wall time, and 3,130,994,688-byte peak RSS. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0226_0229_p26.json) SHA-256 `2323a7f35c49a521fc61537142373dae51ef9148064fcf978d94265b86cbe9f4`; attempt projection SHA-256 `271732166448e7eda88ecc1ef616f50bb1de9632d0cb03122a8c063014fdce26`. This negative branch adds no D4 invention-only g3 descendant; P22 resource and freeze gates remain open.

**Loopover full-arm g2 P26 continuation (2026-10-26, draws 0046–0049):** Four fresh distinct training goals were searched from registered full-arm g1 checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) using exact-effect deduplication, 10,000 discovery attempts plus a 5,000-attempt transfer reserve per request, 60 search ticks, and depth 3. All four tasks remained stuck. This branch added 55,000 attempts to 40,000 inherited attempts (95,000 total under the 120,000 ceiling); new attempts were 54,988 residual and 12 verified across 4,085 exact effects. Candidate `#61574` received 15,000 independent-goal trials without qualification; inherited candidate `#16963` received no new trials. One approval and receipt are inherited; no new approval, receipt, adoption, or checkpoint was created. Validation was empty and no held-out worlds were accessed. Resource snapshot `59ef781a5e97f5442c36e994d5b2df6808e7134d7bfd781037a5cb4159c9ad25` and native-rule-work snapshot `4d6862d6e044c6c1c41b662493a1c871b3712fc7c1bec2e9427e91040c531a0c` validate with complete rule identity coverage and zero unresolved rules. Cumulative declared primitive work was 420,826; the record shows 121 native rule steps, 2,519.922 seconds wall time, and 3,959,062,528-byte peak RSS. Raw result SHA-256 `407ab243f68737ed5ab8104e3eab22f75828508bd1ee8992bf75cc798f2c66d1`; read-only attempt projection SHA-256 `387f3993cca754461a34dd84d56682570fe12e65c0949aa8b4d750cd965ae0e5`. This negative training-only result creates no new checkpoint and does not change the preregistration or held-out disposition.

**Loopover full-arm g2 P26 follow-up (2026-10-26, draws 0038–0041):** A separate branch restored the same registered full-arm g1 checkpoint and searched four fresh distinct training goals with exact-effect deduplication and a fixed 10,000 discovery / 5,000 transfer-reserve split per request. All tasks stayed stuck. It added 55,000 attempts to 40,000 inherited attempts (95,000 total under the 120,000 ceiling); new attempts were 54,996 residual and four verified across 6,528 exact effects. New candidate `#51571` received 15,000 independent-goal trials with no qualification; inherited `#16963` received no new trials. One approval and receipt are inherited; no new approval, receipt, adoption, or checkpoint was added. Validation was empty and no held-out worlds were accessed. Resource snapshot `9a8478e8c1e6432be0810e8be7694b37b0269404a3d98db89a8f60e2595b3913` and native-rule-work snapshot `f6a812df36cc55332599fe3be4667c4d97a0736b6d28f66b398f257234eb88eb` validate with complete native identity coverage and zero unresolved rules. Cumulative declared primitive work was 536,820; the record shows 128 native rule steps, 2,810.279 seconds wall time, and 3,958,571,008-byte peak RSS. Raw result SHA-256 `1a7dc2c179db3ec2db942a8fab4775f487ac42df4fd4e21f5e28497c25f8dbf5`; read-only attempt projection SHA-256 `4ce854fe42f3a9f0fafbdf12afabc8fda953298a9573d48debac2d0ad55c5a14`. This is negative training-only evidence and leaves P22 lineage, freeze, and held-out gates unchanged.

**Loopover invention-only g2 P26 continuation (2026-10-26, draws 0042–0045):** Continued from the registered invention-only g1 checkpoint on four fresh distinct training goals with exact-effect deduplication and the fixed 10,000 discovery / 5,000 transfer-reserve split per request. All tasks remained stuck. The graph added 60,000 attempts to 20,000 inherited attempts (80,000 total below 120,000); new attempts were 59,990 residual and 10 verified across 6,914 exact effects. Candidates `#41575` and `#51579` received 10,268 and 9,732 independent-goal trials, respectively, without qualification. One approval and receipt are inherited; no new approval, receipt, adoption, or checkpoint was added. Validation was empty and no held-out worlds were accessed. Resource snapshot `40d370d186a1789561f9406a73ac1ed1d850084bcf54e9a89db35a466049a350` and native-rule-work snapshot `e63e6d31548f0dec07c248b09be7c74872612fcdde5cc740e4f06ebbe22d31f4` validate, with complete native identity coverage and zero unresolved rules. Cumulative declared primitive work was 402,984; the record shows 98 native rule steps, 1,962.978 seconds wall time, and 2,030,530,560-byte peak RSS. Raw result SHA-256 `b66fba3851bf6a6a0bb95fb84630944079ea543dfe5d08114797e7dfbb6c385c`; attempt-projection SHA-256 `43d5a7a13195d8a944af075d6af7e8c1e5f5710c3e630390bc0f9a66574a8ff8`. This is negative training-only evidence and leaves the Loopover g2 lineage gate open.

**Loopover invention-only g2 P26 follow-up (2026-10-26, draws 0054–0057):** A further branch from the same registered invention-only g1 checkpoint searched four fresh distinct training goals. It added 55,000 attempts to the parent's 20,000 (75,000 total under the 120,000 ceiling); new attempts were 54,991 residual and nine verified across 7,026 exact effects. Candidate `#31572` received 15,000 independent-goal trials without qualification; inherited `#16551` and `#21555` received no new trials. One approval and receipt are inherited; there was no new approval, receipt, adoption, or checkpoint. Validation was empty and no held-out worlds were accessed. Resource snapshot `d69a1598debb82e131c9d09b3b48728b1e3eaaafc298c22bab01fc48fc9a9be2` and native-rule-work snapshot `aa6fd6af9430bae3a6cdeaa974b1f80afed830c3d6ca417b523b6d161c8c8494` validate with complete native identity coverage and zero unresolved rules. Cumulative declared primitive work was 472,496; the record shows 104 native rule steps, 1,755.684 seconds wall time, and 2,030,764,032-byte peak RSS. Raw result SHA-256 `ac9c3babccbd4c62cd4e1b09a20742e23c9515114dd41d48899317820ba221f7`; attempt-projection SHA-256 `48c0e6459eb6df900e020553ef46fe7603f5e8aa4271432fae25efbe3ca7c029`. This is negative training-only evidence and leaves the Loopover invention-only g2 lineage gate open.

**Current P22 regression verification (2026-10-26):** Re-ran the prescribed combined runner/analyzer, resource accounting, proposal CLI, isolated checkpoint panel, development adapter, arm, and four-arm integration test selection. Command: `.venv/bin/pytest -q tests/test_linear_p22_v1.py tests/test_analyze_linear_p22_v1.py tests/test_p22_resource_accounting.py tests/test_run_p22_development_probe_cli.py tests/test_p22_checkpoint_panel.py tests/test_p22_development.py tests/test_p22_arms.py tests/test_p22_four_arm_development.py`. Result: 79 passed in 243.72 seconds. This is mechanism regression evidence only; the six missing descendants and final freeze/held-out gates remain open.

**P22 native runtime provenance refresh (2026-10-26):** Re-ran `evaluation.process_mastery.linear_p22_v1.provenance()` on the current checkout. Runtime attestation returned `ATTESTED`, with native symbols bound, build sources matching, and no issues. Wrapper SHA-256 `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`; loaded extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`; build receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`; build source fingerprint `a525aa2d8ffcb430e1268c368cad6c97f59092e16b048ee397e73cc1a71e34e3`. Runner/analyzer/source-bundle/dependency-closure hashes are unchanged at `fb65b52691a51b0d258a5bed9ae916b322516f151a6a9df1282add22f4dcce4d`, `10dce1e6e0b23f7a1f100ad3c7120829ab5335bf87f792b2a08408f5c4122643`, `0d4cd15a5734e38e532bd1cf062b6996d2c080cca61ec51321952752b1e658ea`, and `a1a6e531f12703e2f0de0bdcf7632072fb85af10a28e7a5f704eaf726ae66a15`. This confirms runtime provenance, not efficacy or the open P22 gates.

**Loopover invention-only g2 P26 continuation (2026-10-26, draws 0058–0061):** Continued from registered invention-only g1 checkpoint `p22-loopover-g1-2638da0f23ae` (digest `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on four fresh distinct training goals. The graph contains 75,000 reserved attempts (20,000 inherited plus 55,000 new), below the 120,000 ceiling; new attempts contain 54,997 residual and three verified attempts across 4,897 exact effects. Candidate `#51578` received 15,000 independent-goal trials with no qualification; candidates `#16551` and `#21555` received no new trials. One approval and receipt are inherited; no new approval, receipt, adoption, or checkpoint resulted. Validation and held-out allocations are empty. Resource snapshot `d53c16a4dd301f25ed1f760f544063c3636cad32274c2145864e55b932d796ad` and native-rule-work snapshot `759bffe1abdcb5872810578bf1a5d105f5e1b5e901a51ac9bdfc8653dde61368` pass digest validation with complete native identity coverage and zero unresolved rules. The record shows 97 cumulative native rule steps, 1,435.582 seconds cumulative wall time, 2,031,214,592-byte process peak RSS attributed to PID `3944454`, and 369,458 cumulative declared search primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0058_0061_p26.json) SHA-256 `50d681ecd22318a98f7ea421b979c0f64c9b401ba64dc17b546263588096c4b5`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_g1_0058_0061.json) SHA-256 `30a3d73b82090dc7c5b66b611efa35311a7f1bbddcdbe6a2c150aec0fe48f97c` covers all 75,000 unique attempt IDs. This negative training-only result yields no Loopover invention-only g2 checkpoint and leaves the lineage, manifest, freeze and held-out gates open.

**Loopover full-arm g1 P26 continuation (2026-10-26, draws 0062–0065):** Continued from registered full-arm g1 checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) on four fresh distinct training goals. The graph contains 100,000 reserved attempts (40,000 inherited plus 60,000 new), below the 120,000 ceiling; the new requests contain 59,984 residual and 16 verified attempts across 5,996 exact effects. New candidates `#61574` and `#81581` received 10,268 and 9,732 independent-goal trials, respectively, with no qualification. The attempt export has 100,000 unique IDs. One approval and receipt are inherited; no new approval, receipt, adoption, or checkpoint resulted. Validation and held-out allocations are empty. Resource snapshot `93b825ccc9cea631c86af108b9d3ceedb238425fd06e559c17234166ffc18811` and native-rule-work snapshot `fd396a2b1228fb4e254c14ad4a03cc6269c71a3ba995229389a6a5ce25805484` pass digest validation with complete native identity coverage and zero unresolved rules. The record shows 122 cumulative native rule steps, 2,664.770 seconds cumulative wall time, 3,958,333,440-byte process peak RSS attributed to PID `3946168`, and 467,288 cumulative declared search primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0062_0065_p26.json) SHA-256 `803b27aad5e80b87f5c34da3f52ce1927209cc40f4875ef770b84beceb7f5942`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g1_0062_0065.json) SHA-256 `871d8fe5dd81a145824dd7138a3e847a80ae465fba4a555cf7b39896e4eedd16`. This negative training-only search yields no Loopover full-arm g2 checkpoint and leaves the lineage, resource, freeze, and held-out gates open.

**D4 full-arm g2 P26 continuation (2026-10-26, draws 0242–0245):** Continued from the registered checkpoint `p22-d4-g2-2d2cb9ecda29` (digest `2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four fresh distinct training goals. The run used exact-effect deduplication, a 10,000-attempt discovery tranche plus 5,000-attempt transfer reserve per request, 60 search ticks, depth 3, and the unchanged 120,000 graph attempt ceiling. All goals remained stuck. The graph contains 73,349 reserved attempts (30,703 inherited plus 42,646 new); the four new requests contain 39,495 residual and 3,151 verified attempts across eight exact effects. Four surfaced candidates had zero qualifications; candidate `#52306` received 2,646 independent-goal trials without qualifying. The run inherits two approvals and two receipts, adding no approval, receipt, adoption, or checkpoint. Validation and held-out allocations are empty. Resource snapshot `6c7b1417994573ee931298db8d1131f756f5dd9e594985b9a330ae2919ac6b6f` and native-rule-work snapshot `29aa5dd2c12f6845b0044ae589f924d0aa8f01e1dbd3a6b3029e1e55d473ee92` pass digest validation with complete rule-identity coverage and zero unresolved rules. The snapshot records 231 cumulative native rule steps, 7,895.347 seconds cumulative wall time, 2,297,171,968-byte process peak RSS attributed to PID `3121560`, and 844,636 cumulative declared search primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0242_0245_p26.json) SHA-256 `2d966fe3aec5b7a18e63cb26e0c066e490d2bea031487d9c6908b072eb18bd92`; the read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0242_0245.json) SHA-256 `968a791c07fff900833937a3c6447aebf515589cac2d9d650c220de3781a8713` contains 73,349 unique attempt IDs. This is negative training-only search evidence; it yields no D4 full-arm g3 descendant and does not permit held-out access.

**D4 full-arm g2 P26 follow-up (2026-10-26, draws 0270–0273; reused allocation):** A separate branch restored the same g2 checkpoint and searched four distinct training goals, but these world IDs also appear in the earlier `p22_four_arm_v2_search_10000_8_d4.json` development artifact (which includes draws 0270–0277). They are not fresh goals for this continuation and this run must not support independent fresh-goal generalization claims. All stayed stuck. The graph contains 70,703 reserved attempts (30,703 inherited plus 40,000 new); the new requests contain 36,656 residual and 3,344 verified attempts across eight exact effects. No candidate qualified, and no new candidate, approval, receipt, adoption, or checkpoint was added; two approvals and receipts are inherited. Validation and held-out allocations are empty. Resource snapshot `8d27899cf4dcea68037932adfd64ae6d05d69cbad560e95786ae04c61e710157` and native-rule-work snapshot `b376b03bd87df83a2997fb14b9d3608cb60c41ad9f35197f94fec05c844bc038` validate with complete identity coverage and zero unresolved rules. The record shows 223 cumulative native rule steps, 7,765.597 seconds cumulative wall time, 2,297,221,120-byte process peak RSS attributed to PID `3181191`, and 791,003 cumulative declared search primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_full_g2_0270_0273_p26.json) SHA-256 `854e1bce991e52fea61a1a4aa910e2b07a0677c88c7b7c06662b59a437930203`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_full_g2_0270_0273.json) SHA-256 `9519d0387103d78c6cdc3b9797847d78a501708dc719f45aaa84c69602041708` contains 70,703 unique attempt IDs. Preserve this as a reused-world negative search record only; it yields no admissible fresh-goal evidence or D4 full-arm g3 descendant.

**Loopover invention-only g2 P26 continuation (completed 2026-10-26, draws 0066–0069):** Continued from registered invention-only g1 checkpoint `p22-loopover-g1-2638da0f23ae` (digest `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on four distinct training goals. All tasks remained stuck. The graph contains 75,000 reserved attempts (20,000 inherited plus 55,000 new), below the 120,000 ceiling. New candidate `#31572` (expression digest `1e9935b5a6109e5e28a477e091986a74c42cd10803c7dd5f709f19ab5dc792e2`) received 15,000 independent-goal trials, all residual, with no qualification; inherited candidates `#16551` and `#21555` received no new trials. The read-only attempt export contains 75,000 unique IDs; 55,000 new attempts include 54,998 residual and two verified attempts across 7,315 exact effects. One approval and receipt are inherited; no new approval, receipt, adoption, or checkpoint resulted. Validation is empty and held-out allocation is empty. Resource snapshot `1345040ce00ab2213df67ffabbdb18b2a7251f1f83a9334b3e6f1534bc40496f` and native-rule-work snapshot `fb5ddc3ca70082f5465c39870960ea8d2c73b04cac3adee80b580a546a68d137` validate with complete native identity coverage and zero unresolved rules. The run records 104 cumulative native rule steps, 1,560.839 seconds wall time, 2,030,526,464-byte peak RSS attributed to PID `4058952`, and 472,496 cumulative declared search primitive work. Raw result SHA-256 `82082c3b746e0632b76d3cfd9cecf96f1781189aff77c1e77940371b0a3b27d6`; read-only attempt export SHA-256 `4f266d84565befbe6b0217fdaa1e79b86af5fcb5b8d1e244b7ff2250476c4518`. This negative training-only search creates no Loopover invention-only g2 descendant; the lineage, resource, freeze, and held-out gates remain open.


**D4 full-arm g2 P26 continuation (2026-10-26, draws 0332–0335):** From approved checkpoint `p22-d4-g2-2d2cb9ecda29`, four distinct training-only requests added 40,000 attempts to the 30,703-attempt parent (70,703 total below the 120,000 ceiling). Each request was capped at 10,000 discovery attempts plus a 5,000 transfer reserve, with 60 ticks, depth 3, and exact-effect deduplication. All four tasks remained stuck; across the full graph, 65,361 attempts were residual and 5,342 verified, covering eight exact effects. The inherited candidate `#9440` received 222 independent-goal trials without qualification; new candidates `#4022`, `#6521`, and `#22382` did not qualify. Two approvals and receipts were inherited; no new approval, receipt, adoption, or checkpoint was created. Validation and held-out allocations were empty. Resource and native-rule-work snapshots validate (`979d1ddb31b50b8962aaf382102c50967c94d1bb98d64311f5300b60710f3475`, `ed642370ef1a61971e6c0c85763cc5e8c0966d36eb0a1301e1ed584f55b99242`); native rule identity coverage is complete with zero unresolved rules. The run records 223 cumulative native rule steps, 6,376.397 seconds cumulative wall time, 2,297,171,968-byte peak RSS, and 813,919 cumulative primitive work. Raw result SHA-256 `f2a9c7d5e351d05fe48f1e12dbe5e09a7568ff4c92f6745a26fd2d13e8ba67ed`; read-only 70,703-attempt export SHA-256 `9c358accdc4b574a9381fe4403ed86de6cb71d46b233017583a8708ecf7a51f4`. No D4 full-arm g3 descendant was produced, and this draft remains unfrozen with held-out access closed.


**Loopover full-arm g1 P26 continuation (2026-10-26, draws 0070–0073):** Continued from `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) on four distinct unused training goals. The graph reserved 95,000 attempts (40,000 inherited and 55,000 new), under the 120,000 ceiling; 94,962 attempts were residual and 38 verified, across 7,734 exact effects. Candidate `#1611` received 16,236 independent-goal trials without qualifying; candidate `#81580` (digest `0d4c9132d822c21db40d419ec855066d1749d645632634a445ecd375fe81d18f`) received 15,000 without qualifying. All tasks remained stuck. One approval and one receipt are inherited; no new approval, receipt, adoption or checkpoint was produced. Validation and held-out allocations are empty. Resource snapshot `dcba509202506790e99450e68c0066a3a791a973b2828f6fadc55e57894d26ff` and native-rule-work snapshot `18c22f5b27b34b1c02ec56bf4484274698042f1b310b1385a9d19337eac14963` validate with complete native-rule identity coverage and no unresolved rules. The run records 121 cumulative native rule steps, 2,414.152 seconds wall time, 3,958,398,976-byte process peak RSS, and 450,798 cumulative primitive work. Raw result SHA-256 `3fd7ad5c85daa21d701e31af3d61cb7903be2a91f626486d977429872cb6dcde`; the read-only export SHA-256 `254f10bb287d232048433556c5099aa47a85bc5a8559ed11612a2732b0eec77a` covers 95,000 unique attempts. No Loopover full-arm g2 descendant was created; this draft remains unfrozen and held-out access remains closed.


**Loopover invention-only g1 P26 continuation (2026-10-26, draws 0074–0077):** Continued from `p22-loopover-g1-2638da0f23ae` (digest `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on four distinct training goals. The graph reserved 75,000 attempts (20,000 inherited and 55,000 new), below the 120,000 ceiling; 74,995 attempts were residual and five verified, across 7,153 exact effects. New candidate `#61581` and inherited candidate `#6542` received 15,000 independent-goal trials each without qualifying; inherited candidates `#16551` and `#21555` received no new trials. All tasks stayed stuck. The one approval and receipt are inherited; no new approval, receipt, adoption or checkpoint was produced. Validation and held-out allocations are empty. Resource snapshot `7128003490c4c0550f986078b98ec58c5722aab795e5abc57c98936504ac00de` and native-rule-work snapshot `4bbe0d7a9587b0cb82892939e838c61b22012145fe47aed788740acf80aa48f0` validate with complete native-rule identity coverage and no unresolved rules. The run records 97 cumulative native rule steps, 1,454.273 seconds wall time, 2,030,338,048-byte process peak RSS, and 384,458 cumulative primitive work. Raw result SHA-256 `81ecc07f4eca0d97d26c45b3cd14cab48b422c13170e640bfb5f6f21b077e95b`; the read-only 75,000-attempt export SHA-256 `19bd99939c1baeb062a239d051c964c2d1ad5cceb8a1a296c4fc7fa73ea0dcf5`. No Loopover invention-only g2 descendant was produced; this draft remains unfrozen and held-out access remains closed.


**Loopover full-arm g1 continuation, draws 0078–0081 (2026-10-26):** The registered g1 checkpoint was continued on four distinct training goals. All tasks stayed stuck; inherited candidate `#1611` (16,236 independent-goal trials) and new candidate `#51571` (15,000 trials) did not qualify. The 95,000-attempt graph and unique-ID export, complete native-rule identity coverage, and resource digests are recorded in the canonical build-plan ledger. No new approval, receipt, adoption, checkpoint, validation, or held-out allocation occurred. This is a negative training result only; it does not satisfy a lineage descendant, freeze, or held-out requirement.


**Loopover invention-only g1 continuation, draws 0082–0085 (2026-10-26):** The registered g1 checkpoint was continued on four distinct training goals. All tasks stayed stuck; candidate `#31572` received 15,000 residual independent-goal trials and inherited candidate `#6542` received 15,000 trials, including two verified attempts. Neither qualified. The 75,000-attempt graph and unique-ID export, complete native-rule identity coverage, and resource digests are recorded in the canonical build-plan ledger. No new approval, receipt, adoption, checkpoint, validation, or held-out allocation occurred. This negative training result does not satisfy a lineage descendant, freeze, or held-out requirement.


**Loopover invention-only g1 continuation, draws 0086–0089 (2026-10-26):** The registered g1 checkpoint continued on four distinct training goals. All tasks stayed stuck; inherited candidate `#6542` had 15,000 independent-goal trials and new candidates `#41575`, `#51579`, and `#61583` had 7,634, 7,366, and 5,000 trials, respectively. No candidate qualified. The 80,000-attempt graph and unique-ID export, complete native-rule identity coverage, and resource digests are recorded in the canonical build-plan ledger. No new approval, receipt, adoption, checkpoint, validation, or held-out allocation occurred. This negative training result does not satisfy a lineage descendant, freeze, or held-out requirement.


**Loopover full-arm g1 continuation, draws 0090–0093 (2026-10-26):** The registered g1 checkpoint was continued on four distinct training goals. All tasks remained stuck. New candidate `#51571` qualified once on distinct training worlds 0090/0092 and remains unapproved; its exact replay is underway. The 95,000-attempt graph and unique-ID export, complete native-rule identity coverage, and resource digests are recorded in the canonical build-plan ledger. No new approval, receipt, adoption, checkpoint, validation, or held-out allocation occurred. The qualification does not yet create a lineage descendant or authorize a transition.


**D4 invention-only g3 over-ceiling follow-up (2026-10-26, draws 0266–0269):** The approved invention-only g2 checkpoint was continued on four fresh distinct training worlds. The graph contains 86,926 reserved attempts (44,280 inherited, 42,646 new); all new tasks stayed stuck. The attempt projection has 86,926 unique IDs, 75,402 residual and 11,524 verified attempts across eight exact effects. No new candidate qualified: inherited `#9459` still has malformed qualification `#15845` with missing `kind`, and identity candidate `#25873` remained unqualified after 2,646 trials. No approval, receipt, adoption or checkpoint was added. Resource snapshot `70895697c1b8ef96edf3d6ecb4daff3feacf2955bf9e9e5ec6779cdf8f3a2341` and native-rule-work snapshot `97ab077732dd6c96be0bcc6e3610b8245cdac5b97bd2629fb85547eee9c0ba65` validate with complete native identity coverage. The 916,444 cumulative declared primitive work exceeds the fixed 600,000 ceiling, excluding this branch from admissible checkpoint and freeze evidence. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0266_0269_p26.json) SHA-256 `0a347e82b43f0efb2323d07fa833153b0bd628d2a62f27fb487c9c8420a93d95`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_g2_0266_0269.json) SHA-256 `193ff9ef1116a59e819aa36d444c53655dc1e1e9eeefd4d010fa181d2dee38a3`. No validation or held-out worlds were accessed; P22 remains unfrozen.


**Loopover full-arm g1 continuation (2026-10-26, draws 0102–0105):** Continued from registered g1 checkpoint `p22-loopover-g1-c9f470ba1639` on four distinct training worlds. The graph contains 100,000 attempts (40,000 inherited, 60,000 new), below its 120,000 ceiling; all new tasks remained stuck. Candidates `#61574`, `#71578`, and `#81582` received 7,634, 7,366, and 5,000 independent-goal trials without qualification. The export has 100,000 unique attempt IDs, 99,953 residual and 47 verified attempts across 8,463 exact effects. No new approval, receipt, adoption or checkpoint resulted; validation and held-out allocations are empty. Resource snapshot `de2683ed5f5055226ed3530f25062389dd0b3c4d3d4d68b745f129989f47a5e6` and native-rule-work snapshot `c574013ec8ad51ace10a4b123c0fddd00a2937b676f94fc88ac265f0fea7b0e1` validate with complete rule identity coverage. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0102_0105_p26.json) SHA-256 `8ec526d0b23ee759e9581eef73c047693e7636c045ea3af45a9b629efeb0ed59`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g1_0102_0105.json) SHA-256 `daa619e1848afcdf18118e59f3e16b3303a0a9ad572ef038b10cf618b4ad81fb`. This negative training result creates no g2 descendant; P22 remains unfrozen and held-out access closed.

**Loopover invention-only g1 continuation (2026-10-26, draws 0106–0109):** Continued from registered invention-only g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four distinct training worlds. The graph contains 75,000 attempts (20,000 inherited, 55,000 new), below its 120,000 ceiling; all new tasks remained stuck. Candidate `#31572` received 15,000 independent-goal trials without qualification. The attempt export has 75,000 unique IDs, 74,993 residual and seven verified attempts across 9,361 exact effects. No new approval, receipt, adoption or checkpoint resulted; validation and held-out allocations are empty. Resource snapshot `10b67518726ac37d937000a589a5b12247d8184dd4913225bb2dc9f09b05b413` and native-rule-work snapshot `13162d66595a86920af9748722c03e86326019b61b20e6c3e9ca1992e10603d7` validate with complete native identity coverage. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0106_0109_p26.json) SHA-256 `c02bcef1c1d6c795c167d3d5e9198e5e6430575053205c5900e8efa03f1b1fb3`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_g1_0106_0109.json) SHA-256 `ff3b58eee4635d3a154aa83efb90bcc5271c6342cdbadcc300fb76dcba979039`. This negative training result creates no invention-only g2 descendant; P22 remains unfrozen and held-out access closed.


**Loopover full-arm g1 continuation (2026-10-26, draws 0110–0113):** Continued from registered g1 checkpoint `p22-loopover-g1-c9f470ba1639` on four distinct training worlds. The graph contains 95,000 attempts (40,000 inherited, 55,000 new), below its 120,000 ceiling; all new tasks remained stuck. Branch-local candidate `#51571` (expression digest `6591e9d96396fd54161365fc3b6cca83308c75d8f7bdfa90cff1debe5332b00c`) received 15,000 independent-goal trials without qualification; this is distinct from the separately bound candidate with the same local ID in draws 0090–0093. The export has 95,000 unique attempt IDs, 94,951 residual and 49 verified attempts across 9,041 exact effects. No new approval, receipt, adoption or checkpoint resulted; validation and held-out allocations are empty. Resource snapshot `9c2495491eda384031fa786739b325dc599482799fc78d4acb053ecc8173b9c0` and native-rule-work snapshot `9900142f0c8b57fc86fa02fc1dd93c5457b6d49a46d04ff9207f5458cdc07e92` validate with complete native identity coverage. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0110_0113_p26.json) SHA-256 `5551183edcfa219e5009b6ea9c0f374418894f34cbcbd092a8c22483cf43a0cd`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g1_0110_0113.json) SHA-256 `c7a07c4f81a412e2011952f3b9b40e11a0d1778b40628af51dda90b3dfd720fd`. This negative training result creates no g2 descendant; P22 remains unfrozen and held-out access closed.


**Loopover invention-only g1 continuation (2026-10-26, draws 0114–0117):** Continued from the registered g1 checkpoint on four distinct training worlds. The graph contains 75,000 attempts (20,000 inherited, 55,000 new), below its 120,000 ceiling; all new tasks remained stuck. Branch-local candidate `#31572` (digest `7fb1f08e6ac6412d271feffcea1bfdec32dd3a484ecfaf42c13fa6a7a681a3ce`) qualified as `#76587`, `independent_goal_composition`, on worlds 0114 and 0115. Its non-identity effect is absent from the 12 active parent effects. The export has 75,000 unique IDs, 74,991 residual and nine verified attempts across 9,439 exact effects. No new approval, receipt, adoption or checkpoint resulted; validation and held-out allocations are empty. Resource snapshot `386ef3c630c1c7f7833f5f40d39870c5cde7d0147a9b7945b0d897c53a892c84` and native-rule-work snapshot `11843052425f0b08e51bb6d1a35e372e92d283dcecb8924c17f06143c239a7f9` validate with complete native identity coverage. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0114_0117_p26.json) SHA-256 `bc68b6ba331ce4849154f934289ab7f27c7c87e774598aaa572f0ce16c298a22`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_g1_0114_0117.json) SHA-256 `21e6dc99125665ead20ff51522995d0929093837bd540bac06d0113571fcac1f`. Exact replay completed with matching candidate digest, effect, qualification `#76587`, witnesses 0114/0115, and byte-identical 75,000-attempt exports. Replay raw SHA-256 is `06b781b1349a9df53bdde85a6f17cdc7ca411804800498dddf8f365dbe5b64fa`; shared attempt-export SHA-256 is `21e6dc99125665ead20ff51522995d0929093837bd540bac06d0113571fcac1f`. Source/replay resource and native-work digests validate with complete identity coverage and zero unresolved rules. Candidate-specific request [`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_INVENTION_G1_0114_0117.md`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_INVENTION_G1_0114_0117.md) is awaiting exact approval; no action or checkpoint exists. P22 remains unfrozen and held-out access closed.

**Loopover invention-only g1 continuation (2026-10-26, draws 0118–0121):** Continued from the same registered g1 checkpoint on four fresh distinct training worlds. The graph contains 75,000 attempts (20,000 inherited, 55,000 new), below its 120,000 ceiling; all new tasks remained stuck. Branch-local candidate `#31572` (digest `6a8aa48a317d8d59d53e3b9616caeb9c4af49eb17fb66a9e998ca808b60d3539`) received 15,000 independent-goal trials without qualification; inherited candidates `#16551` and `#21555` received no new trials. This local ID is distinct by digest from the candidate in 0114–0117. The export has 75,000 unique IDs, 74,971 residual and 29 verified attempts across 8,294 exact effects. No new approval, receipt, adoption or checkpoint resulted; validation and held-out allocations are empty. Resource snapshot `95d47c27a966ffdd1ab0e01d5d79df895d857980b49c3fd5aec9a2b142be7ada` and native-rule-work snapshot `9b549921198cb98f5213ecfea666277aefd4df0aef6f808434bc9c015a445a4d` validate with complete native identity coverage. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0118_0121_p26.json) SHA-256 `10390a57a511f1e750d67174eb44872e68bb01dbb0639708bf5ec6f351d79c48`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_g1_0118_0121.json) SHA-256 `9f96a04ebce69f2f73c15fe4acd834270832f5bb5bf2c6e69456768c4c2649ec`. This negative training result creates no invention-only g2 descendant; P22 remains unfrozen and held-out access closed.

**Current P22 regression verification repeat (2026-10-26):** Re-ran `.venv/bin/pytest -q tests/test_linear_p22_v1.py tests/test_analyze_linear_p22_v1.py tests/test_p22_resource_accounting.py tests/test_run_p22_development_probe_cli.py tests/test_p22_checkpoint_panel.py tests/test_p22_development.py tests/test_p22_arms.py tests/test_p22_four_arm_development.py`; 79 tests passed in 262.03 seconds. This verifies current mechanism regression only and does not resolve the six missing descendants or authorize freeze/held-out execution.

**D4 full-arm g2 restored proposal branches (2026-10-26):** Two training-only continuations from checkpoint digest `2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123` searched distinct four-world sets 0350/0355/0358/0365 and 0370/0375/0378/0385. Each graph contains 70,703 unique attempts (30,703 inherited, 40,000 new), four stuck tasks and three recorded candidates with zero qualifications. Candidates `#4022` and `#6521` each received six independent-goal trials; `#22382` received none. Both exports are training-only; there were no new approvals, receipts, adoptions or checkpoints, and validation/held-out allocations are empty. Resource snapshot digests validate; native-work snapshots validate with complete identity coverage and no unresolved rules. Cumulative declared primitive work is 800,015 and 818,886. Raw result/export SHA-256 pairs are `f9780a926a83dcf2b9e207cb6a810cb65b42696129448700147c43b251915863` / `c52639ce079fa79d803017f2042170ecc39fd798fd87dab6df38b4dc47ce9bd5` and `a2b77c03760810d094d2704db384302b88602c7449476d9c58aaa3f3e9d6d9bc` / `a257d10e69ea19d27bc7ea964660c2634130137d40704426763518a3af2272e4`. Resource/native-work digest pairs are `44b58b5aa8991e6a865afc98cb67a50d5e0fd24f5e13788604112d700d5ef178` / `9f04619005e89fe67eef0f3aadff6b7883c4ec4b92d2a6b899b6c217b1ff0e32` and `29d11bdcd0cd5c42bc1913c7617f3637910932d4ea63ffc1dde9d217367c9046` / `f11d2c2ae3d86e0d2e7e7fe6dd4a58893aee4235ab5f25d160478d0c6b372e84`. No D4 full-arm g3 checkpoint resulted.

**D4 invention-only g2 continuation (2026-10-26, draws 0340–0343):** Continued from digest-valid checkpoint `p22-d4-g2-84854777d0e3` on four distinct training goals. The graph contains 87,808 unique attempt IDs (44,280 inherited and 43,528 new); all tasks remained stuck. No new candidate qualified: `#25873` has the identity effect after 3,528 independent-goal trials, `#9456` received six without qualification, and `#12174`/`#79409` received no new trials. Inherited `#9459` qualification `#15845` remains invalid because its kind is missing. No new approval, receipt, adoption or checkpoint resulted; validation and held-out allocations are empty. Resource/native-work snapshots validate with complete native identity coverage and zero unresolved rules. Cumulative primitive work is 906,970; wall time 14,765.366 seconds; peak RSS 3,250,769,920 bytes (PID `4074142`). Raw result SHA-256 `5318217c199603bde00295a6b9349e69d0310a335a084d6f16962c3293bf6596`; attempt export SHA-256 `a978cbd84b30c651625def055955c88083a2baa041e05d7bb340d06dbcb75a25`; resource snapshot `e684479c5ed1a8c4134ce87b93e7d5f1af889843260ba41747c78301bdce1f79`; native-work snapshot `65a35da9fe36eb42d6e80d1cff0b819b358858de5f381df46422f6fc92162ce9`. No D4 invention-only g3 descendant resulted.

**P22 development log update (2026-10-28):** Seven generation-two training-only continuation searches across D4 and Loopover arms completed with no new qualification, adoption or checkpoint. No validation or held-out allocation was made. The plan records exact compressed artifact hashes and per-run resource totals; the four-arm development log records the draw sets and outcome. These searches do not amend preregistered thresholds, ceilings or held-out conditions.

**Training search log (2026-10-28):** Two further full-arm g2 searches (Loopover 0200–0203; D4 0912–0915) completed without qualifying candidates. Both were training-only and made no validation or held-out allocation; exact resource snapshots and compressed artifact hashes are recorded in the canonical plan. No thresholds or freeze conditions changed.

**Training search log (2026-10-28):** Loopover full-arm draws 0204–0207 reproduced the previous two unqualified candidate effects and produced no checkpoint. No validation or held-out allocation occurred; see the canonical plan for artifact hashes.
