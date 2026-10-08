# MetaShape rung-attribution discrimination panel v2 preregistration (2026-09-27)

## Question

After two examples induce a schema, does MetaShape's exact structural path transfer to a new supported instance while rejecting held-out cases that alter, omit, or extend the fixed relation structure? How often does the weaker prior-recognition path attribute those controls anyway?

## Design

Run two fresh processes for each of four authored schema families (8 workers). Each worker boots a fresh `WorldAdapter`, loads the `meta_shape_growth` seed dependency closure, disables seed persistence, and trains on exactly two examples that vary two named fields while holding one field constant. It then submits five fixed-order probes:

1. positive holdout: new values for both varying fields, unchanged fixed field;
2. negative, fixed-value change;
3. negative, fixed field omitted;
4. negative, extra untrained field added;
5. negative, fixed field changed to a different value type.

The four families reuse v1.1's `FrameBindingProbe`, `MotionRuleProbe`, `ResourceTransferProbe`, and `GoalTraceProbe` so outcomes can be compared. Each family runs alone in its worker; this prevents a shape acquired for another family in the same graph from confounding its attribution. Existing seeded/prior coverage remains active and is recorded. Thus the known `spatial_dynamics` prior conflict for `MotionRuleProbe` is a measured condition, not silently excluded.

For every teach call record observation status, `covered_by`, residual, duration, storage result, current MetaShape inventory, and source lock. Report `recognized` (structural rung) separately from `recognized_prior` (keyword-prior fallback). Count a negative as a false attribution if either status is recognized or prior-recognized; also report exact target-shape coverage separately. Preserve each per-worker outcome and resource record.

## Provenance and gates

Hash, before and after every worker: all Python under `domains/`, `substrate/`, `runners/dsl/python/`, `worlds/`, and `scripts/`; all seed JSON; all regular files under `data/slabs/`; the native extension and build manifest; this protocol, runner, analyzer, and shared measurement helper. Record commit, Python/platform, process IDs, seed-load outcome, and persistence state. Refuse execution if the native build is stale or any lock changes.

Integrity gates:

- 8 distinct workers, exactly two per family;
- one successful `meta_shape_growth` dependency load per worker, no seed failure;
- exact pre/post source/runtime lock equality at worker and parent boundaries;
- two training examples and all five held-out probes per worker;
- raw, lock, runner, protocol, and analyzer hashes reconcile independently.

Capability outcomes are descriptive rather than all-pass gates. Report per-family training mint count, positive exact-transfer rate, positive prior-attribution rate, negative exact-shape false-coverage rate, any-rung negative false-attribution rate, residual rate, and cost. Do not pool families into one accuracy estimate. The fixed-field semantics are authored by the experiment; this measures structural discrimination, not truth or downstream utility.

## Scope limits

This is a targeted, synthetic rung-attribution test over four hand-designed schemas, two workers per schema, and one seed-defined learning mechanism. It does not estimate natural-task prevalence, semantic validity, downstream benefit, or open-ended concept invention. Results apply only to the locked source/runtime snapshot. A failure to mint or transfer is retained as evidence; no family will be removed or repaired after outcomes are visible.
