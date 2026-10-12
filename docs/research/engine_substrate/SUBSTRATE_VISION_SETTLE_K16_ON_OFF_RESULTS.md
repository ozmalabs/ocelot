# K=16 acute settling on/off ablation

**Run:** 2026-09-25. **Evidence:** paired one-seed native workload with independent response, work-count, and provenance audit. No production seed or engine source changed.

## Design
Two independent 4×4 lateral sheets used seed 20260928, connectivity 8. Both had identical benchmark-only `hard_realtime` tags, 3,000 retinal-development steps, and 2,000 theta-adaptation presentations. We pinned theta and froze learning before probing, then toggled only `SettleParams.settle` (1.0 versus 0.0). The existing `cell_stats` procedure covered 12 orientations and 16 phases and also performs baseline and preferred-orientation F1/F0 measurements.

## Result
The complete tuning matrices were exactly equal and mean OSI was 0.294689 in both arms. No weight drift occurred during the readout. The settled arm consumed 91,006 native progress applications across 480 presentations; the settle-off arm consumed 2,848, a 96.87% reduction. Their single-run readout times were 13.11 s and 3.92 s, respectively. The shared adaptation work was also identical at 383,230 progress applications per arm.

This is direct evidence that, for this one developed/adapted sheet and stimulus sequence, the authored settling phase added substantial measured work without changing the recorded rate tuning. It does not prove settling is generally vacuous, and the timing pair is not a reliable speedup estimate. Tick returns are counts only; they do not report whether each call reached a fixed point or exited on cycle detection.

The runner's built-in `probe_count_expected` assertion expected 192 calls and therefore returned `pass=false`. That count included only the 12×16 tuning presentations; `cell_stats` also makes 32 baseline and 16×16 phase presentations, for 480. The raw report is preserved with this failed assertion. The independent analyzer uses all 480 recorded tick counts and passes the measurement invariants.

## Evidence
- [`preregistration`](SUBSTRATE_VISION_SETTLE_K16_ON_OFF_ABLATION_PREREG_20260925.md), [`v1.1 count correction`](SUBSTRATE_VISION_SETTLE_K16_ON_OFF_ABLATION_V1_1_AMENDMENT_20260925.md)
- [`runner`](../../../scripts/substrate_vision_settle_k16_on_off_ablation.py), [`independent analyzer`](../../../scripts/analyze_substrate_vision_settle_k16_on_off_ablation.py)
- [`raw report`](../../../evaluation/reports/substrate_vision_settle_k16_on_off_ablation_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_settle_k16_on_off_ablation_analysis_20260925.json), [`lock`](../../../evaluation/substrate_capability/vision_settle_k16_on_off_ablation_lock_20260925.json)

## Next gate
Repeat over preregistered seeds with balanced execution order and retain per-frame states plus exact progress values. Add task stimuli or a trained cortical arm to test whether another objective responds to settling even when this readout does not. Keep the production seed unchanged until that broader result is available.
