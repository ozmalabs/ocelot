# CPython `stat` bounded module-composition replay v1.2 results

Date: 2026-09-28  
Status: complete; all registered integrity and analysis gates pass.

## Result

Two fresh workers replayed the frozen v1 workload against the current source snapshot: seven `stat.S_IS*` predicates, five inputs each, and two positive controls. Both workers returned all 35/35 primary outputs exactly, passed both positive controls, and had zero wrong returns, abstentions, receipts, or minted observations. The independent AST selector and bit-mask oracle reconstructed the same frozen frame. Worker outcomes matched case by case. The additional ambiguous-module-name refusal guard was not directly triggered by this positive-only frame, so its refusal behavior remains untested here.

| Measure | Worker 0 | Worker 1 |
|---|---:|---:|
| Exact primary outputs | 35/35 | 35/35 |
| Positive controls | 2/2 | 2/2 |
| Wrong returns / abstentions | 0 / 0 | 0 / 0 |
| Receipts / minted observations | 0 / 0 | 0 / 0 |
| Median call wall / CPU | 25.33 / 25.34 ms | 24.91 / 24.92 ms |
| P95 call wall / CPU | 34.63 / 34.62 ms | 38.93 / 38.51 ms |
| Boot loaded / total (failures) | 731 / 742 (11) | 731 / 742 (11) |
| Peak process RSS | 1.806 GB | 1.806 GB |

Timing includes a cold first call (about 1.79 s); median and p95 summarize all 37 scheduled calls, so the median describes warmed repeated calls while the tail reflects this startup outlier. Full boot takes about 12.3–12.4 s wall and 13.3–13.8 s CPU. This is not a substrate-only latency estimate: full runtime boot dominates process setup and the code-reading request reprocesses source.

## Integrity and provenance

The runner and independent analyzer passed all 20 gates, including stable full-source locks before/during/after both workers, exact task/source hashes, complete schedules, worker parity, frozen baseline artifacts, and an independently reconstructed frame. The pre-run amendment discloses four changed runtime files and one changed loaded seed since v1; therefore v1-to-v1.2 differences are descriptive and not causally attributable to the emitter changes. Four measurement scripts were added to the source inventory. The frame, CPython input, native extension, control corpus, and baseline artifact hashes remain frozen as specified.

- Raw report SHA-256: `0557b753e7282aa3fca3a9dd629a6f4e91a6adea93ebc42d1565e722774e40c3`
- Current-source lock SHA-256: `529f59be3e44d89bccda2394128b1ea5a00c867215230aa9210732b804a1d90c`
- Frozen frame SHA-256: `d1538bb1dec48de2ef8d89252f1afd4f9e8159a0e9768688b29945b1ac5d8bc0`

## Claim boundary

This is repeatability evidence for a targeted, inspected module-composition fragment under the latest locked source. It is not blind family transfer, a Python accuracy estimate, or evidence that the new refusal branch is safe. Earlier v1 abstained on 35/35 cases; v1.1 and v1.2 both pass the targeted positive panel after bounded helper/constant and bitwise lowering was added. Because other runtime and seed inputs also changed, that sequence does not isolate implementation causality. Next, use a separately locked adversarial refusal panel for ambiguous/dynamic globals, duplicate writes, unsupported helper effects/recursion/depth, and invalid bitwise operand types/ranges; then evaluate a genuinely held-out function family selected without inspecting candidate outputs.

## Artifacts

- [v1.2 preregistration](SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_2_REPLAY_PREREG_20260928.md)
- [v1.2 amendment](SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_2_AMENDMENT_20260928.md)
- [v1.2 runner](../../../scripts/substrate_stdlib_stat_prediction_panel_v1_2.py)
- [v1.2 analyzer](../../../scripts/analyze_substrate_stdlib_stat_prediction_panel_v1_2.py)
- [raw report](../../../evaluation/reports/stdlib_stat_prediction_panel_v1_2_20260928.json)
- [source lock](../../../evaluation/substrate_capability/stdlib_stat_prediction_panel_v1_2_lock_20260928.json)
- [frozen task frame](../../../evaluation/reports/stdlib_stat_prediction_frame_v1_20260927.json)
