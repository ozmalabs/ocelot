# MetaShape experiment-summary held-out discrimination preregistration (2026-09-26)

## Question

After the daemon close path mints a MetaShape from two supported experiment summaries that vary in `axis_tag` and topic, does that minted pattern recognize a third supported summary with new values while refusing a refuted summary that changes the fixed `answer` field?

## Locked procedure

1. Disable seed persistence before boot. Create a fresh adapter and load only `meta_shape_growth` with dependencies; require a complete two-seed load.
2. Add two ready `Experiment` nodes with `outcome="supported"`, `axis_tag` `bridge_a` and `bridge_b`, empty `hypothesis`/`game`/`run_dir`, and `taught=False`. Invoke only the daemon `_close_tick` hook to produce training summaries. Record the newly minted MetaShape name, support, and signature.
3. Add one new ready supported Experiment with `axis_tag="bridge_c"`; run `_close_tick` and record its observation `status`, `covered_by`, and residual. This is the positive holdout.
4. Add one new ready refuted Experiment with `axis_tag="bridge_d"`; run `_close_tick` and record the same fields. `answer` now differs from the support-2 training pattern; this is the negative control.
5. Record per-phase observations, new MetaShape nodes, Experiment taught flags, source/native hashes, and elapsed time. Do not directly call `teach()` or edit seeds/rules.

## Primary gates

- The training pair closes and mints exactly one MetaShape with support 2.
- The supported holdout is covered by that exact minted MetaShape.
- The refuted negative control is not covered by that minted MetaShape.
- The negative control alone adds no new MetaShape.
- Source/input lock matches and persistence guard remains enabled.

This small pattern-specific test separates held-out reuse from a fixed-field negative control. It does not estimate false-positive rates, natural experiment distributions, semantic truth, or broad capability. A failed gate is reported without changing the inputs or acceptance criteria.
