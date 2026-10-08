# Shared-substrate multi-sheet task pilot v1.4 results

## Outcome

The source-stable two-sheet capture completed in both global and root-scoped modes. All closure, replay, calibration, topology, source, and weight-stability checks pass. The driver's overall `pass` is false because its `joint_B_SUnit_activity_recorded` gate requires positive B `rate` during A's K=16 readout; the captured `rate` value is zero in both modes. This is a measured endpoint result, not a missing capture or an infrastructure failure.

During A's paired readout, B's 128 active retinal pixels are confirmed for the grating context, but all 16 B SUnits have zero captured `rate` and `act` at that K=16 endpoint in both scopes. B-only K=16 tuning readout has maximum response 1.7744 and mean OSI 0.2968 in each scope. That sweep establishes response somewhere in its stimulus sequence, but does not isolate the exact fixed phase-zero paired frame. The later v1.5 direct endpoint control shows positive B `act` for that exact frame, with the same per-unit activation when A is also stimulated. Thus v1.4's endpoint-zero result does not establish cross-sheet suppression; the distinct readout sequences/fields require reconciliation.

Thus v1.4 alone did not identify why its joint B endpoint fields were zero. V1.5 establishes that the exact frame drives B `act` and that adding A does not change it in a one-presentation root-scoped control. The `rate`/`act` distinction for the root-scoped exact-frame endpoint is resolved by v1.6; readout-sequence effects and global-scope behavior remain open. The result does not establish general scope safety.

## Recorded measurements

| Mode | Adaptation time | Maximum cumulative closure work / presentation | B grating retinal bursts | B SUnit endpoint rate / act during paired A readout | B-only tuning max / mean OSI |
|---|---:|---:|---:|---:|---:|
| Global | 1,593.8 s | 238,132 | 128 | 0 rate / 0 act | 1.7744 / 0.2968 |
| Root-scoped | 148.8 s | 868 | 128 | 0 rate / 0 act | 1.7744 / 0.2968 |

The adaptation-time ratio is descriptive for this one seed and fixture. The global arm had one closure continuation; the root-scoped arm had none. Every captured presentation terminated as `fixed_point` or `repeated_graph_state` within the registered cumulative bound. The A tuning delta between blank and B-grating conditions remains zero in both modes, consistent with v1.3.

## Next discriminating measurement

V1.5 has completed the fixed-frame conditions under root-scoped settling. The next step is a pass-by-pass trace of the `rate` and `act` writers/readers and a replay of the K=16 readout sequence from the same prepared snapshot. After reconciling those measurements, repeat the fixed-frame comparison under global scope and broaden seeds only if the endpoint semantics are stable.

## Evidence and limits

- [Raw v1.4 capture](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_4_20260927.json)
- [Protocol amendment](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_4_AMENDMENT_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_4_lock_20260927.json)

This remains a single-seed, 4×4, two-sheet pilot. It measures a particular learned state and readout schedule; it is not an estimate of natural-task frequency, general tractability, or scale performance.
