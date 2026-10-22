# Linear P16 v2 preregistration

Version 1 is preserved as invalid for registered inference because its standalone freeze contains a malformed build-receipt SHA-256 (61 characters). The v1 held-out raw scorecard remains archived at `/tmp/cognition-linear-p16-heldout.json` with SHA-256 `02cebd99658af2fd539efde2b08a5845280b49a9385d373969defdd81e80b641`; its analyzer rejected the artifact mismatch and produced no report. It is not rescored under this version.

This version is frozen after implementation commit `18edc11662636d507e1afb76b6e7342f240e11be`, a clean native build, the complete development allocation, and the focused regression suite. This document is committed by itself before the v2 held-out draw. The fixed JSON contract below is the analyzer's machine-readable freeze.

The panel retains the P16 evidence question and criteria: native execution provenance and comparator conformance in a finite one-step unrestricted permutation world and a finite state-dependent tool world. Both arms receive the same initial state, goal, legal actions and complete transition model. The arms are native graph frontier search and graph-selected, approved expression execution. Goal success, work and latency are descriptive; the registered pass is exact artifact identity, paired input equality, completed execution, verified external receipts and zero-tolerance controls. This protocol does not claim autonomous operator learning, general search or physical capability.

The full draw contains 200 paired worlds per family and arm. Development uses seeds `26_160_000 + family_index*10_000 + draw`, family order `permutation`, `state_dependent_tool`. V2 held-out uses the untouched offset `2_000_000`, disjoint from both development and the invalid v1 held-out allocation. Each split allocates 100 examples of each of five controls from its control base; each control kind receives a separate 1,000-seed block. No row or control is dropped. V2 held-out is executed once and archived outside git with raw and analyzer-output hashes.

The registered conformance gate requires exactly 800 held-out scored rows, 400 paired worlds, 200 records per arm/family, completed graph execution, matching paired world and access hashes, independently regenerated world identity, external receipt verification for each emitted action, and 100/100 passing cases for each missing-expression, stale-expression, tampered-expression, wrapper/native-mismatch and unauthorized-emission control. Analyzer tampering probes must detect all five changes. Any missing row, adapter, receipt, provenance mismatch or failed control fails the gate. Success-rate differences do not determine P16 pass/fail. The capability boundary remains finite one-step four-element worlds only.

The host run is capped at 30 ticks, 100,000 native rule steps per tick, 200,000 graph nodes, 64 MiB serialized graph bytes, a 1,000,000-unit expression budget, and native primitive search at depth 1 with 256 expansions. The shared native ThinkingBudget is enabled for expression execution. Raw rows retain actions, receipts, resource counters and elapsed time, including failures.

V2 development sanity allocation: 32 paired rows and 500 controls completed with no integrity or conformance failures; all five analyzer tamper probes detected their mutations. All 32 emitted actions had verified external receipts. Primitive search solved 16/16 sampled worlds and graph-expression execution solved 1/16. This development result is descriptive and does not alter the frozen gate.

```json
{
  "phase": "linear-p16-v2",
  "implementation_commit": "18edc11662636d507e1afb76b6e7342f240e11be",
  "invalidated_v1_raw_sha256": "02cebd99658af2fd539efde2b08a5845280b49a9385d373969defdd81e80b641",
  "families": ["permutation", "state_dependent_tool"],
  "arms": ["primitive_search", "graph_expression"],
  "development": {"seed_base": 26160000, "split_offset": 0, "n_per_family_per_arm": 8, "controls_per_kind": 100, "control_seed_base": 26170000},
  "heldout": {"seed_base": 28160000, "split_offset": 2000000, "n_per_family_per_arm": 200, "controls_per_kind": 100, "control_seed_base": 28170000},
  "seed_formula": "26_160_000 + split_offset + family_index*10_000 + draw",
  "control_seed_formula": "control_seed_base + control_kind_index*1_000 + draw",
  "control_kinds": ["missing_expression", "stale_expression", "tampered_expression", "wrapper_native_mismatch", "unauthorized_emission"],
  "limits": {"max_ticks": 30, "max_steps_per_tick": 100000, "max_expression_nodes": 64, "max_graph_nodes": 200000, "max_serialized_graph_bytes": 67108864, "expression_budget": 1000000.0, "planner_expansions": 256, "planner_depth": 1},
  "criteria": {"heldout_rows": 800, "paired_worlds": 400, "records_per_arm_per_family": 200, "controls_per_kind": 100, "control_failures_allowed": 0, "receipt_failures_allowed": 0, "provenance_mismatches_allowed": 0, "analyzer_tamper_cases": 5, "analyzer_tamper_detections_required": 5},
  "task_generation": {"state_space_size": 24, "world_action_count": 24, "process_inputs_independent_of_goal": true, "state_dependent_tool_rule": "even source states permit even position permutations; odd source states permit all permutations"},
  "artifacts": {
    "source_bundle_sha256": "42519aaafea85acd135a91acc0d27600030b7791e920dc38853889286f5e10ef",
    "runner_sha256": "3737b8c812626feb286a454c88d1a944cec6da194dc79aa575384a9f5d07567d",
    "analyzer_sha256": "d7bb5620fc0295ea227635d500d0b06eb233ff4b6dd7d09fb8a26366cd9fe2d7",
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1",
    "profile_sha256": "71789ecdedeb3ab28d8e430262fc5fc9c4ca7f4bd3093638b626d276ac780f16",
    "world_adapter_sha256": "0407c2d7eadb8c3f4be72f8c33bc6085436f1298a5dcc5f806391fcfe6aeb3ad",
    "dependency_closure_sha256": "9f205f0889858bb0d35a719ff85a858aa5c4b59239231a479e14e3211c782ae5",
    "engine_source_sha256": "3cac6758e73b997afc48a6cf5bc1ca99a907e950c180a5be37f3a231b2d8e3b1"
  },
  "runtime": {
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1",
    "build_source_fingerprint": "73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54"
  },
  "unsupported": ["physical world", "broad capability program", "motor program", "family program", "general open-world tool learning", "multi-step strategy quality"]
}
```
