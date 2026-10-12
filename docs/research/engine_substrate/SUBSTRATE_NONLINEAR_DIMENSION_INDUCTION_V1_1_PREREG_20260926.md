# Nonlinear dimension-induction gate v1.1 — amended preregistration

**Amendment v1.1 (before confirmatory execution):** v1 capture is preserved as a failed harness attempt. It serialized each observation signature as a JSON string, but production `shape_decode_loop` consumes a structured list. The corrected runner passes the structured signature and residual list directly. v1 produced 60/60 ordinary `minted` outcomes, including all 10 linear positive controls, so its capture is inadmissible and supports no capability conclusion.

**Status: v1.1 amended protocol; execution not yet started.** The substrate learns geometric transforms between whole signatures, so v1 operationalizes transfer as a seeded training shape and a structurally distinct seeded transfer shape. It does not claim supervised function learning from labeled scalar examples. Before running, the runner emits a lock containing hashes of this protocol, runner/analyzer, relevant Rust/Python source, native extension/build manifest, and all generated inputs. Changes after lock require a versioned amendment.

## Question and estimand

Can the production observation-to-decode path acquire a previously unavailable transformation from one whole-shape transition, mint/adopt it as reusable structure, and transfer it to a distinct shape whose transformed target is withheld until after acquisition?

The primary outcome is the count of nonlinear task families with a proposed new operator that is independently correct on every held-out row and subsequently reused. Recognition, a low residual, a fitted training decomposition, or application of a preinstalled operator alone do not count as induction.

## Task families

Use integer 2-D points and a typed relation signature with stable point identity. For each family/replicate, seed one six-relation training base shape and one six-relation structurally distinct transfer base shape. Show only the transformed training signature in the first observation; then observe the transformed transfer signature after recording the acquired codebook. The transfer target is generated and locked before execution but is not inserted until this second stage:

1. **Linear positive control:** `T(x,y)=(x+y, 2y)`; verifies the existing matrix-induction route.
2. **Quadratic shear:** `T(x,y)=(x+y², y)`; the target is nonlinear and not representable by one 2×2 integer matrix over the complete schedule.
3. **Piecewise control:** `T(x,y)=(x+max(y−1,0), y)`; tests a simple branch boundary and is not in the current held operator set.

The exact train and transfer point schedules are fixed in the runner and expanded by replicate-specific identities. Assert before execution that both nonlinear training transitions are not reproduced by any 2×2 integer matrix in the registered finite search envelope. If the assertion fails, stop and amend before running; do not silently regenerate. This is an operator-transfer test with finite geometric fixtures, not conventional train/test sampling from a natural distribution.

## Arms

- **Production induction:** current full observation/closure/decode route and current configured learner.
- **Frozen/no-induction:** same route with all acquisition/mint rules disabled or tombstoned; verifies the gain depends on acquisition.
- **Linear positive control:** run the linear family through production induction in every replicate.

Use ten fresh substrate instances per family × arm. Randomize execution order from the published seed. Both shapes are seeded as prior structure, but only the transformed training shape is observed before acquisition state is recorded. Then observe the transformed transfer shape and measure recognition, residual, mint, and reuse. The frozen arm receives the same bases and observations with GenInfer disabled. Held-operator application is covered by separate codebook-ablation evidence and is not represented as a new arm in this induction test.

## Outcomes and resource measures

For every training and transfer call, record route/rung, candidate class and representation, residual dimensions/transforms, refusal status, graph delta, mint/adoption event, codebook before/after, exact observed signature, closure rounds/candidate counters where available, wall and CPU time, peak RSS, and errors. Independently apply every newly minted matrix to the transfer base and compare identity-aligned outputs with the locked target. Score the observed transfer route and exact map prediction separately.

Classify each production-induction outcome as:

- **Induced and transferred:** a new operator was proposed and adopted; its independent application to the transfer base exactly matches the locked target, and production decode recognizes the transfer observation.
- **Induced but invalid:** a new operator was proposed/adopted but its independent transfer prediction or production transfer route is wrong.
- **Residual/refusal:** no candidate was adopted; preserve the exact status and reason.
- **Held structure only:** the held-operator arm succeeds without acquisition; never credit this to induction.
- **False explanation:** training is marked explained/recognized but independent held-out predictions fail.

Report family-level counts and Wilson intervals, paired differences by arm, candidate/search bounds, median/p90/max latency, and per-process peak RSS. Do not pool the three families into a general nonlinear-learning rate.

## Integrity and admission gates

Admit the run only if all generated schedules, point identities, target values, and train/holdout partitions match the lock; every process starts from a fresh substrate; no holdout leaks into training or codebook construction; independent scoring agrees with the target on a separate hand-checked sample; graph deltas identify the exact operator mint; and repeats are semantically deterministic. The linear positive control must reproduce current matrix induction. The held-operator arm must be reported separately from all acquired structure. Any unmet integrity gate makes the run inconclusive, not negative evidence.

## Claim boundary

A positive result would establish induction/transfer only for the tested representations and families. A negative result would show that this configured production route did not induce these targets under the registered budget; it would not establish impossibility for the substrate or all learning routes. Neither result answers general intelligence or natural-task prevalence.

## Reproduction

The v1.1 source lock records the corrected runner/analyzer and generated schedules. Run the probe once with `--lock`, inspect and preserve the generated lock, then rerun without that flag. The independent analyzer checks factorial completeness, the nonlinear-vs-linear controls, minted operator transfer predictions, and the source lock. Record implementation/harness failures as versioned amendments; do not silently alter the protocol or reuse failed workers as fresh replicates.
