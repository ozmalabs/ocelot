# Linear P16 preregistration

Frozen after implementation commit `cbed5182588077bde8cd3a109650e322ec620f16`, a clean native build, the complete development allocation, and the focused regression suite. This document is committed by itself before any held-out allocation is run. The fixed JSON contract below is the analyzer's machine-readable freeze.

P16 measures native execution provenance and comparator conformance in two finite one-step panels: unrestricted permutations of four elements and a finite tool world whose legal actions depend on source-state parity. Each world gives the same initial state, goal, legal action map and complete one-step transition model to both arms. The arms are native graph frontier search and graph-selected, approved expression execution. Goal success, work and latency are descriptive; the registered pass concerns artifact identity, matching world inputs, valid external receipts, and zero-tolerance controls. The expression operator is fixed and human-approved in development for this conformance panel; this does not establish autonomous operator learning or general search.

The full draw contains 200 paired worlds per family and arm. Development uses seeds `26_160_000 + family_index*10_000 + draw`, with family order `permutation`, `state_dependent_tool`. Held-out uses the disjoint offset `1_000_000`. Each split also allocates 100 examples of each of five controls from its control base; each control kind receives a separate 1,000-seed block. No row or control is dropped. Held-out is executed once and archived outside git with raw and analyzer-output hashes.

The registered conformance gate requires exactly 800 held-out scored rows, 400 paired worlds, 200 records per arm/family, completed graph execution, matching paired world and access hashes, independently regenerated world identity, external receipt verification for each emitted action, and 100/100 passing cases for each missing-expression, stale-expression, tampered-expression, wrapper/native-mismatch and unauthorized-emission control. Analyzer tampering probes must detect all five changes. Any missing row, adapter, receipt, provenance mismatch or failed control fails the gate. Success-rate differences do not determine P16 pass/fail. The capability boundary is limited to finite one-step four-element worlds; there is no physical capability, broad tool-learning or general-search claim.

The host run is capped at 30 ticks, 100,000 native rule steps per tick, 200,000 graph nodes, 64 MiB serialized graph bytes, a 1,000,000-unit expression budget, and native primitive search at depth 1 with 256 expansions. The shared native ThinkingBudget is enabled for expression execution. All raw rows retain action, receipt, resource counters and elapsed time, including censored or failed work.

Development sanity allocation: 32 paired rows and 500 controls completed with no integrity or conformance failures; each of the five analyzer tamper probes detected its mutation. All 32 actions had verified external receipts. Primitive search solved 16/16 sampled worlds and the graph-expression arm solved 1/16. This is a descriptive development result and does not alter the frozen gate.

```json
{
  "phase": "linear-p16-v1",
  "implementation_commit": "cbed5182588077bde8cd3a109650e322ec620f16",
  "families": ["permutation", "state_dependent_tool"],
  "arms": ["primitive_search", "graph_expression"],
  "development": {"seed_base": 26160000, "split_offset": 0, "n_per_family_per_arm": 8, "controls_per_kind": 100, "control_seed_base": 26170000},
  "heldout": {"seed_base": 27160000, "split_offset": 1000000, "n_per_family_per_arm": 200, "controls_per_kind": 100, "control_seed_base": 27170000},
  "seed_formula": "26_160_000 + split_offset + family_index*10_000 + draw",
  "control_seed_formula": "control_seed_base + control_kind_index*1_000 + draw",
  "control_kinds": ["missing_expression", "stale_expression", "tampered_expression", "wrapper_native_mismatch", "unauthorized_emission"],
  "limits": {"max_ticks": 30, "max_steps_per_tick": 100000, "max_expression_nodes": 64, "max_graph_nodes": 200000, "max_serialized_graph_bytes": 67108864, "expression_budget": 1000000.0, "planner_expansions": 256, "planner_depth": 1},
  "criteria": {"heldout_rows": 800, "paired_worlds": 400, "records_per_arm_per_family": 200, "controls_per_kind": 100, "control_failures_allowed": 0, "receipt_failures_allowed": 0, "provenance_mismatches_allowed": 0, "analyzer_tamper_cases": 5, "analyzer_tamper_detections_required": 5},
  "task_generation": {"state_space_size": 24, "world_action_count": 24, "process_inputs_independent_of_goal": true, "state_dependent_tool_rule": "even source states permit even position permutations; odd source states permit all permutations"},
  "artifacts": {
    "source_bundle_sha256": "d40f4d26276af65aa027491f352830bfefdd9a08eacddde27d377b590f2163fc",
    "runner_sha256": "9be81bab1198d284cab20b0dd4dfd41fe0ad291b00b9dfce5abd5b1524855a38",
    "analyzer_sha256": "9dc8e567136c2e0709fa4f8548c7d7fbba28f0f3993fbf379571936b368c1e5a",
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96d9e1a45e623a1",
    "profile_sha256": "71789ecdedeb3ab28d8e430262fc5fc9c4ca7f4bd3093638b626d276ac780f16",
    "world_adapter_sha256": "0407c2d7eadb8c3f4be72f8c33bc6085436f1298a5dcc5f806391fcfe6aeb3ad",
    "dependency_closure_sha256": "9f205f0889858bb0d35a719ff85a858aa5c4b59239231a479e14e3211c782ae5",
    "engine_source_sha256": "3cac6758e73b997afc48a6cf5bc1ca99a907e950c180a5be37f3a231b2d8e3b1"
  },
  "runtime": {
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96d9e1a45e623a1",
    "build_source_fingerprint": "73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54"
  },
  "unsupported": ["physical world", "broad capability program", "motor program", "family program", "general open-world tool learning", "multi-step strategy quality"]
}
```
