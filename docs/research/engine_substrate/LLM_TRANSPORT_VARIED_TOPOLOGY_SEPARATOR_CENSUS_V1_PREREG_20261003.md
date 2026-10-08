# LLM transport varied-topology separator census v1 preregistration (2026-10-03)

## Question

Across the captured cross-model, multi-hop transport graphs with fan-in 1/2/4/8, how do graph-only minimum vertex separators, connected components, and treewidth vary with retained fan-in and model?

## Frozen source data

Use the full 960-row source-locked Qwen3-0.6B/1.7B cross-model transport capture: two models × four adjacent-layer hops × ten held-out rows × four evaluator-set fan-ins × three workers. Reconstruct each 16-node bipartite edge set from the locked `.npz` training/held-out coefficient exports by refitting the registered ridge-1.0 transports on the 60 training rows and repeating the stable per-target top-r fan-in selection. Require every reconstructed topology hash to match the captured row hash. Do not select rows by outcome, width, or runtime.

Apply one worker-specific opaque permutation to all 16 node IDs. Group graphs only by model, fan-in, and the exact anonymized node/edge signature. For each unique topology, enumerate candidate vertex subsets by increasing cardinality until all subsets at the first valid cardinality are checked. A valid separator leaves at least two nonempty components; if the graph is already disconnected, the empty set is reported. Record every minimum separator, component profile, separator-search time, and the repeated held-out rows covered by that topology. Compare the minimum separator with the width and component profile already recorded by the exact-inference capture.

## Gates and measures

Use three fresh workers. Require upstream capture and analyzer gates to pass, all 960 reconstructed hashes to match, source/export hashes to remain stable, full model/hop/input/fan-in coverage, stable unique-topology results, and independent recomputation of all unique separator results. Report topology count and separator/width distributions by model and fan-in, never treating repeated held-out rows as distinct topologies. This is a census of model-derived factors under evaluator-imposed fan-in, not a natural-task sample.

## Claim limits

This audit adds structural diversity and cross-model replication. It does not execute a separator-conditioned solver, learn fan-in, or establish natural cheap-cut prevalence. The edge pruning levels are imposed, the text set is generated, and exact inference outcomes measure internal coefficient prediction. No claim about general cognition or autonomous frame learning follows.
