# Live graph prompt-neighborhood cut measurement v2 results

## Result

The locked analysis processed ten worker records and collapsed exact duplicate
graph digests to five independent graph structures. Each prompt root was
compared with all other Message nodes available (2–8 per graph) and with up to
64 degree-ranked non-Message controls. Across 12 radius/cutoff cells, prompt
cut-per-frame-node was below the non-Message control median in only 9/60
graph-cell comparisons, while it was below the same-type Message census
median in 51/60. The two control arms point in opposite directions.

| Hub cutoff | Radius | Median prompt frame nodes | Median prompt cut/frame node | Median non-Message control cut/frame node | Graphs prompt lower than non-Message control |
|---:|---:|---:|---:|---:|---:|
| 10 | 1 | 21 | 1.857 | 0.034 | 0/5 |
| 10 | 2 | 41 | 1.208 | 0.033 | 0/5 |
| 10 | 3 | 53 | 0.955 | 0.033 | 0/5 |
| 100 | 1 | 22 | 1.857 | 1.484 | 0/5 |
| 100 | 2 | 45 | 0.872 | 1.398 | 3/5 |
| 100 | 3 | 60 | 0.867 | 0.004 | 0/5 |
| 1,000 | 1 | 23 | 18.182 | 1.533 | 0/5 |
| 1,000 | 2 | 410 | 1.054 | 1.387 | 3/5 |
| 1,000 | 3 | 776 | 0.252 | 0.117 | 0/5 |
| None | 1 | 23 | 18.182 | 1.533 | 0/5 |
| None | 2 | 410 | 1.054 | 1.387 | 3/5 |
| None | 3 | 776 | 0.252 | 0.117 | 0/5 |

For the non-Message arm, median degree gap is 5, maximum observed gap is 8,
and the median number of exact-degree controls is 3 of 64. The same-type
Message arm is a census rather than a sample: it has only 2–8 nodes per graph,
and prompt-root degree gaps are large (15–29). Those constraints explain why
the comparator arms disagree and limit inference. The 12 settings are
sensitivity checks over the same five graphs, not 60 independent samples.

## Interpretation

This assay does not support a robust cheap-cut claim for prompt-rooted task
neighborhoods. Under most settings, degree-ranked non-Message nodes have
lower crossing-edge cost per frame node; under the same-type Message census,
the prompt roots often have lower ratios, but those other messages are few
and substantially lower degree. The large frame expansion from 23 nodes at
radius 1 to 410–776 nodes at radii 2–3 without a strict hub cutoff also shows
that apparent low boundary ratios can depend on absorbing larger shared
regions.

These prompt-centered balls are structural probes, not inferred task frames.
The control comparison is type-confounded in one arm and weakly powered in
the other. Five repository-authored prompts do not estimate natural-task
prevalence. No treewidth, separator uniqueness, or runtime tractability was
measured. The result is useful negative/sensitivity evidence and motivates
independent task ownership review before attempting frame-local execution.

The v1 pilot is retained as a design diagnostic: its “degree-matched” Message
control arm was not well matched in realized degree. V2 explicitly reports
actual degree gaps and adds a broader control arm.

## Reproduction artifacts

- [V2 preregistration](LIVE_GRAPH_PROMPT_NEIGHBORHOOD_CUTS_V2_PREREG_20261004.md)
- [V2 evaluator](../../../evaluation/substrate_capability/measure_live_graph_prompt_neighborhood_cuts_v2.py)
- [V2 source lock](../../../evaluation/substrate_capability/live_graph_prompt_neighborhood_cuts_v2_lock_20261004.json)
- [V2 raw capture](../../../evaluation/reports/live_graph_prompt_neighborhood_cuts_v2_20261004.json)
- [Independent analysis](../../../evaluation/substrate_capability/analyze_live_graph_prompt_neighborhood_cuts_v2.py)
- [Analysis lock](../../../evaluation/substrate_capability/live_graph_prompt_neighborhood_cuts_analysis_v2_lock_20261004.json)
- [Analysis output](../../../evaluation/reports/live_graph_prompt_neighborhood_cuts_v2_analysis_20261004.json)
- [V1 pilot capture](../../../evaluation/reports/live_graph_prompt_neighborhood_cuts_v1_20261004.json)
- [V1 pilot protocol](LIVE_GRAPH_PROMPT_NEIGHBORHOOD_CUTS_V1_PREREG_20261004.md)
