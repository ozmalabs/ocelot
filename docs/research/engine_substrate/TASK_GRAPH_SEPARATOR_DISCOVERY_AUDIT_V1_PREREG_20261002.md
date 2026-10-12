# Task-graph separator discovery audit v1 preregistration (2026-10-02)

## Question

Can a graph-only minimum vertex-separator search recover the small separators in two available model-derived task-graph families, and how much proposal time does that search add relative to the measured exact role-conditioned solver?

## Frozen graph families

Use two source-locked task captures: the four-mode/eight-neuron connected K₄,₈ graphs from the Qwen3-0.6B layer-12 mode/neuron census (ten held-out inputs), and the eight-source/eight-target connected K₈,₈ transport graphs from the L12→L13 transport census (ten held-out inputs under learned and shuffled coupling). Each family has one topology repeated over its input/control rows; do not count repeated weighted rows as additional topology samples. Reconstruct only the captured complete bipartite skeletons, with arbitrary integer node IDs. The separator search itself receives edges and node count only, without layer-role labels.

For each graph, enumerate subsets by increasing cardinality, testing whether deletion leaves at least two nonempty connected components. Stop after testing every subset at the first cardinality with a valid separator. Record all minimum separators, number of tested subsets, component profiles, and elapsed time. Use three fresh worker processes and three searches per worker/topology. Check candidate sets for repeatability across workers.

## Cost accounting and gates

Report search-time median and spread. For K₈,₈, divide proposal time by its 20 unique held-out/control cells and compare that amortized cost with the separately source-locked v1.2 exact role-conditioned solve time. Also report proposal time divided by that median solve time as the number of future solves needed to amortize one search. Include solver and discovery figures side by side; do not imply runtime integration. For K₄,₈, report the search measurement only because no role-conditioned runtime capture exists for that family.

Require source/capture hashes stable, prior capture gates passing, correct edge counts/connectivity, full combinatorial coverage through the first valid separator size, identical candidate sets across repeated runs, and independently recomputed minima. These are only two authored bipartite model-derived families. The procedure is graph-only but exhaustive; it does not establish that this search is a practical or generally useful frame learner, natural-task separator prevalence, task utility, or scaling beyond 16 variables.

## Artifacts

The runner source-locks both prior task captures and the v1.2 conditioned-solver capture. Raw search timings, analyzer, lock, and result are linked from the results document.
