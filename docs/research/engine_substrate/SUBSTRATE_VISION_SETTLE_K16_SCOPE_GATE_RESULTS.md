# K=16 orientation response and settle-scope gate

**Run:** 2026-09-25. **Evidence:** four-arm, one-seed native comparison after retinal development and theta adaptation, with independent OSI and exact tuning parity audit. Production seed and engine source remain unchanged.

## Design
A 4×4 lateral cortical sheet (seed 20260927, connectivity 8) was evaluated under four benchmark variants: authored global versus Retina-root-scoped mean, crossed with unfiltered full-rescan closure versus default tick with all five vision seed families tagged `hard_realtime` in cloned manifests. Every arm shared the same 3,000-step retinal development and 2,000-presentation theta adaptation. The probe used 12 orientations × 16 phases (`cell_stats`, rate readout). No cortical weight training was performed; weights were held fixed during theta adaptation and probing.

## Result
All four tuning matrices were exactly equal. Independent recomputation from each tuning curve matched per-unit OSI, and each arm's mean OSI was 0.252461. The four arms also had identical final weight hashes. This supports single-seed response parity between global and root-scoped competition, and between full rescan and tagged default tick under this stimulus protocol. The measured OSI is a one-seed baseline, not a population estimate or evidence of learned/selective capability.

Full-rescan calls explicitly reported fixed points or repeated graph states (adaptation: 335 fixed-point and 1,665 repeated-state outcomes; probe: 89 and 391). The tagged tick API returns a progress count only. The v1.1 runner mistakenly labeled each positive count `tick_cycle_detected`; this does not establish the termination reason or exact per-presentation work. Its own `no_silent_or_zero_progress_probe_reports` check is therefore not evidence for termination status. V1.2 amendment records this evidence limit. A future repeated run should preserve per-call tick counts and use an API that reports termination status.

The first v1 execution was confounded because the full-rescan arm's retinal-development phase used untagged default tick while the tagged arm did develop. Its partial file was overwritten during correction; only an incomplete console summary remains and is explicitly excluded from evidence.

## Evidence
- [`v1 preregistration`](SUBSTRATE_VISION_SETTLE_K16_SCOPING_GATE_PREREG_20260925.md), [`v1.1 driver/preparation correction`](SUBSTRATE_VISION_SETTLE_K16_SCOPING_GATE_V1_1_AMENDMENT_20260925.md), [`v1.2 status-reporting amendment`](SUBSTRATE_VISION_SETTLE_K16_SCOPING_GATE_V1_2_AMENDMENT_20260925.md)
- [`runner`](../../../scripts/substrate_vision_settle_k16_scope_gate.py), [`independent analyzer`](../../../scripts/analyze_substrate_vision_settle_k16_scope_gate_v1_1.py)
- [`v1.1 raw`](../../../evaluation/reports/substrate_vision_settle_k16_scope_gate_v1_1_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_settle_k16_scope_gate_v1_1_analysis_20260925.json), [`lock`](../../../evaluation/substrate_capability/vision_settle_k16_scope_gate_v1_1_lock_20260925.json)
- [Incomplete excluded v1 console summary](../../../evaluation/reports/substrate_vision_settle_k16_scope_gate_v1_confounded_summary_20260925.json)

## Limits and next gate
This gate establishes exact parity on one seed and a developed retina, but not learned cortical selectivity, a multi-seed distribution, or a speedup. Next add multi-seed replication and a positive-control/learned arm, record complete per-call progress/status for tagged tick, and include a baseline with settling disabled to measure the actual contribution of `st_settle`. Keep production metadata and seed semantics unchanged until those comparisons are complete.
