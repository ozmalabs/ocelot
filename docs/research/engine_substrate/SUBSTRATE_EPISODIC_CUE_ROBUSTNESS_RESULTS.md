# Episodic cue robustness and near-neighbor probe — 2026-09-25

## Result

The pre-locked two-arm probe confirms an exact-key retrieval boundary for these authored tasks. In both arms, all six exact cues reconstructed the correct target summary (12/12). With six lexically similar `northwest` events added, all six exact `north` requests still returned the correct target; no tested near-neighbor displaced an exact match.

All 12 truncated prefixes and all 12 paraphrased cue strings produced zero candidates and explicit `insufficient_information` responses. That is the expected conservative behavior under the frozen protocol, and it is also a clear limitation: this path does not perform partial-string or semantic cue matching at the request interface. The seed's `partial_cue_completion` name describes conservative completion for an exact matching cue that has overlapping episodes, not fuzzy matching over cue strings.

## Descriptive timing

Median query tick latency (single run, six queries per cell) was 0.180 ms exact, 0.151 ms truncated, and 0.151 ms paraphrase in the clean arm; in the near-neighbor arm it was 0.210, 0.184, and 0.178 ms. The values are too small and single-run to support a scaling or performance claim.

## Interpretation and limits

This probe establishes the behavior of one symbolic-key interface over six synthetic targets. The near-neighbor manipulation did not impair exact-key retrieval at this scale. It does not establish lexical robustness, semantic memory, natural-language paraphrase handling, or prevalence of exact-key access in real tasks. A future semantic-cue evaluation must include an explicit upstream cue-normalization/grounding mechanism and compare it against exact-key, no-memory, and distractor controls; this experiment does not silently reinterpret opaque keys as language.

## Reproducibility

- Protocol: [`SUBSTRATE_EPISODIC_CUE_ROBUSTNESS_PREREG_20260925.md`](SUBSTRATE_EPISODIC_CUE_ROBUSTNESS_PREREG_20260925.md)
- Pre-run lock: [`episodic_cue_robustness_lock_20260925.json`](../../../evaluation/substrate_capability/episodic_cue_robustness_lock_20260925.json)
- Runner: [`substrate_episodic_cue_robustness.py`](../../../scripts/substrate_episodic_cue_robustness.py)
- Independent auditor: [`analyze_substrate_episodic_cue_robustness.py`](../../../scripts/analyze_substrate_episodic_cue_robustness.py)
- Raw run: [`substrate_episodic_cue_robustness_20260925.json`](../../../evaluation/reports/substrate_episodic_cue_robustness_20260925.json)
- Independent analysis: [`substrate_episodic_cue_robustness_analysis_20260925.json`](../../../evaluation/reports/substrate_episodic_cue_robustness_analysis_20260925.json)

The pre-run lock contains seven input hashes and all matched during the independent audit. No exploratory worker was run before locking this probe.
