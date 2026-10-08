# Runtime CAN closure attribution v1 (2026-09-29)

## Result

All 16 fresh workers passed the seven integrity gates: complete size/topology/mode coverage, unique PIDs, parity of audited and uninstrumented progress and final states, zero independent fixed-point residuals, zero-work terminal probes, complete native and per-rule counters, and unchanged source/native locks. Each worker contains an uninstrumented run and an identical audit-enabled replay. Audit timing is diagnostic and is not treated as ordinary runtime.

| N | Topology | Mode | Median progress | Median candidate pairs | Median Term evaluations | Plain closure (ms) | Audited closure (ms) |
|---:|---|---|---:|---:|---:|---:|---:|
| 128 | Path | 2-state | 5 | 6,028,288 | 37,002,642 | 1,267 | 3,944 |
| 128 | Path | 3-state | 9 | 4,879,117 | 30,906,594 | 1,062 | 3,410 |
| 128 | Banded-2 | 2-state | 7 | 7,705,153 | 48,186,849 | 1,709 | 5,086 |
| 128 | Banded-2 | 3-state | 8.5 | 5,697,857 | 36,189,090 | 1,275 | 3,863 |
| 256 | Path | 2-state | 7 | 62,776,634 | 387,604,789 | 16,192 | 45,100 |
| 256 | Path | 3-state | 11 | 48,329,355 | 303,159,242 | 11,045 | 32,818 |
| 256 | Banded-2 | 2-state | 10 | 83,555,435 | 521,738,639 | 19,549 | 58,427 |
| 256 | Banded-2 | 3-state | 10.5 | 57,446,855 | 360,332,817 | 14,404 | 40,763 |

Values are medians over two deterministic workers per cell. Candidate-pair counts and Term evaluations are taken from the per-rule native scale audit.

## Attribution

Doubling N from 128 to 256 multiplies median candidate pairs by 10.4x on the 2-state path and 10.8x on the 2-state banded-2 graph. The corresponding uninstrumented closure time grows 12.8x and 11.4x. These two size points show strongly superlinear work in this range, but do not establish an asymptotic exponent.

Across all 16 audited replays, `can_native_hebbian_reweight`, `can_native_hebbian_mint`, and `can_native_note_coactivation` account for nearly all Term evaluations: approximately 1.83 billion, 0.93 billion, and 0.69 billion respectively. They account for approximately 364 million, 186 million, and 3.38 million candidate pairs. The update rules' Term counts are below one million combined. This identifies the dominant current cost in this workload: matching and evaluating the Hebbian mint/reweight and coactivation rules, rather than the state update itself.

The scale v1 result showed that exact JT remained near-linear for fixed width while closure dominated end-to-end time. This attribution now explains much of that gap and provides concrete targets for a subsequent implementation experiment. It does not establish the same bottleneck for other active rule sets or application domains.

## Limits and next gate

Only path and bandwidth-2 authored CAN fixtures are used. Per-rule counters instrument one CAN rule family; a state/progress parity gate confirms the audit did not change the measured fixed point. Instrumented times are several times higher and must not be used as production timing. Next compare a candidate-index or match-cursor optimization against this baseline with exact state/progress parity, counter reduction, invalidation controls, and instrumentation-off wall-time measurements. Keep natural task distributions and end-to-end learned frame discovery as separate open gates.

## Reproducibility

- [Preregistration](CAN_RUNTIME_CLOSURE_ATTRIBUTION_V1_PREREG_20260929.md)
- [Runner](../../../evaluation/substrate_capability/can_runtime_closure_attribution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/can_runtime_closure_attribution_v1_lock_20260929.json)
- [Raw capture](../../../evaluation/reports/can_runtime_closure_attribution_v1_20260929.json)
