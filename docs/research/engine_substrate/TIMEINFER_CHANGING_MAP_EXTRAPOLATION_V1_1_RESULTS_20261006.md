# TimeInfer changing-map extrapolation v1.1 results

## Result

The corrected source-locked replication completes all 15 workers with exact
repeat parity and stable inputs. The order-2 translation positive control
reports order 2, predicts the withheld next frame exactly, and mints once in all
three runs. Random translation refuses and does not mint in all three runs.

`TimeInfer` refuses every registered changing or nonlinear map sequence:

| Case | Direct recognition | Exact held-out prediction | Rule result | Mints |
|---|---:|---:|---|---:|
| Changing linear shear | 0/3 | 0/3 | `time_none` in 3/3 | 0/3 |
| Changing quadratic shear | 0/3 | 0/3 | `time_none` in 3/3 | 0/3 |
| Static quadratic shear | 0/3 | 0/3 | `time_none` in 3/3 | 0/3 |

No map case was falsely accepted or minted. This measures the current
`TimeInfer` route on these exact integer fixtures: its order-N path transfers
polynomial rigid-translation offsets, while this route does not recognize
either the registered static nonlinear map or changing linear/nonlinear maps.
It does not measure the separate `GenInfer` nonlinear induction route or a
richer sequence-map learner.

The median time for the four direct field queries together is 0.332 ms for the
translation control, 5.20 ms for changing linear shear, 46.07 ms for changing
quadratic shear, 46.95 ms for static quadratic shear, and 0.323 ms for random
translation. These timings exclude boot and rule closure but include four
native evaluations; they are descriptive for this fixture, not an asymptotic
scaling estimate. The larger map-case cost indicates that refusal can still
consume appreciable search work here; it should not be described as a cheap
floor without a separately instrumented work count.

## Instrument correction

The preserved v1 capture failed its positive-control analysis because the
runner accepted only a Python list, while the native binding returns a
predicted frame as a tuple of rows. V1.1 fixes the representation check and
repeats the full frozen schedule in fresh processes. The v1 capture remains
available for audit and is excluded from the result above.

## Scope and reproduction

The fixtures are small and authored. No natural-task prevalence, general
nonlinear extrapolation, or stream-length complexity claim follows. The next
gate is an explicit bounded changing-map hypothesis family, with candidate
budget, exact held-out transfer, refusal controls, false-mint rate, and work
counts fixed before implementation comparison.

Artifacts: [v1.1 protocol](TIMEINFER_CHANGING_MAP_EXTRAPOLATION_V1_1_PREREG_20261006.md),
[runner](../../../evaluation/substrate_capability/timeinfer_changing_map_extrapolation_v1_1.py),
[analyzer](../../../evaluation/substrate_capability/analyze_timeinfer_changing_map_extrapolation_v1_1.py),
[lock](../../../evaluation/substrate_capability/timeinfer_changing_map_extrapolation_v1_1_lock_20261006.json),
[capture](../../../evaluation/reports/timeinfer_changing_map_extrapolation_v1_1_20261006.json),
[analysis](../../../evaluation/reports/timeinfer_changing_map_extrapolation_v1_1_analysis_20261006.json),
[preserved v1 capture](../../../evaluation/reports/timeinfer_changing_map_extrapolation_v1_20261006.json).
