# CAN Stage A fallback envelope results v1

## Result

All 18 cells passed across three fresh workers: N=16/32 × path/banded-2/complete, three matched seeds each. Every ordinary, compare-only, and Stage-A-enabled run reached the independent CAN fixed point within budget. Stage-A-enabled and ordinary closure had exact full-graph and progress/terminal parity in every cell.

The measured workload had **zero Stage-A-derivable drains**, **434 excluded drains**, and **zero runtime conflict fallbacks**. Thus the fallback rate is undefined here: the current static derivability filter did not admit any drain from this authored CAN rule workload, so the runtime overlap guard had no proposal set to assess. Stage A was inapplicable in this envelope. Compare-only recorded zero divergences/unsound drains, which is vacuous for Stage A correctness because it compared no eligible drains.

Stage-A-enabled / ordinary median wall-time ratios range from 0.75× to 1.04× across the six size/topology groups, with only three repeats per group. These noisy descriptive timings are not evidence of a speedup or stable overhead. The useful result is the eligibility census: the current Stage A rules are not applicable to the measured CAN path because each drain fails the static admission conditions, including read/write coupling for update rules.

## Evidence and limits

- Preregistration: [`SUBSTRATE_CAN_STAGE_A_FALLBACK_ENVELOPE_PREREG_20260926.md`](SUBSTRATE_CAN_STAGE_A_FALLBACK_ENVELOPE_PREREG_20260926.md)
- Runner: [`substrate_can_stage_a_fallback_envelope_v1.py`](../../../scripts/substrate_can_stage_a_fallback_envelope_v1.py)
- Independent analyzer: [`analyze_substrate_can_stage_a_fallback_envelope_v1.py`](../../../scripts/analyze_substrate_can_stage_a_fallback_envelope_v1.py)
- Lock: [`can_stage_a_fallback_envelope_v1_lock_20260926.json`](../../../evaluation/substrate_capability/can_stage_a_fallback_envelope_v1_lock_20260926.json)
- Raw capture: [`substrate_can_stage_a_fallback_envelope_v1_20260926.json`](../../../evaluation/reports/substrate_can_stage_a_fallback_envelope_v1_20260926.json)
- Analysis: [`substrate_can_stage_a_fallback_envelope_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_can_stage_a_fallback_envelope_v1_analysis_20260926.json)

The analyzer passes all nine checks. This result concerns one authored CAN rule set and a synthetic topology envelope; it does not estimate natural-workload prevalence, prove general Stage A soundness, or measure useful Stage A throughput. Next identify workloads containing rules that actually pass static derivability, then measure admitted share and overlap fallback there. Avoid treating all-excluded corpora as guard-soundness evidence.
