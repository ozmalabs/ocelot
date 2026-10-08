# Vision hard-realtime tag gate

**Run:** 2026-09-25. **Evidence:** paired native one-frame runtime probe and independent audit. The benchmark adds metadata to cloned manifests only; production seed files and engine source are unchanged.

## Result
On a 3×3 sheet, the unmodified-rule full-rescan control and benchmark-only hard-realtime-tagged default-tick treatment had the same rule count. The treatment added `latency_class="hard_realtime"` to every executable rule in the five vision manifests (waves, settle, onoff, lateral, compose). Default tick then made 111 progress applications and produced nonzero activity. It exactly matched the unfiltered full-rescan control across recorded RetinaCell, HCell, LBipolar, and SUnit state.

Together with the prior probe, this supports the routing diagnosis: the enabled DualProcess plan filters for `hard_realtime`, and untagged vision rules do not run on that path. The one-frame comparison shows that the metadata route can restore this fixture's default-tick behavior without changing its recorded response. It does not establish multi-frame parity, orientation-score parity, or that every vision rule should be assigned that latency class in production.

## Evidence
- [`preregistration`](SUBSTRATE_VISION_HARD_REALTIME_TAG_GATE_PREREG_20260925.md), [`runner`](../../../scripts/substrate_vision_hard_realtime_tag_gate.py), [`independent analyzer`](../../../scripts/analyze_substrate_vision_hard_realtime_tag_gate.py)
- [`raw report`](../../../evaluation/reports/substrate_vision_hard_realtime_tag_gate_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_hard_realtime_tag_gate_analysis_20260925.json), [`lock`](../../../evaluation/substrate_capability/vision_hard_realtime_tag_gate_lock_20260925.json)
- Routing sources: [`cognitive_cycle.rs`](../../../runners/dsl/src/cognitive_cycle.rs), [`substrate.rs`](../../../runners/dsl/src/substrate.rs)

## Next gate
Compare full-rescan closure and tagged default tick over the complete 12-orientation, 16-phase instrument and calibrated development/adaptation controls. Track per-presentation status and response parity. Then compare global and root-scoped settle variants using the corrected tick metadata. Do not edit production latency metadata before that workload-level gate.
