# Event-reasoning Stage A applicability envelope results v1

## Result

All 30 cells passed across six fresh worker processes: entity counts 1, 4, 16, 64, and 256, with all six arm-order permutations represented. The native loader installed the three authored event-reasoning rules. Ordinary, compare-only, and Stage-A-enabled arms all reached the independent per-entity oracle; ordinary and enabled runs matched complete graph state, progress, and terminal behavior exactly.

Every size had three compared derivable rule drains per run, no statically excluded drains, and no overlap fallbacks. Thus the measured drain admission share was 100% and fallback rate 0% for this independent-entity workload. Proposal count was exactly three per entity per run, matching the three-rule chain. Compare-only recorded zero divergent and zero unsound drains.

| Entities | Compared drains / run | Proposals / run | Median ordinary wall time | Median Stage A wall time | Stage A / ordinary |
|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 3 | 21.6 µs | 24.7 µs | 1.37× |
| 4 | 3 | 12 | 24.8 µs | 32.2 µs | 1.13× |
| 16 | 3 | 48 | 52.0 µs | 57.0 µs | 1.15× |
| 64 | 3 | 192 | 106.9 µs | 186.9 µs | 1.71× |
| 256 | 3 | 768 | 297.5 µs | 781.3 µs | 2.57× |

Wall-time medians use six runs with balanced arm order. The upward ratio at larger sizes is consistent with extra proposal capture and commit work in the current Stage A path, which remains sequential. These are very small workloads and six samples; timings are descriptive, not a general cost law or a speedup claim. The experiment does not establish that Stage A is useful for the broader substrate, only that this authored rule family is admitted and that the current enabled implementation costs more at larger measured sizes.

## Evidence and limits

- Preregistration: [`SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_PREREG_20260926.md`](SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_PREREG_20260926.md)
- Runner: [`substrate_event_reasoning_stage_a_envelope_v1.py`](../../../scripts/substrate_event_reasoning_stage_a_envelope_v1.py)
- Independent analyzer: [`analyze_substrate_event_reasoning_stage_a_envelope_v1.py`](../../../scripts/analyze_substrate_event_reasoning_stage_a_envelope_v1.py)
- Lock: [`event_reasoning_stage_a_envelope_v1_lock_20260926.json`](../../../evaluation/substrate_capability/event_reasoning_stage_a_envelope_v1_lock_20260926.json)
- Raw capture: [`substrate_event_reasoning_stage_a_envelope_v1_20260926.json`](../../../evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_20260926.json)
- Analysis: [`substrate_event_reasoning_stage_a_envelope_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_analysis_20260926.json)

The independent analyzer passes all ten checks, including an independently recomputed graph oracle, exact ordinary/enabled parity, six arm-order permutations, and proposal-count scaling. The fixture uses independent synthetic entities; it does not measure inter-entity graph coupling, production prevalence, cost on realistic seeds, or natural-task capability.
