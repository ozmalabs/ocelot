# Bigville aggregate component-inference preregistration

## Question

When authored resident CAN networks are assembled into one shared substrate, can connected components be recovered from the extracted causal graph and used to factor exact MAP without changing the global optimum, and how does that compare with whole-graph junction-tree inference as resident count grows?

## Workload and design

Use the deterministic cast in `seeds/bigville_cast100.json`, `worlds.bigville_can_beliefs.build_resident_can_mt`, and the authored shared scenario evidence. For N=10, 25, 50, and 100 residents, build each resident's five-Concept, five-pair 3-state CAN in one native Substrate, then add one aggregate Microtheory containing all resident Concepts. Extract the aggregate network through `can_network_from_mt`.

Discover connected components only from the extracted causal edges, without using resident labels. Compare (a) min-fill plus global junction-tree MAP on the complete extracted graph, and (b) BFS component discovery plus independent exhaustive MAP on every induced component. An independent energy function scores both assembled states against the same extracted unary/pairwise model. Alternate solver order across three fresh workers to balance timing order.

## Gates and provenance

Lock protocol, runner, cast, Bigville builder, CAN extraction/solver and width code, Rust graph/PyO3 sources, native extension/build manifest, and commit at worker start/end. For each N require exactly N graph-discovered components, each containing five concepts and five undirected pairs; exact equality between aggregate extraction and the union of resident-level extracted factors; width at most 2; exact component/global energy agreement; valid 3-state outputs; and stable complete source hashes. Report build/extraction/width/global-solver/component-discovery-plus-local-solver time separately. Three worker replications per size.

## Claim boundary

This is a disconnected-component positive control over deterministic authored simulation data. It establishes graph-derived decomposition and exact factorization only when there are no cross-component factors. It does not establish bounded nonzero separators, connected-frame locality, natural population prevalence, BP/marginal quality, or native rule-engine frame scheduling.
