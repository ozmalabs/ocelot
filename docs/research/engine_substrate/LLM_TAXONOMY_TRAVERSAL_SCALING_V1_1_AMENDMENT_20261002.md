# LLM taxonomy traversal scaling v1.1 amendment

Date: 2026-10-02

## Reason

The first v1 capture preserved all per-query answers, but its independent analyzer used the wrong shuffled-control scoring direction: it counted false answers as correct for both positive and negative queries. The control score must count `true` for positive closure pairs and `false` for sampled unreachable pairs. This amendment corrects that analysis and calls for a fresh, separately locked three-worker capture so that the final result binds the corrected analyzer and protocol.

## Scope

The graph, query fixture, six-hop operating envelope, worker, timing procedure, and primary closure measures remain as preregistered in [v1](LLM_TAXONOMY_TRAVERSAL_SCALING_V1_PREREG_20261002.md). The amended analyzer additionally reports full-closure accuracy separately from accuracy within the implementation's six-hop bound. A correct six-hop implementation is expected to miss the three closure-positive pairs whose shortest paths exceed six edges; these remain closure errors and bounded-envelope successes.

The shuffled graph control is scored as balanced classification accuracy over the same positive and negative query sets. All source files, the original preregistration, this amendment, seed, query fixture, native binary, and native build manifest are included in a new source lock. The original v1 capture is retained as a pilot and excluded from the amended result.

## Claims not added

This remains a traversal utility and cost measurement over the harvested graph. The graph's internal closure is the oracle; external taxonomy correctness is not measured here. The assay does not measure treewidth, automatic frame discovery, natural cheap-cut prevalence, or downstream task utility. The source harvest's reported 27.2% valid-ancestor yield remains a separate content-quality measure.
