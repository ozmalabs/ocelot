# Episodic retrieval query-cost attribution — 2026-09-25

## Finding

The prior checkpoint sweep's sharp query latency growth is localized to one authored rule: `episodic_mark_overlapping_cues_for_conservative_completion`. That rule joins `Agent -recorded_episode→ Episode` twice, then checks whether the two cue keys are equal. In this all-unique-cue workload it still compares the episode population even though no collisions exist.

The pre-locked single-query audit measured its per-query candidate tests as exactly `2*N*(N+1)` at every tested N. It accounts for 96.2% of all rule candidate tests at N=78 and 98.5% at N=192. It accounts for 99.5% of all where evaluations at N=192. Per-rule term evaluations grow from 360 at N=6 to 368,640 at N=192. This is exact operation-count evidence of quadratic work for this rule on these graph sizes and source, not a general runtime theorem.

| Episodes N | Uninstrumented tick median | Per-rule audit tick median | All-rule candidate tests | Overlap-rule candidate tests | All-rule term evaluations |
|---:|---:|---:|---:|---:|---:|
| 6 | 0.488 ms | 0.514 ms | 134 | 84 | 835 |
| 24 | 0.657 ms | 1.204 ms | 1,358 | 1,200 | 7,369 |
| 78 | 2.396 ms | 6.301 ms | 12,806 | 12,324 | 65,851 |
| 192 | 12.003 ms | 34.489 ms | 75,278 | 74,112 | 380,833 |

Per-rule scale audit adds overhead: 1.05× at N=6 and 2.87× at N=192 in the paired medians. Use uninstrumented wall time for the current runtime envelope and integer counters for attribution. At N=192 the overlap rule generates 74,112 candidate tests per query while only two node inserts and nine attribute-set attempts occur across the whole tick; the discrepancy points to pair enumeration and filtering as the dominant work for this path, not write volume.

The control and audit readers returned identical expected summaries with recalled provenance at every size. Counter tests match the `2*N*(N+1)` identity in each of the 12 audited reader processes. All 11 frozen inputs matched. The audit run had three replicates per size; the preceding uninstrumented all-key scale sweep independently showed the same steep latency rise.

## Implication

The measured episodic operating path does not remain cheap merely because each cue is unique and the retrieval answer is one item. The collision-detection rule performs a population-wide pair check on every query tick. It is a concrete counterexample to assuming frame locality alone makes an implementation cheap: the rule explicitly joins the whole Episode population, and no frame/index boundary narrows it.

The next tractability experiment should compare an incremental or cue-indexed collision detector against the current rule under matched collision semantics, including all-unique and controlled-collision stores. It must preserve uncertainty caps for both members of a colliding pair, check old-checkpoint compatibility, and measure both read and write costs. This report does not prescribe or claim that optimization yet.

## Reproducibility

- Protocol: [`SUBSTRATE_EPISODIC_QUERY_ATTRIBUTION_PREREG_20260925.md`](SUBSTRATE_EPISODIC_QUERY_ATTRIBUTION_PREREG_20260925.md)
- Pre-run lock: [`episodic_query_attribution_lock_20260925.json`](../../../evaluation/substrate_capability/episodic_query_attribution_lock_20260925.json)
- Runner: [`substrate_episodic_query_attribution.py`](../../../scripts/substrate_episodic_query_attribution.py)
- Independent analyzer: [`analyze_substrate_episodic_query_attribution.py`](../../../scripts/analyze_substrate_episodic_query_attribution.py)
- Raw measurements: [`substrate_episodic_query_attribution_20260925.json`](../../../evaluation/reports/substrate_episodic_query_attribution_20260925.json)
- Independent analysis: [`substrate_episodic_query_attribution_analysis_20260925.json`](../../../evaluation/reports/substrate_episodic_query_attribution_analysis_20260925.json)

No exploratory worker was run before the lock. No test suite was run.
