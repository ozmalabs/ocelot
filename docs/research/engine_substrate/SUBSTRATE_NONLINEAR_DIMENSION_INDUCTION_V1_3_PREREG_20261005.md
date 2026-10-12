# Nonlinear dimension induction current-source extension v1.3

## Question

Does the current production observation/decode route induce and reuse a coupled two-coordinate nonlinear transform that lies outside its 2×2 integer-linear operator family, when trained on one whole-shape transition and transferred to a distinct shape?

## Locked families and protocol

Run ten fresh substrates per family and arm, for 40 independent cases total. Retain the existing six-point train/transfer schedules and typed identity-bearing shape signature:

- Positive control: `T(x,y)=(x+y,2y)`.
- New coupled-quadratic family: `T(x,y)=(x+xy,y+x²)`.

The coupled family uses an interaction term and a quadratic term in a different coordinate; it is not either previously measured one-coordinate quadratic shear `x+y²` or piecewise shear `x+max(y−1,0)`. Before execution, lock generated training and transfer signatures and exhaustively verify that no 2×2 integer matrix in the runner's finite bound fits either signature set. If the preflight fails, stop before capture.

Cross the two families with:

1. Production induction enabled.
2. The same full route with acquisition/mint disabled or tombstoned.

Randomize all cases under a fixed published seed. For each training and transfer stage, record status, residual, quanta added, generators before/after, closure time, graph size, and errors. Independently apply each newly minted linear generator to the transfer base by stable point identity. Keep production recognition and independent exact-transfer prediction separate.

## Gates

1. Lock preregistration, runner, analyzer, current source/build/native inputs, and generated case schedule before execution; recheck source/native stability after capture.
2. Require ten replicates per family × arm, fresh substrate instances, exact schedule and train/transfer partitions, no duplicates, and finite positive timings.
3. Require both positive-control train and transfer recognition and exact matrix `[1,1,0,2]` in all ten enabled linear cases; require frozen controls not to mint new linear generators.
4. Require independent linear-fit preflight to reject the coupled-quadratic family on both registered signatures for every replicate.
5. Report nonlinear acquisition, transfer prediction, recognition, refusal, quanta, and closure cost without pooling it into a general learning rate.

## Claim boundary

A positive result covers this coupled-quadratic family and finite schedule only. A negative result means this production route did not acquire this operator under its current hypothesis class and budget; it does not show that the substrate or a richer induction route cannot learn it. This does not measure perception-to-induction, natural-task prevalence, or general capability.

## Reproduction

Create the source/native lock with the v1.3 runner's `--lock` mode, inspect and preserve it, run the capture, then run the independent analyzer. Preserve any failed or incomplete run as diagnostic evidence; protocol or source changes require a new version.
