# ProblemShape BP parameter semantics v1.1 preregistration (2026-09-27)

## Question

The ProblemShape extractor keys `solve_can_bp` on `has_combine=yes` and deliberately omits the combine value. Prior schema-transfer evidence shows that `max_product` and `sum_product` share one key and are recognized by one minted shape. Does that structural reuse coincide with equal solver behavior on selected identical CAN networks?

## Design

Run six fresh full-seed worker processes: two replicates for each of three fixed resident indices `[0, 25, 50]` from the locked `bigville_cast100.json`. Within each worker, build one resident CAN Microtheory, create two real solve Goals on that same target, with `combine=max_product` and `combine=sum_product`, resolve both through the registered solver path, then extract their ProblemShape keys without observing/minting. BP uses `commit=False`; verify the CAN Concept computational fields (`state`, `external_field`, `identity_field`) are unchanged across both solver calls. Record answer maps, convergence, Goal status, signature keys, exact state equality, max absolute belief delta, boot and request costs, and source/build locks.

The source lock covers this protocol, runner, native/runtime closure, and the resident seed. Each worker captures full input hashes before and after execution. The fixed schedule and residents are encoded by the runner.

## Gates and interpretation

- Six unique cold worker processes, two per resident; every source/build input remains equal to the locked snapshot.
- Both real Goals resolve, both have the same nonempty ProblemShape key, and all extracted beliefs are finite.
- CAN Microtheory state/edge projection is identical before versus after BP, consistent with `commit=False`; this wrapper-level projection does not inspect native edge weights.
- Analyze whether returned belief maps are exactly equal and report numerical deltas, per resident and replicate. Equality is not assumed as a pass condition: observed divergence demonstrates that one ProblemShape key represents a shared structural Goal schema, not behaviorally interchangeable solver settings. Equality only supports equivalence on this selected panel, not in general.
- Any worker or source-integrity failure invalidates inference from affected cells; preserve all raw records.

## Limits

This is a three-resident, two-setting semantic contrast, not an estimate of all CAN solver behavior, convergence quality, task utility, or safe parameter abstraction. It does not challenge ProblemShape's intended role as structural recognition; it audits the stronger interpretation that reuse implies behavioral substitutability. The v1 exploratory capture found closure-added `is_ambivalent` annotations, so v1.1 deliberately checks computational fields rather than requiring all metadata attrs to remain byte-identical. No natural-task prevalence claim follows.
