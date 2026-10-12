# LLM transport role-separator inference v1 preregistration (2026-10-02)

## Question

On the connected 16-variable, width-8 transport graphs in the existing held-out census, does exact conditioning on one eight-variable layer and independent optimization of the other layer preserve exact MAP and held-out sign outcomes, and what measured runtime does it have relative to monolithic junction-tree inference?

## Frozen inputs and design

Use all ten disjoint held-out L12→L13 coefficient pairs, all three-state variables, and both learned and shuffled transport conditions from the existing source-locked task-graph cost assay. Each fresh worker reconstructs the graph and extracts live unary and pair factors. The model builder supplies source and target variable roles. Enumerate all 3⁸ assignments to the target layer; for each assignment, minimize each source variable independently over its three states, select the globally best assignment, and directly rescore the returned joint state. Compare to monolithic `junction_tree_map` using the registered min-fill order.

Measure substrate and graph construction, factor extraction, min-fill ordering, monolithic JT, role-conditioned solve, direct rescoring, peak Python allocation for the conditioned solver, process RSS, exact energy agreement, valid state membership, and held-out target-sign accuracy. Use three fresh workers and all 60 cells. Do not expose held-out target signs to either solver.

## Gates and claim boundary

Require stable source/native/export hashes, complete 3×10×2 coverage, connected 16-node/64-factor graphs, exact factor extraction, matching width certificates, monolithic and conditioned energy agreement within 1e-8, direct-rescore agreement, valid states, and no substrate mutation. Compare paired per-cell and aggregate solver times. The source/target partition is supplied by the graph builder and incurs no discovery cost in this assay; therefore the result measures the payoff of a known exact decomposition, not learned or automatic partition discovery. These are model-derived mode-sign outcomes, not language-task utility or natural graph prevalence.

## Artifacts

- Input task-graph census: [results](LLM_TRANSPORT_TASK_GRAPH_EXACT_CENSUS_V1_1_RESULTS_20261002.md)
- Baseline timing: [cost results](LLM_TRANSPORT_TASK_GRAPH_COST_V1_RESULTS_20261002.md)
- Runner, source lock, capture, and independent analysis: linked from the result report.
