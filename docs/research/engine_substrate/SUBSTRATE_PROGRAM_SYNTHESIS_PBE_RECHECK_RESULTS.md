# Program synthesis PBE recheck — current checkout

**Date:** 2026-09-24. **Purpose:** check whether the preregistered, prompt-free PBE string result survives execution through the current checkout's native extension. This is a provenance refresh of an existing workload result, not a new benchmark family or an independent replication.

## Method

Ran `scripts/pbe_string_battery.py` against the fixed 26-task fixture `tests/fixtures/pbe_string/pbe_string_tasks.json`. The harness invokes native `SynthEnumerate` directly. It compares the engine's typed default with one fixed declared operator/constant inventory and escalates each declared-arm failure once to the preregistered higher budget. Held-out examples are checked by the harness. No task, grammar, or budget was changed.

The full per-task data and provenance are in [`substrate_program_synthesis_pbe_recheck_20260924.json`](../../../evaluation/reports/substrate_program_synthesis_pbe_recheck_20260924.json). The native extension's SHA-256 matches `_native.build.json`'s recorded engine hash; that build manifest records the source fingerprint and the `synth_enumerate.rs` hash. The worktree was dirty overall, but `synth_enumerate.rs` itself was unmodified. The harness wrote its output to `/tmp` during execution; the preserved report is a separately named artifact, leaving the existing `results/pbe_string_battery.json` untouched.

## Result

| Arm | Held-out passes | Scope |
|---|---:|---|
| Typed default | 12/26 | `max_size=15`, engine default candidate cap |
| Fixed declared grammar | 17/26 | Same base budget |
| Declared plus one high-budget escalation for each failure | 20/26 | Escalated to `max_size=20`, 2,000,000 candidates |

The 12 typed-default passes are a subset of the 17 declared passes. The high-budget escalation adds `pbe_015`, `pbe_025`, and `pbe_026`. The full battery completed in 12.91 seconds on this run. These are point results from one process/run; the corpus is hand-built, the declared DSL is fixed but not a general program language, and the result does not measure end-to-end goal orchestration, cross-task transfer, learning cost, or general induction.

## Interpretation and next measurement

The recheck agrees with the existing final alphabet-pricing result (12/26, 17/26, 20/26). This supports the narrow claim that the current extension reproduces that corpus outcome. It does not establish a benefit over a frozen pre-pricing engine in this checkout, because that engine was not rebuilt as a paired control here. The stronger next check is a preregistered, paired current-source comparison across the unchanged fixture, reporting exact task-set differences, candidate counts, search time, and peak memory for both engine versions, followed by a second PBE task family selected before outcomes are observed.
