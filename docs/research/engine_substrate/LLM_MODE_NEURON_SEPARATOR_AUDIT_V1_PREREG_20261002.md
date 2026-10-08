# LLM mode-neuron separator audit v1 preregistration (2026-10-02)

## Question

Does exhaustive graph inspection of the connected task-derived mode-neuron factor graph reveal a small variable separator, and does conditioning on that separator reduce exact-inference state work relative to a width-optimal monolithic elimination order?

## Frozen data and method

Consume the source-locked three-worker capture from the [mode-neuron task-graph inference census](LLM_MODE_NEURON_TASK_GRAPH_INFERENCE_CENSUS_V1_RESULTS_20261002.md). Include all 30 rows. Check that every row has 12 variables, 32 factors, and all 32 edges between the four mode variables and eight neuron variables, as established by the locked census runner's graph construction and row counts. The rows are repeated held-out weighted instances of one topology; they are not 30 independent graph topologies.

Enumerate every variable subset as a candidate vertex separator. After removing each subset, compute connected components of the remaining induced graph. A separator is valid when at least two nonempty components remain. Report the smallest valid separator cardinality and all minimum separators. For operation comparison, use the optimal-side elimination order for K₄,₈: eliminate eight neuron variables first, then the four modes. Count table assignments visited as 8×3⁵ for the neuron eliminations plus 3⁴+3³+3²+3 for the final mode reductions. For the role-based separator candidate, condition on all four modes and independently minimize each of eight neuron variables: 3⁴×8×3 local assignments. These are transparent state-assignment proxies, not measured runtime or a full accounting of factor combination, memory, ordering, or parallel overhead.

## Gates and claim boundary

Require all 30 source rows and the source-locked capture hash, connected K₄,₈ topology in every row, exhaustive coverage of 2¹² subsets, and identical separator result across rows. Report the per-graph counts and ratios. The audit evaluates one model export, one layer, one fixed authored bipartite construction, and one four-mode separator. It cannot establish natural cheap-cut prevalence, automatic separator discovery, task utility, or scale behavior. A small separator only supports a tractability argument if its discovery and conditioned inference costs improve over the monolithic baseline.

## Artifacts

- Prior source capture: [inference census capture](../../../evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json)
- Audit runner: [separator audit](../../../evaluation/substrate_capability/llm_mode_neuron_separator_audit_v1.py)
- Source lock and result: generated alongside the run under `evaluation/substrate_capability/` and `evaluation/reports/`.
