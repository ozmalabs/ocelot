# LLM transport task-graph exact-inference census v1 preregistration

## Question and sample

Does exact CAN inference reproduce held-out adjacent-layer mode signs on the connected transport graph built from the learned Qwen3-0.6B L12→L13 transition, and does the learned transport carry more task-relevant signal than a value-preserving shuffle? The source export is `/applications/data/model_graph_work/transport_L12_13.npz`: 60 train and 10 disjoint held-out coefficient pairs. Fit the 32×32 ridge transport on all train pairs only (ridge 1.0); evaluate every held-out pair, with no outcome or width-based selection.

For each held-out pair, construct a 3-state graph with the eight largest-magnitude L12 coefficients as source variables, the first eight L13 modes as target variables, source unary fields from L12 coefficients, zero target unary fields, and bidirectional transport couplings. Run the learned transport and a deterministic flattened-value shuffle control on the same inputs. Extract factors from the live graph. Use min-fill as the JT order; independently solve each graph with generic factor-table variable elimination in extraction order. Also run the existing substrate BP path and calculate a linear transport baseline restricted to the selected eight source modes.

## Gates and measurements

Run three fresh workers over all ten inputs each. Require stable source/native/export hashes, paired identical topology, exact expected unary/pair factor extraction, connectivity, matching min-fill and triangulation width, exact JT/oracle/direct-energy agreement within 1e-8, valid returned states, and no graph mutation. Report held-out target-sign agreement for exact MAP, BP, linear transport, and shuffled-transport exact MAP; also report construction, extraction, ordering, exact solver, oracle, and BP time. No solver is allowed to read held-out target coefficients except the final scoring step.

## Claim boundary

This measures exact-inference integration and held-out mode-sign prediction for one learned adjacent-layer transition from one model, one layer pair, eight selected source modes, eight target modes, and ten held-out examples. It does not establish language-task utility, natural frame prevalence, learned separator discovery, other model/layer transfer, or system-level capability. A failed or weak shuffled control remains reportable and will constrain causal interpretation.

## Artifacts

- Runner: [llm_transport_task_graph_exact_census_v1.py](../../../evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1.py)
- Analyzer: [analyze_llm_transport_task_graph_exact_census_v1.py](../../../evaluation/substrate_capability/analyze_llm_transport_task_graph_exact_census_v1.py)
- Lock: [llm_transport_task_graph_exact_census_v1_lock_20261002.json](../../../evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_lock_20261002.json)
- Raw capture: [llm_transport_task_graph_exact_census_v1_20261002.json](../../../evaluation/reports/llm_transport_task_graph_exact_census_v1_20261002.json)
- Analysis: [llm_transport_task_graph_exact_census_v1_analysis_20261002.json](../../../evaluation/reports/llm_transport_task_graph_exact_census_v1_analysis_20261002.json)
