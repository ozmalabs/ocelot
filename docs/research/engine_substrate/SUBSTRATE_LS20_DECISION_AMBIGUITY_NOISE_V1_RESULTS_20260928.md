# LS20 decision under station ambiguity and recognition noise v1 results

**Status:** complete; all integrity and world-oracle gates pass. **Scope:** 120 paired synthetic LS20-shaped worlds; navigation is held to the quanta router.

## Outcomes

Each cell has 20 paired worlds. Clean recognition succeeds on all 20 in every cell. At sigma 0 and 8, the injected path also recognizes all 20 exact transform keys and succeeds on all 20, for both one and six stations. This includes 100% success with five distractor stations in this small sample.

| Stations | Pixel-noise sigma | Recognition exact | Clean success | Noisy success | Noisy failure reason | Paired noisy breaks/fixes | Exact McNemar p |
|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | 0 | 20/20 | 20/20 | 20/20 | — | 0/0 | 1.000 |
| 1 | 8 | 20/20 | 20/20 | 20/20 | — | 0/0 | 1.000 |
| 1 | 12 | 14/20 | 20/20 | 14/20 | 6 `no_waypoint` | 6/0 | 0.03125 |
| 6 | 0 | 20/20 | 20/20 | 20/20 | — | 0/0 | 1.000 |
| 6 | 8 | 20/20 | 20/20 | 20/20 | — | 0/0 | 1.000 |
| 6 | 12 | 17/20 | 20/20 | 17/20 | 3 `no_waypoint` | 3/0 | 0.250 |

Every observed sigma-12 recognition error was a refusal (`req_key=None`), rather than a wrong transform label. The six one-station refusals and three six-station refusals caused the corresponding no-waypoint failures. No noisy arm fixed a task that the paired clean arm broke. The one-station paired difference is nominally significant at this panel's unadjusted exact two-sided test; the six-station result is not. With 20 worlds per cell, the confidence bounds are broad (for 14/20: 0.481–0.855; for 17/20: 0.640–0.948). Treat the apparent station-count difference as unresolved sampling variation, not evidence that distractors improve performance.

## Cost, controls, and integrity

At sigma 0, clean/noisy exact outcome parity holds on all 40 pairs. The independent analyzer re-derived every intended shape transformation, exactly-one-matching-station condition, and 4-connected path to every station and goal. All 120 scenario hashes are unique; all task oracles and routes pass. Pre-run, post-run, and live source/input locks agree, and the locked native extension is fresh. The worker used 293.3 s wall, 540.7 s aggregate CPU, and 117,704 KiB peak RSS. Median per-episode wall time ranged from 0.95–1.37 s across arms/cells; noisy refusal cases are faster because the planner terminates without a waypoint. Timing is descriptive for this host and generated workload.

The initial preflight failure happened before any task result row; it is disclosed in the [amendment](SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V1_AMENDMENT_20260928.md), with its original lock retained separately. The corrected capture and analyzer passed all seven integrity gates. No task outcomes were used to change conditions or seeds.

## Interpretation and next gate

The held structure supports up to five distractor stations on these generated tasks when recognition is correct. Recognition noise is the observed failure boundary: sigma 8 survives all sampled cases, while sigma 12 produces conservative refusals rather than confidently selecting a wrong transform. This is a useful refusal profile, not a reliability curve: the noise threshold is task/render specific, the per-cell sample is small, and the two station-count samples use different generated worlds. Next run a preregistered multi-seed replication with enough worlds to estimate the sigma transition and confidence intervals by station count; include adversarially confusable transforms and measure whether a confidence/margin gate can recover degraded cases without increasing wrong-key execution.

Artifacts: [preregistration](SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V1_PREREG_20260928.md), [amendment](SUBSTRATE_LS20_DECISION_AMBIGUITY_NOISE_V1_AMENDMENT_20260928.md), [runner](../../../evaluation/substrate_capability/ls20_decision_ambiguity_noise_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_ls20_decision_ambiguity_noise_v1.py), [execution lock](../../../evaluation/substrate_capability/ls20_decision_ambiguity_noise_v1_lock_20260928.json), [raw capture](../../../evaluation/reports/ls20_decision_ambiguity_noise_v1/capture.json), [analysis](../../../evaluation/reports/ls20_decision_ambiguity_noise_v1_independent_analysis.json). The failed preflight lock is preserved at [preflight lock](../../../evaluation/substrate_capability/ls20_decision_ambiguity_noise_v1_preflight_lock_20260928.json).
