# Current-engine PBE synthesis recheck (2026-09-25)

## Question and method

Does the fixed 26-task, prompt-free string PBE battery retain its prior result on the currently installed native engine, and what search cost accompanies its held-out passes? The run calls native `SynthEnumerate` through the existing [`pbe_string_battery.py`](../../../scripts/pbe_string_battery.py) runner. It compares the engine's typed default against one fixed declared operator/constant inventory and escalates failures in that declared arm once. The fixture and arm/budget definitions were unchanged. The wrapper captured per-task candidate counts and timings, process-wide CPU and peak RSS, build/source hashes, and the prior recheck comparison. The exact command and raw rows are in the [raw report](../../../evaluation/reports/substrate_program_synthesis_pbe_recheck_20260925.json); the harness is [`substrate_program_synthesis_current_recheck.py`](../../../scripts/substrate_program_synthesis_current_recheck.py).

## Results

| Arm | Held-out passes | Candidate evaluations | Sum of rounded per-task search/holdout times |
|---|---:|---:|---:|
| Typed default, max size 15 | 12/26 | 2,818,727 | 1.887 s |
| Declared fixed grammar, max size 15 | 17/26 | 2,123,383 | 1.053 s |
| Declared-arm failures escalated, max size 20 | 3 additional / 9 re-probed | 12,574,684 | 9.776 s |

The fixed declared grammar gains five passes over typed default at the same maximum size with fewer aggregate candidate evaluations on this fixture. Escalation gains three additional tasks for about 5.9× the declared-default candidate count and 9.3× its rounded task-time sum. Overall declared-plus-escalation performance is 20/26. The one found-but-failed-holdout case remains a failure, not a pass.

By task tier, typed default passes 8/9 single-op, 3/8 composition, 0/5 deep-or-missing, and 1/4 memorization-trap tasks. Declared default passes 8/9, 6/8, 1/5, and 2/4 respectively. High-budget escalation adds two memorization-trap tasks and one composition task; it solves none of the four deep-or-missing tasks it re-probes.

The process used 12.73 seconds wall time, 12.30 seconds user CPU, 0.54 seconds system CPU, and 287,008 KiB peak RSS. Peak RSS and CPU include Python imports, all arms, and report generation; they are not per-arm native memory measurements. The prior 2026-09-24 recheck had identical pass task IDs in all arms. This is same-fixture repeated evidence, not an independent task-family replication or a pre-pricing baseline comparison.

## Claim boundary and next work

This measures bounded enumerative program synthesis with a fixed operator inventory. It does not measure residual-triggered rung selection in the full substrate, open-ended concept minting, learning from interaction, retention, cross-domain transfer, or reuse amortisation. One held-out example per task is weak protection against overfitting. The next E2 step is a separately selected task family with frozen splits, recurring-novelty and one-off/adversarial controls, plus matched search budgets and explicit proposal/mint/rollback accounting.
