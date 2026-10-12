# Native visual rule-phase trace and tick parity v1 preregistration

## Question

Can an opt-in observer capture visual unit state immediately after the `oo_sunit_rate` rule fires inside the same native cycle plan used by `WaveWorld.step`, while preserving the default final graph exactly?

## Design

- Use the three independently adapted shared-substrate checkpoints from vision checkpoint replication v2.0 (20260935, 20260936, 20260937), each in global and root-scoped rule variants.
- For each seed/scope pair, restore identical checkpoint state into two independent substrates. The control uses unmodified `WaveWorld.step`; the trace arm replaces only the Python wrapper's `tick` call with the new native `tick_with_rule_state_trace`, which must invoke the same cognitive-cycle default plan, max-step budget, cycle flag, epoch advancement, rule latency filtering, reflex handling, and trajectory control.
- Present one 0° phase-0 grating to sheet A and a blank to sheet B, target first and sibling second. This is six paired cells and twelve substrate paths. Every arm starts from its exact checkpoint.
- Trace after successful execution of `st_settle` (or `st_settle_root_scoped_benchmark`) and `oo_sunit_rate`, for all 32 SUnits, recording `act`, `act_next`, `theta`, `rate`, `act_step`, and `rate_step`. Use a 10,000-event cap; any truncation is a reported failure.

## Gates

1. Lock the protocol, runner, analyzer, adapter, seed/checkpoint hashes, Rust sources, native build manifest, and loaded extension. Require two source-lock probes 20 seconds apart and stable per-worker fingerprints.
2. Verify trace and control arms restore the same prepared graph and have the same graph digest after A and B steps, per seed/scope pair.
3. Confirm the trace contains successful `oo_sunit_rate` events for both sheets and reports their exact rule name/order and per-node snapshots.
4. At each captured rate-rule event, independently calculate `max(act - theta, 0)` and compare it with the captured `rate` for every node with a matching rate/activation update stamp. Report coverage and all residuals; equation mismatch is a substantive outcome, not grounds for dropping a worker.
5. Confirm no event truncation and report pass/progress counts, traced versus control wall/CPU time, process peak RSS, and observer event count.

## Interpretation boundary

This validates an instrumentation path on one synthetic grating and three existing learned checkpoints. Exact final graph parity is required before using the trace as a phase-local measurement tool. It does not establish recognition quality, frame discovery, natural image prevalence, or scaling. The observer records after a whole rule invocation (all bindings for that rule), not after each individual binding.

## Reproduction

Build the native engine with `scripts/engine_build.sh`, create the source lock with the runner's `--lock` option, repeat it after a 20-second stable-source interval, run the capture, and execute the independent analyzer. Raw data, lock, analysis, and result note use the `vision_native_rule_phase_trace_v1_20260929` stem.
