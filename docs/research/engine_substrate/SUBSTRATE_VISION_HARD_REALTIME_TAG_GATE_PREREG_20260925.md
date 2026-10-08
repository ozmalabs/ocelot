# Vision hard-realtime class-tag gate preregistration

Date: 2026-09-25. Benchmark-only metadata clone; production seeds and engine source remain unchanged.

## Question
Can the full vision pipeline's default `tick` response be restored by assigning the relevant vision rules to the `hard_realtime` class required by the enabled DualProcess plan?

## Paired frame probe
Build two identical 3×3 lateral `settle_lib.build_sheet` graphs, seed 20260925, connectivity 8, settle=1. Control uses authored manifests unchanged and unfiltered native `run_rules_report(200000, detect_cycles=True)`. Treatment deep-copies the manifests `vision_waves`, `vision_settle`, `vision_onoff`, `vision_lateral`, and `vision_compose` and adds `latency_class="hard_realtime"` to every executable rule; the same stimulus is submitted through default `tick(200000, detect_cycles=True)`. Every other manifest value, graph input and rule body is identical. Apply one 0-degree, phase-0, period-4 grating using the existing presenter writes. Record selected rules' resulting classes, tick/full-rescan progress and status, root/retina input state, all RetinaCell/LBipolar/HCell/SUnit attrs relevant to the frame, and paired exact values plus tolerances.

## Gate
Treatment tick must make progress and produce nonzero SUnit act/rate. Its terminal relevant state must match full rescan exactly where practical; any non-identical state is reported as a semantic discrepancy, not accepted based only on nonzero output. Treatment must not exceed the application cap. No timing, multi-frame tuning, or seed-change claim is made here.
