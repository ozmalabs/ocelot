# Vision settling dependency-cut census

**Run:** 2026-09-25. **Evidence type:** deterministic static source census with symbolic arithmetic; no runtime costs measured. The preregistration, runner, independent analyzer, raw records and lock are linked below.

## Finding

The authored `vision_settle` seed combines local neighbor excitation with global competition. Its batched `st_settle` rule matches each `SUnit` through `r -has_sunit-> u`, reads `act` from local `sunit_neighbour` neighbors, and also folds over `NodesOfType(SUnit)` to read every SUnit's `act`; it writes `act_next`. Batched `st_commit` copies `act_next` to `act`. The global fold has no world/frame filter in its AST ([seed lines 162–352](../../../seeds/vision_settle.json)).

Therefore, for this rule signature, every output depends on all N current activations and its primal dependency graph is complete, with exact treewidth N−1. Under a hypothetical equal partition of k units per frame, each frame exposes N−k external state variables and N(N−k) ordered cross-frame input incidences. With N=64 and k=4, this is 60 boundary activations per frame and 93.75% of the global input incidences cross frame boundaries. At N=1024 and k=16, the boundary is 1008 activations per frame and the cross-frame share is 98.4375%. These are exact symbolic counts implied by the rule, not observations of scheduler work.

The current scoped settlement API is Microtheory-specific: it accepts `scope_mt: Option<NodeID>` and defines owned nodes as the Microtheory plus one `has_concept` hop ([`substrate.rs`](../../../runners/dsl/src/substrate.rs:5011), [`rewrite.rs`](../../../runners/dsl/src/rewrite.rs:2848)). No arbitrary SUnit-frame entry point was found. Thus this seed both refutes cheap-cut locality for this particular global-competition rule and exposes a substrate scope limitation for measuring spatial frames directly.

## Verification and artifacts

The independent analyzer passed all source-signature, case-matrix, arithmetic, and scope-API checks. See [`preregistration`](SUBSTRATE_VISION_SETTLE_CHEAP_CUT_CENSUS_PREREG_20260925.md), [`runner`](../../../scripts/substrate_vision_settle_cheap_cut_census.py), [`analyzer`](../../../scripts/analyze_substrate_vision_settle_cheap_cut_census.py), [`raw census`](../../../evaluation/reports/substrate_vision_settle_cheap_cut_census_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_settle_cheap_cut_census_analysis_20260925.json), and [`lock`](../../../evaluation/substrate_capability/vision_settle_cheap_cut_census_lock_20260925.json).

## Claim boundary and next gate

This establishes no frequency estimate for dense/global rules and no claim that all natural workloads lack cheap cuts. It identifies a concrete counterexample to treating cheap cuts as a universal property of the substrate's authored workloads. The analysis assumes one sheet's SUnits are the relevant population; because `NodesOfType(SUnit)` is graph-global rather than rooted at `r`, multiple sheets in one substrate may also compete across worlds. That semantic consequence needs a runtime probe.

Next test a concrete cortical-sheet instance with two sheets in one substrate, then measure the global fold's actual candidate/Term work as sheet size grows. Separately add a generic frame/scope mechanism before claiming that spatial frames can execute independently; retain global competition as a declared boundary variable or a global factor, rather than hiding it inside local tiles.
