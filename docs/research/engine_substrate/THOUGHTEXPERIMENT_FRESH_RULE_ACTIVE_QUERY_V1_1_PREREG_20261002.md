# Thoughtexperiment fresh-rule active query v1.1 — isolated branch and CoW comparison

## Amendment rationale

V1's proposal-selection and held-out outcomes remain valid, but its neutral-rate timing comparison is not: the predictor reused mutable branches across four candidate pools, so later conditions ran on larger graphs. V1.1 leaves the v1 artifacts unchanged and resets prediction state for every hypothesis/example pair. It also compares two branch backends from the same base: immutable snapshot `.fork()` (shared-page CoW) and `fork_full_copy_experiment()`.

## Question

On the newly authored `classify_meter_mode` target, does prompted native-Term selection plus active querying preserve proposal utility when every candidate prediction is isolated? How do shared-page snapshot forks and full-copy forks compare on semantics and cost for this small task graph?

## Procedure

Four workers independently compose the fault repair. For each backend and each neutral rate (0%, 50%, 90%, 99%), the selector receives the same 100 unique examples and two supplied hypotheses. Each hypothesis/example callback creates a fresh branch from the same unchanged fault base, replaces the target rule, inserts exactly one case, runs native closure and a fixed-point probe, and reports the resulting class. No branch is reused. The predictor records fork, patch, closure, and full prediction timings. Snapshot creation is measured once per worker.

All eight order rows per worker (backend × neutral rate) are captured before any expected labels are attached. The post-freeze stage computes labels, compares survivors, draws the preseeded random probe, and evaluates four separate positive/negative/neutral held-outs under both backends. It checks receipt parity, source preservation, and fixed-point completion. Active Python/Rust/seed sources and the loaded binary are locked.

## Measures and pass conditions

Pass requires all 32 backend-condition selections to be valid one-bit discriminators, with only the composed proposal surviving the post-freeze oracle; both backends must return identical query predictions and choices. The proposal must pass every held-out and the fault must fail every nonzero held-out. All source, receipt, primary-preservation, and fixed-point checks must pass. Report selector total, branch fork, patch, and closure timings separately by backend and neutral rate; timings are descriptive for this small graph and are not an asymptotic claim.

## Scope boundary

The new rule family extends structural-composer evidence beyond the prior fixtures, but remains a deliberately authored binary rule with an explicit flip cue. Python supplies the rule, fault, query pool, labels, and orchestration. This tests semantic transfer and the thoughtexperiment branch interface, not autonomous diagnosis, open-ended induction, or general CPU speedup.

## Reproduction

Run `python3 evaluation/substrate_capability/thoughtexperiment_fresh_rule_active_query_v1_1.py --lock`, `--orders`, and `--score`, followed by `python3 evaluation/substrate_capability/analyze_thoughtexperiment_fresh_rule_active_query_v1_1.py`.
