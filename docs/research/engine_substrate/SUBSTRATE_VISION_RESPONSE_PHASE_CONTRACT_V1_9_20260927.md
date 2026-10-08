# Vision substrate response-phase measurement contract v1.9

## Purpose
A substrate response is not represented by one interchangeable activity scalar. On the current vision fixture, `rate` and final `act` are sampled at different points in the closure. Every task result must identify which phase and field it reports.

## Required record per presentation

1. **Input delivery:** declared frame, active-pixel count, Retina step, and observed retinal burst count for each sheet.
2. **Rate-write snapshot:** the first completed pass at which every SUnit's `rate_step` equals the current Retina step. Record each unit's `act`, `theta`, `rate`, `act_step`, and `rate_step`. Gate the local rule semantics with `rate == max(act - theta, 0)` at this snapshot (absolute tolerance 1e-9). Do not call this value the final settled response.
3. **Closure trajectory:** one complete substrate pass per trace row, total progress work, total passes, exact full-graph state digests, and per-sheet `act`/`rate`/`theta` summaries. Termination must be labelled `fixed_point`, exact `repeated_graph_state` with cycle start and period, or explicit cap. A cycle endpoint is not a fixed point.
4. **Post-settle outcome:** for a fixed point, report final per-unit `act` and derived summaries. For a cycle, report the cycle's per-unit min/max/mean across every state in the detected period and retain the terminal phase separately. Never collapse the cycle to its last state.
5. **Work and timing:** progress steps and passes are primary engine work measures. Wall time is descriptive and must name hardware, trace mode, and whether graph hashing is included.

## Current source-derived interpretation
`oo_sunit_rate` is guarded by `rate_step < Retina.step` and `act_step == Retina.step`, writes `max(act-theta,0)`, and stamps the current step. The v1.8 trace confirms this equation exactly at the first rate-write snapshot. The settling rules can continue changing `act` on later passes while `rate_step` remains current and rate remains unchanged. This is a field/phase distinction; it is not by itself evidence that either field is wrong.

## Admission gate
A task/scale comparison is interpretable only when input delivery passes, rate-write equations pass, update stamps are present, and closure class is reported separately. If a closure cycles, post-settle output is an orbit statistic. If any gate fails, preserve the capture and report the failure; do not infer capability absence from a zero scalar.
