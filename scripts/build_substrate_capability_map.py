#!/usr/bin/env python3
"""Generate and validate the machine-readable substrate capability inventory."""
from __future__ import annotations

import hashlib
import json
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs/research/engine_substrate/SUBSTRATE_CAPABILITY_MAP.md"
OUT = ROOT / "evaluation/substrate_capability/capability_map.json"
MAP_DIR = MAP.parent

AUDIT_NOTES = {
    "counterfactual_imagination_and_thoughtexperiment_harness": {
        "status": "measured_bounded",
        "canonical_state_owner": "Live state remains in the primary Substrate; imagination supports serialization, guarded native deep-copy, graph-page sharing, and reusable native snapshots. A Linux process-CoW prototype also forks the guarded substrate for in-place child rehearsal.",
        "python_shadow_or_indexes": "Python domains orchestrate detached and reusable native snapshot branches, read residuals, and preserve the primary graph/rule revision. The process-CoW child sends a residual receipt to the primary; branch state is not merged.",
        "normal_entrypoints": [
            ("domains/imagination.py", "imagine", "detached graph + active rewrite-rule copy, candidate/hypothesis application, graph-then-struct execution, and residual readout"),
            ("domains/self_correction.py", "imagine_and_check_convergence", "matched candidate rehearsal; candidate edits stay in detached rule store"),
            ("domains/self_correction.py", "imagine_candidate_batch", "fixed-revision candidate batch; compute baseline once, suppress per-candidate primary traces, and check primary graph/rule identity"),
            ("domains/collapse_model.py", "_bounded_forward_look", "bounded recurrence probe over detached state"),
            ("evaluation/substrate_capability/thoughtexperiment_self_change_blind_baseline_v1.py", "run_case", "source-locked blinded selection and proof-gate evaluation over seven fault profiles"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_self_change_blind_baseline_v1.py", "main", "independent candidate-admissibility, minimality, selection, and abstention analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_self_change_end_to_end_v1.py", "one", "graph-generated threshold candidate through CoW/full-copy rehearsal, canary, and Rust CAS commit"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_self_change_end_to_end_v1.py", "main", "independent paired-backend semantic, held-out, revision, commit, and phase-cost gates"),
            ("evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1.py", "worker", "source-locked syntax-only structural edit proposal coverage on five faulted rule forms"),
            ("evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v1.py", "main", "independent source-lock, candidate-accounting, repeatability, and proposal-coverage analysis"),
            ("evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2.py", "worker", "paired source-locked proposal coverage after adding unit threshold, guard-removal, and boolean-effect edits"),
            ("evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v2.py", "main", "independent paired v1/v2 coverage and repeatability analysis"),
            ("evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1.py", "worker", "source-locked graph-neighborhood relation evidence translated into candidate match-edge extensions"),
            ("evaluation/substrate_capability/analyze_blind_structural_repair_relation_evidence_v1.py", "main", "independent relation-proposal coverage, source-lock, candidate-accounting, and repeatability analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v1.py", "one", "source-locked opaque candidate generation, CoW branch scoring, graph-native selection/abstention, canary, and guarded CAS"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_blind_candidate_tournament_v1.py", "main", "independent lifecycle, control-margin, no-repair abstention, source-lock, and repeatability gates"),
            ("evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2.py", "one", "six-case source-locked boolean/threshold candidate tournament with ambiguity and relation controls plus phase timing"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_blind_candidate_tournament_v2.py", "main", "independent repair, abstention, canary/CAS, source-lock, timing, and repeatability gates"),
            ("evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1.py", "worker", "source-locked fixed-aperture no-op/candidate branch scaling on sparse path graphs through 32,768 decoys"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_candidate_branch_scaling_v1.py", "main", "independent output parity, primary graph/rule isolation, source-lock, and per-phase scaling analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2.py", "worker", "54-cell factorial scale sweep varying path/tree background size, task-chain aperture, and measured separator width"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_candidate_branch_scaling_v2.py", "main", "independent semantic/isolation/source gates and per-rule audit proving Exists work tracks actual boundary degree"),
            ("runners/dsl/src/py.rs", "PySubstrate::tick_graph_then_struct", "explicit graph-resident then native rewrite-rule cycle plan"),
            ("runners/dsl/src/py.rs", "PySubstrate::fork_full_copy_experiment", "guarded PyO3 exposure for isolated deep-copy control branches"),
            ("runners/dsl/src/substrate.rs", "Substrate::fork_full_copy_experiment", "native deep-copy control; isolates Γ epoch and refuses pending or external effects"),
            ("runners/dsl/src/substrate.rs", "Substrate::experiment_graph_rule_revision", "O(1) graph/rule semantic revision guard for fixed-primary candidate batches"),
            ("runners/dsl/src/substrate.rs", "Substrate::apply_experiment_graph_delta", "revision-checked staged graph-diff adoption; rejects stale or conflicting receipts before publishing"),
            ("runners/dsl/src/py.rs", "PySubstrate::replace_active_rule_by_name_if_revision", "atomic graph/rule-revision-checked successor-rule activation; parses before replacing and rejects active-name collisions"),
            ("runners/dsl/python/substrate_rs/__init__.py", "Substrate::replace_active_rule_by_name_if_revision", "Python API for revision-checked candidate rule activation"),
            ("evaluation/substrate_capability/thoughtexperiment_rule_activation_v1.py", "run", "source-locked recurrence/conversation activation with stale and malformed-candidate controls"),
            ("evaluation/substrate_capability/thoughtexperiment_persistent_adoption_v1.py", "run", "same-substrate sequential task evaluation plus controlled regression rollback and recovery"),
            ("runners/dsl/src/persist.rs", "apply_graph_delta", "staged graph/interner delta application with NodeID, edge-reference, and before-image validation"),
            ("domains/imagination.py", "commit_imagination", "revision-checked staged writeback with targeted native node/edge reads and retained legacy snapshot control"),
            ("runners/dsl/src/graph.rs", "TypedGraph::next_live_node_id", "next-live-ID query preserving adoption allocation semantics across trailing tombstones"),
            ("runners/dsl/src/py.rs", "PySubstrate::next_live_node_id", "Python-visible native next-live-ID query without graph serialization"),
            ("evaluation/substrate_capability/thoughtexperiment_commit_phase_profile_v1.py", "worker", "counterbalanced targeted-versus-legacy commit timing with trailing tombstone and full graph oracle"),
            ("runners/dsl/src/graph.rs", "TypedGraph::restore_node", "preserves restored identity and indexes; journals a live identity's before-image on replacement"),
            ("runners/dsl/src/py.rs", "PySubstrate::apply_experiment_graph_delta", "Python-visible atomic experiment residual adoption"),
            ("runners/dsl/python/substrate_rs/__init__.py", "Substrate::apply_experiment_graph_delta", "backend-neutral Python API for guarded residual adoption"),
            ("runners/dsl/src/substrate.rs", "Substrate::snapshot", "capture reusable immutable base without exposing storage backend"),
            ("runners/dsl/src/substrate.rs", "ExperimentSnapshot::fork", "create isolated mutable branch from captured revision"),
            ("runners/dsl/src/py.rs", "PySubstrate::snapshot", "default guarded PyO3 snapshot capture with storage-independent API"),
            ("runners/dsl/src/py.rs", "PySubstrate::_experiment_snapshot_with_backend", "private backend-selecting hook for controlled measurements"),
            ("runners/dsl/src/py.rs", "PySubstrateSnapshot::fork", "Python-visible branch creation from immutable base"),
            ("runners/dsl/python/substrate_rs/__init__.py", "Substrate::snapshot", "backend-neutral Python wrapper for reusable snapshots"),
            ("runners/dsl/python/substrate_rs/__init__.py", "SubstrateSnapshot::fork", "Python consumer API for isolated branch creation"),
            ("runners/dsl/src/graph.rs", "TypedGraph::mutation_version", "monotone graph-write revision used by fixed-primary isolation checks"),
            ("runners/dsl/src/substrate.rs", "Substrate::experiment_graph_rule_revision", "O(1) graph/rule semantic revision guard for fixed-primary candidate batches"),
            ("runners/dsl/src/graph.rs", "TypedGraph::mutation_version", "monotone graph-write revision used by fixed-primary isolation checks"),
            ("runners/dsl/src/graph.rs", "begin_experiment_delta_log", "Rust before-image journal records touched object state for sparse experiment residuals"),
            ("runners/dsl/src/persist.rs", "graph_experiment_delta", "exact conclusions and derived-only residual readout from touched graph objects"),
            ("runners/dsl/src/graph.rs", "TypedGraph::finish_rule_write_effect", "bounded per-effect before/after graph values with independent per-event and per-report caps"),
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules_effect_delta_report", "explicit effect-value observer, kept separate from endpoint-only event attribution"),
            ("evaluation/substrate_capability/thoughtexperiment_event_effect_cost_v1.py", "main", "source-locked endpoint/effect observer cost comparison with 45 isolated processes"),
            ("runners/dsl/src/graph.rs", "enable_rule_write_effect_target_attribution", "bounded effect-indexed node/edge targets without before-after value cloning"),
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules_effect_target_delta_report", "explicit target-only observer API with endpoint and full-value modes preserved"),
            ("evaluation/substrate_capability/thoughtexperiment_effect_target_cost_v1.py", "main", "source-locked endpoint/value/target comparison with 27 isolated runs"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_effect_target_cost_v1.py", "main", "independent target partition, parity, cap, source-lock, and cost analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_production_rule_diagnosis_v1.py", "execute", "four-arm diagnosis on the discourse_goal_resolve production seed rule with real shared-page omission branches"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_production_rule_diagnosis_v1.py", "main", "independent one-binding, exact cure graph, primary isolation, replication, and cost checks"),
            ("runners/dsl/src/graph.rs", "record_deferred_rule_patch_effect_origin", "opt-in bounded queue provenance from RulePatch identity to originating rule effect"),
            ("runners/dsl/src/substrate.rs", "Substrate::apply_pending_rule_patches", "emits deferred patch receipt writes under a unique originating ApplyRulePatch effect"),
            ("evaluation/substrate_capability/thoughtexperiment_deferred_patch_diagnosis_v1.py", "execute", "four-arm rematch/target/value/blind diagnosis through a real rule-patch queue drain"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_deferred_patch_diagnosis_v1.py", "main", "independent queue-origin, curing-branch, exact-parity, and primary-isolation gates"),
            ("evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_diagnosis_v1.py", "execute", "source-locked necessity diagnosis through production SetRuleClause queue drain"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_diagnosis_v1.py", "main", "independent source-origin, committed rule-change, necessity, abstention, and primary-isolation gates"),
            ("evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_competing_v1.py", "execute", "three-case competing, duplicate, and ambiguous deferred clause-edit experiment"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_competing_v1.py", "main", "independent queue-order, multi-origin, necessity, refusal, and primary-isolation gates"),
            ("evaluation/substrate_capability/thoughtexperiment_effect_trace_diagnosis_v1.py", "worker", "three-worker held-out effect-index localization over 80 randomized binding cases"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_effect_trace_diagnosis_v1_correction.py", "main", "independent effect-index accuracy, endpoint ambiguity, replication, and source-lock checks"),
            ("evaluation/substrate_capability/thoughtexperiment_effect_trace_counterfactual_v1.py", "execute_case", "full graph/rule rematching and effect-trace comparison followed by real shared-page omission branches"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_effect_trace_counterfactual_v1_correction.py", "main", "independent exact localization, counterfactual cure, primary-revision isolation, and paired cost checks"),
            ("evaluation/substrate_capability/thoughtexperiment_delta_journal_inference_v1.py", "run_branch", "source-locked nonzero-inference journal versus whole-graph-diff comparison"),
            ("evaluation/substrate_capability/thoughtexperiment_process_cow_self_correction_v1.py", "process_cow_candidate", "Linux os.fork page-CoW rehearsal; child returns residual over pipe and parent persists a receipt"),
            ("scripts/jabberwock_live_self_repair.py", "main", "configured live ARC episode measures regression, auto-mints a Fault, applies a rule edit, and gates recovery"),
            ("evaluation/substrate_capability/thoughtexperiment_live_self_repair_v1.py", "one", "three fresh source-locked repetitions of the live perception self-repair episode"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_live_self_repair_v1.py", "main", "independent episode, source-lock, process-identity, and recovery gates"),
            ("evaluation/substrate_capability/thoughtexperiment_fixed_revision_six_candidate_batch_v1.py", "run_batch", "six-candidate fixed-revision batch; shared baseline and O(1) semantic revision guard"),
            ("evaluation/substrate_capability/thoughtexperiment_snapshot_fork_contract_v1.py", "exercise", "source-locked reusable snapshot lifecycle, sibling, primary, and read-only isolation probe"),
            ("runners/dsl/src/bin/typed_graph_attr_index_lifecycle_probe_v1.rs", "main", "current-source graph attribute-index build, query, mutation, fork, and restore lifecycle measurement with exact parity gates"),
            ("evaluation/substrate_capability/typed_graph_attr_index_lifecycle_v1.py", "main", "source-locked multi-size/selectivity lifecycle capture and semantic-gate validation for TypedGraph attribute indexes"),
            ("evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_1.py", "main", "paired traced/untraced full-Substrate GenInfer lifecycle scaling with decoy codebooks, branch isolation, mutation, and graph restore"),
            ("evaluation/substrate_capability/analyze_geninfer_scope_index_lifecycle_v1_1.py", "main", "independent helper-work attribution, exact outputs, indexed membership, traced/untraced parity, and source-lock checks"),
            ("evaluation/substrate_capability/analyze_geninfer_scope_helper_residual_v1.py", "main", "post-hoc attribution of residual ShapeDecode, TransformDecode, DimInfer, GenInfer population and candidate work from locked traces"),
            ("evaluation/substrate_capability/cow_solver_alternatives_snapshot_v1_1.py", "worker", "20-worker native CAN solver-alternative consumer over one reusable snapshot and eager controls"),
            ("scripts/analyze_cow_solver_alternatives_snapshot_v1_1.py", "main", "exact solver/graph parity, primary/sibling isolation, revision, and read-only-fork gates"),
            ("evaluation/substrate_capability/cow_solver_alternatives_scale_v1_1.py", "worker", "18-worker 32/128/256-node path/banded solver-alternative scaling with reusable CoW and eager controls"),
            ("scripts/analyze_cow_solver_alternatives_scale_v1_1.py", "main", "72 branch-pair semantic/fixed-point parity and fork/settle cost summaries"),
            ("evaluation/substrate_capability/cow_solver_alternatives_scale_v1_2.py", "run", "18-worker per-rule native work attribution across 32/128/256 path and banded CAN graphs"),
            ("scripts/analyze_cow_solver_alternatives_scale_v1_2.py", "main", "global/per-rule candidate-test reconciliation and scoped work-counter scaling summaries"),
            ("evaluation/substrate_capability/cow_snapshot_write_density_locality_v1.py", "main", "70 fresh-process CoW/eager branch sweep over write density and graph-index locality"),
            ("scripts/analyze_cow_snapshot_write_density_locality_v1.py", "main", "semantic/isolation gates and per-cell fork, closure, PSS, and locality summaries"),
            ("evaluation/substrate_capability/fixtures/cow_snapshot_write_density/src/main.rs", "main", "native branch-local additive rule closure with density/locality treatments and PSS samples"),
            ("evaluation/substrate_capability/thoughtexperiment_productive_residual_snapshot_v1.py", "worker", "productive hypothesis-driven graph residual over eager, direct-page, and reusable-snapshot branches"),
            ("scripts/analyze_thoughtexperiment_productive_residual_snapshot_v1.py", "main", "fresh-process, convergence, exact nonempty-residual, primary, and later-fork gates"),
            ("evaluation/substrate_capability/thoughtexperiment_residual_adoption_v1.py", "worker", "15-worker productive residual adoption, stale-revision rejection, and malformed before-image atomicity panel"),
            ("scripts/analyze_thoughtexperiment_residual_adoption_v1.py", "main", "independent full-primary delta oracle, identity parity, rejection, and unchanged-state gates"),
            ("scripts/analyze_thoughtexperiment_reusable_snapshot_batch_v2.py", "main", "independent five-block exact-parity and changed-object residual analysis for the live candidate harness"),
            ("evaluation/substrate_capability/thoughtexperiment_fixed_revision_process_cow_batch_v1.py", "run_process_batch", "matched six-candidate Linux process-CoW versus native-copy batch comparison"),
            ("evaluation/substrate_capability/thoughtexperiment_branch_creation_cost_v1.py", "process_branch", "branch-setup-only eager-copy versus Linux page-CoW comparison with matched focus scope"),
            ("scripts/genmint_candidate_snapshot_efficacy_v1.py", "worker", "isolated GenMint candidate snapshot against frozen and exposure-without-consolidation controls; eager/graph-page semantic parity"),
            ("scripts/analyze_genmint_candidate_snapshot_efficacy_v1.py", "main", "independent input, outcome, schedule, isolation, and backend-parity checks for candidate-snapshot efficacy"),
            ("scripts/genmint_candidate_snapshot_efficacy_v1_1.py", "worker", "GenMint candidate-validation consumer over reusable SubstrateSnapshot forks"),
            ("scripts/analyze_genmint_candidate_snapshot_efficacy_v1_1.py", "main", "reusable snapshot revision, branch isolation, and exact efficacy-output parity gates"),
            ("domains/edit_ops.py", "find_edge_identity_sites", "enumerate edge and bounded node-attribute identity guard sites from a rule"),
            ("domains/edit_ops.py", "apply_add_edge_identity_guard", "materialize a mechanical absence-guard rule variant for a selected identity site"),
            ("evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1.py", "candidate_pool", "source-locked generated node-identity hypothesis pool, graph-Term evidence selection, and held-out score stages"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_editops_node_identity_v1_1.py", "main", "independent candidate-pool binding, selector, abstention, source-control, and held-out gates"),
            ("evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1.py", "run_branch", "generated rule-variant evaluation in isolated CoW branches and journaled selected-proposal receipt return"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_editops_node_identity_cow_v1_1.py", "main", "cross-backend semantics, held-out selection, branch isolation, receipt parity, and stale-retry rejection"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1.py", "main", "current-source 100k-node thought-experiment fanout replay over full-copy and shared-page snapshots"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_current_source_replay_v1.py", "main", "independent source-lock, semantic parity, and named-phase lifecycle coverage analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py", "main", "lifecycle-bounded graph-export and canonical-digest instrumentation for the 100k replay"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py", "main", "independent timer conservation, source-lock, and semantic parity checks"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1.py", "main", "matched fresh-process instrumentation on/off control over six backend/replicate pairs"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1.py", "main", "amended exact paired semantic projection and instrumented lifecycle timing analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1.py", "main", "32-worker eight-replicate matched instrumentation on/off control"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_2.py", "main", "independent paired confidence interval, semantic parity, and source-lock analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v1.py", "main", "18-worker source-locked 10k/100k/200k graph-node scale sweep with both snapshot backends"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_node_scale_v1_1.py", "main", "independent semantic, source-lock, timer, RSS, allocator, and scale-ratio analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v2.py", "main", "12-worker current-source 200k/400k/1m thoughtexperiment scale sweep on both snapshot backends"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_node_scale_v2.py", "main", "independent semantic, source-lock, timer, RSS, allocator, and million-node scale analysis"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_worker_v1.py", "run_worker", "matched full-digest and revision/receipt validation paths with full exact post-lifecycle parity audit"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_replay_v1.py", "main", "current-source replay loading the revision/receipt candidate worker"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_revision_receipt_cost_v1.py", "worker", "lifecycle-bounded export/digest instrumentation for the validation comparison"),
            ("evaluation/substrate_capability/thoughtexperiment_revision_receipt_validation_v1.py", "main", "16-worker paired 200k/1m full-digest versus revision/receipt validation sweep"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_revision_receipt_validation_v1.py", "main", "independent exact parity, semantic, provenance, instrumentation, and paired speedup analysis"),
            ("evaluation/substrate_capability/audit_thoughtexperiment_tracked_mutations_v1.py", "main", "static inventory of every public mutable TypedGraph method and expected revision/journal hook"),
            ("evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_edge_topology_v1_1.py", "main", "24-worker source-locked fixed-node/fixed-edge path, star, clustered-star, and random-tree topology fanout comparison"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_edge_topology_v1_1_1.py", "main", "independent 24-worker semantic, provenance, topology-size, lifecycle-timing, memory, and sparse-baseline comparison"),
            ("evaluation/substrate_capability/thoughtexperiment_touched_object_parity_v1_1.py", "main", "18-worker source-locked comparison of exact full-graph parity and journal-touched-node reconstruction, including untracked-mutation falsifiers"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_touched_object_parity_v1_1_1.py", "main", "independent semantic, touched-state reconstruction, false-negative control, exact-audit timing, and scale analysis"),
            ("runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1.rs", "main", "current-source 16-case semantic mutation matrix comparing journal deltas with whole-graph diff, phase checkpoints, and post-capture divergence"),
            ("evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_1.py", "main", "source-lock-validated confirmatory build and raw capture for journal mutation matrix"),
            ("runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_2.rs", "main", "expanded 17-case current-source journal parity matrix including direct mutable node access"),
            ("evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_2.py", "main", "locked v1.2 build and raw capture for direct-mutable-node journal coverage"),
            ("runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_3.rs", "main", "17-case journal matrix preserving complete journal and whole-graph diff payloads for independent recomputation"),
            ("evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_3.py", "main", "source-locked build/capture followed by independent raw-diff analysis"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_3.py", "main", "independently recomputes all journal/oracle equalities, phase diff, divergence control, and source-lock checks"),
            ("runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_4.rs", "main", "20-case journal and mutation-revision matrix including direct edge restoration, scope transition, and derived-index control"),
            ("evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_4.py", "main", "source-locked v1.4 evaluator build, capture, and independent raw-diff analysis"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_4.py", "main", "independently recomputes 20 journal/oracle equalities, revision expectations, scope and derived-index controls"),
            ("runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_5.rs", "main", "21-case semantic residual matrix including narrow-scope write and full-state oracle after clearing aperture"),
            ("evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_5.py", "main", "source-locked v1.5 evaluator build and independently analyzed capture"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_5.py", "main", "independent journal parity, revision, narrow-scope semantic residual, and source-lock checks"),
            ("runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_6.rs", "main", "26-case runtime matrix covering mixed and hidden edge writes under restricted apertures"),
            ("evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_6.py", "main", "source-locked current-source evaluator and capture runner"),
            ("evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_6.py", "main", "independent 26-case semantic residual, revision, aperture, and source-lock analysis"),
            ("evaluation/substrate_capability/audit_thoughtexperiment_tracked_mutations_v2.py", "main", "re-run current-source TypedGraph mutation hook inventory after hidden-edge before-image correction"),
            ("evaluation/substrate_capability/measure_live_graph_prompt_neighborhood_cuts_v1.py", "main", "initial prompt-root neighborhood cut pilot across radius/hub settings; same-type Message comparator retained as a design diagnostic"),
            ("evaluation/substrate_capability/measure_live_graph_prompt_neighborhood_cuts_v2.py", "main", "five-graph prompt-neighborhood cut sensitivity with same-type Message census and degree-ranked non-Message controls"),
            ("evaluation/substrate_capability/analyze_live_graph_prompt_neighborhood_cuts_v2.py", "main", "recomputes 60 graph/settings summaries and reports control degree gaps and sensitivity direction"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::tick", "Default production cycle plan; not equivalent to detached graph-then-struct execution"),
        ],
        "limits": ["The reusable snapshot interface captures a stable graph/rule revision and integrates with six-candidate rehearsal. Typed out/in adjacency buckets use a 64-shard persistent map on the shared-graph-page route, while most remaining graph query indexes and non-graph Substrate fields still copy eagerly. Direct shared-page batching has no stable gain at baseline/+1k, but wins all five paired blocks at +10k (1.16x median) and +50k (1.81x) on one synthetic task family and host; one of six candidates is useful in every arm. Isolation, a stable consumer contract, and future backend compatibility remain useful independently of speed.",
                   "Targeted thoughtexperiment commit reads pass exact full-graph, authorization, isolation, and trailing-tombstone allocation checks across 72 paired trials. At 1,000 nodes, targeted commit wins 9/9 pairs with 4.57–5.44x lower medians for attribute/add/mixed families; hub-delete wins 8/9 at 1.40x. This is synthetic, one-host evidence with edge population confounded by family, not a scaling law (THOUGHTEXPERIMENT_TARGETED_COMMIT_READS_V1_RESULTS_20261001.md).",
                   "Linux process-CoW is a guarded single-threaded prototype, not a portable Rust overlay or security sandbox; full native branch-local overlays are not implemented.",
                   "Sparse mutation-journal residual readout has exact parity across five mutation classes on one synthetic one-rule probe and measured 5.1x–222.7x scoped branch/readout speedups; this does not establish natural-task or corrected-rehearsal throughput.",
                   "A native full-copy control matches outcomes against the serialization route on one bounded self-correction fixture and is faster in the recorded single-host run.",
                   "The process-CoW prototype matches prediction and residual outcomes and returns a primary receipt, but its randomized-block end-to-end medians are slower at smaller sizes and within 2% of native deep copy at +10k.",
                   "Fixed-revision baseline reuse matches the standalone positive/negative outcomes and improves two-candidate throughput 1.15x–1.27x on one fixture; corrected-rehearsal end-to-end marginal cost and broad-panel experiment throughput remain unmeasured.",
                   "The six-candidate fixed-revision native batch passes exact nested residual parity and isolation and improves throughput 1.50x–1.79x over standalone six-candidate trials across 771–50,771 nodes; only one of six variants is useful on that task.",
                   "Effect-value tracing exactly localizes a failing node's writer effect in 80 synthetic cases when diagnosis receives only the native event report and target node; it does not beat full rematching/rule inspection. On an authored fan-out cap workload it adds about 148 MiB retained RSS/PSS and 2.51x observer time over endpoint events, so the API remains explicitly opt-in pending realistic diagnosis utility.",
                   "A uniquely sourced production ApplyRulePatch deferred event now preserves enqueue effect identity; target-only diagnosis cures the stale receipt in one branch with 3,521 median report bytes on a small fixture. Other deferred queues, multi-origin behavior, and natural-task utility remain open (THOUGHTEXPERIMENT_DEFERRED_PATCH_DIAGNOSIS_V1_RESULTS_20261005.md).",
                   "A production-derived four-edge discourse lifecycle rule with dynamic event binding passes fault-injection diagnosis through blind, rematch, target-only, and value-trace arms; every arm returns the same corrected branch graph without touching primary. Value trace reduces branch count 3→1 and is fastest on this tiny 3-replicate fixture; deferred effects and task prevalence remain open (THOUGHTEXPERIMENT_PRODUCTION_RULE_DIAGNOSIS_V1_RESULTS_20261005.md).",
                   "A bounded effect-target-only observer preserves effect-indexed node/edge attribution with no value payload: at report cap it uses 163,672 KiB median RSS/PSS and 326 ms versus 276,292 KiB / 600 ms for full effect values and 118,048 KiB / 231 ms for endpoint events. It reduces value-trace overhead but remains about 1.42x endpoint time and adds 44.6 MiB on this authored stress fixture; natural-task diagnosis benefit and transient peak bounds are open (THOUGHTEXPERIMENT_EFFECT_TARGET_COST_V1_RESULTS_20261005.md).",
                   "On an 80-case generated conjunction panel, complete graph/rule rematching and effect trace each find the right omission with one shared-page counterfactual branch; rematching's pooled median total is 0.526 ms vs 0.567 ms for tracing. The trace has no measured advantage over this stronger baseline on this family; production-derived joins, deferred effects, and realistic diagnosis remain open.",
                   "Matched process-CoW batching preserves exact nested results and primary isolation but reaches 0.58x–0.75x native-copy batch throughput across measured sizes; a native Rust branch overlay remains unimplemented.",
                   "Branch setup alone crosses over only at larger measured fixtures: process fork/scope is 1.91x faster at 50k nodes, near parity at 10k, and slower at baseline/+1k; this setup-only gain does not translate to full candidate throughput.",
                   "A source-locked field census accounts for all 25 TypedGraph and 50 Substrate fields and fails closed on declaration drift; its policy labels are a design checklist, not a semantic isolation proof.",
                   "A 10k-node reusable snapshot lifecycle probe passes isolation at fanout 1/4/16/32; the current five-block six-candidate runs match exact results/residuals against direct graph-page sharing, while reusable snapshots show no consistent additional speed over direct forks; separate GenMint and solver consumers pass reusable-fork semantic parity without an end-to-end speedup. Bounded native concurrent branch lifecycle, topology/write-density, and degree/placement panels now pass isolation and adjusted-reclamation gates. A retained-base high-churn panel passes all 200 waves across 10k/50k bases and fanout 4/16; first/last live allocation agrees and all adjusted post-drop residuals are zero. In that synthetic one-host panel, CoW is 7.66x–13.16x faster per full wave and uses 16.04x–22.75x less live allocator payload than eager copy. Broader full-Substrate memory amplification, concurrent commit/conflict behavior, natural-task consumer prevalence, and real serving-runtime integration remain open.",
                   "Revision-checked atomic graph-diff adoption passes exact full-primary delta-oracle parity plus stale-revision and malformed-before-image rejection across 15 fresh workers at 0/10k/50k nodes. This is one productive fixture; derived-only receipts can omit injected-node dependencies, graph-diff omits edge attrs, and revision-token coverage for in-place rule edits plus concurrent merge semantics need further audit.",
                   "A bounded native CAN solver-alternative consumer passes eager parity over 20 fresh workers. The 18-worker scale follow-up extends it to 32/128/256 Concepts and 72 alternatives with exact eager parity; at 256 Concepts fork costs are about 2.3 ms while scoped settling takes about 3.8–4.0 s. Operation work is now attributed: candidate tests grow about 62× for 4× N and 8× for 2× N; 99.3%–99.99% is local-bucket work, with the two Hebbian rules dominant. This is finite-size, one-host evidence, not a complexity law; coactivation and join-order controls are next. Neither result establishes general planning or optimality (COW_SOLVER_ALTERNATIVES_SNAPSHOT_V1_1_RESULTS_20261001.md). A source-locked v1 capture omitted its preregistered fork timing and is retained as semantic-only pilot evidence. vLLM-style shared-prefix/KV-block serving is a future adapter target only; this graph snapshot API has no model KV-cache integration and no prefix-serving evidence.",
                   "The write-density/locality sweep passes all 70 fresh-process rows: at 50,771 nodes CoW fork medians stay near 0.1 ms versus 11.5–14.2 ms eager and concurrent wall time favors CoW in 34/35 paired rows at each size. Sparse spread mutation costs more closure time than contiguous mutation; PSS advantage varies by density. This is one ring workload and one host, and supports reusable isolation/fork utility rather than a universal speed or memory claim (COW_SNAPSHOT_WRITE_DENSITY_LOCALITY_V1_RESULTS_20261001.md).",
                   "A task-generated residual-transfer panel replays the frozen ten-event common-ground task through direct closure, eager receipt/adoption, and shared-snapshot receipt/adoption. Eight fresh workers pass all event/goal, per-event progress, canonical graph, task-path, common-ground, terminal fixed-point, and branch-to-primary parity gates. The receipt arms each produce 48 nonempty event receipts across 80 events and 128 effects; serialized edge order differs from Direct in 32/80 event states despite canonical fact parity. A second mixed-act task finds 72/80 mismatches; source review implicates sorted `graph_diff.edges_added`, ordered receipt replay in `apply_graph_delta`, and slab-order serialization. Consumer order-contract audit remains open. With cold imports separated, median episode routes are 5.62ms direct, 13.65ms eager, and 11.01ms shared; this one authored fixture does not establish natural-task prevalence or speedup over Direct (THOUGHTEXPERIMENT_TASK_GENERATED_RECEIPT_TRANSFER_V1_1_RESULTS_20261001.md).",
                   "A second task-generated receipt panel replays the ten-event mixed-act dialogue using the production goal-event helper, ordinary settlement, eager receipt, and shared-snapshot receipt. Eight workers pass all event/goal, per-event progress, canonical graph, resolved-goal, common-ground, deferred-residual, terminal, and branch-to-primary gates. Each receipt arm emits 128 task receipts with 48 nonempty and 512 effects; wire order differs from Direct in 72/80 event states. Median routes are 6.03ms Direct, 22.15ms eager receipt, and 20.41ms shared receipt; this remains slower than ordinary execution and is one authored fixture, not natural-task prevalence (THOUGHTEXPERIMENT_MIXED_ACT_TASK_RECEIPT_TRANSFER_V1_1_RESULTS_20261001.md). The first v1 capture is retained as a JSON serialization failure diagnostic; only v1.1 is confirmatory.",
                   "Earlier corrected-residual scale probes use synthetic families and one host. Native concurrent branches now have bounded lifecycle, topology/write-density, degree-placement, and 200-wave high-churn coverage; full-state parity across arbitrary mutable Substrate fields, complete process-memory comparison, concurrent commit/conflict behavior, external-effect sandboxing, natural-task prevalence, and independent-host replication remain open.",
                   "The positive/negative control only establishes candidate-route discrimination on the frozen fixture; it does not establish general self-improvement.",
                   "A four-family five-policy proposal-utility panel completes four workers per family with source-stable, held-out-separated orders; all 80 policy cells eventually find a valid candidate, and every attempted branch preserves primary state and verifies its receipt. Experience rank gets 8/16 first-choice successes versus 0/16 for frozen rank, but default order and same-target memoization get 16/16; experience has no measured economic advantage after training acquisition cost. The preregistered exhaustive held-out candidate-scoring gate fails because scoring stops at first success (70/104 candidate instances covered), so results are descriptive, not confirmatory. Candidate generation and oracles remain host-authored; this is not self-improvement ([results](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_RESULTS_20261002.md), [protocol](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_PREREG_20261002.md), [lock](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_lock_20261002.json), [orders](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_orders_20261002.json), [scores](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_scores_20261002.json), [analyzer](../../../scripts/analyze_thoughtexperiment_blinded_proposal_utility_v1.py), [analysis](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_analysis_20261002.json))",
                   "A v1.1 complete-coverage replication scores all 104 held-out candidate instances and reproduces the ordering result, but the pre-capture lock omits the analyzer hash required by protocol, so retain it as descriptive. The v1.2 rerun locks 48 sources including the analyzer, completes 104/104 exhaustive candidate outcomes and 144 policy-prefix trials, and passes all seven analysis gates. Experience rank gets 8/16 first-choice passes against frozen rank's 0/16, while default and target memoization both get 16/16. Median policy-selection costs are 3.64s experience versus 36.4ms default, including training acquisition; exhaustive audit branches are costed separately. This measures ranking over the authored candidate set, not autonomous generation or self-improvement ([v1.1 results](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_1_RESULTS_20261002.md), [v1.2 results](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_RESULTS_20261002.md), [protocol amendments](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_3_AMENDMENT_20261002.md), [lock](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_2_lock_20261002.json), [orders](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_2_orders_20261002.json), [scores](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_2_scores_20261002.json), [analyzer](../../../scripts/analyze_thoughtexperiment_blinded_proposal_utility_v1_2.py), [analysis](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_2_analysis_20261002.json))",
                   "The proposal-generation boundary audit finds an existing graph-resident A8 structural composer that selects EditOps and emits variants for chosen-action rules; the navigation study passes with a supplied `flip` cue. The four-family candidate tasks include shape, recurrence, and control-classifier targets outside A8's current `writes_chosen_action` filter or operator vocabulary. Extending composition to those rule classes and routing its proposals into held-out isolated evaluation is the next delegation gate. Host-side applicability extraction/materialization must remain costed separately, and the cue must be recorded as input ([boundary audit](THOUGHTEXPERIMENT_PROPOSAL_GENERATION_BOUNDARY_AUDIT_20261002.md), [A8 results](MAC_FAC_A8_RESULTS.md), [navigation results](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_RESULTS_20261002.md)).",
                   "A8-to-Thoughtexperiment v1.3 passed graph attribution and adjacent held-out outcomes but failed the raw candidate digest prediction because engine metadata remained in the digest; graph selection was slower than default. v1.4 locks a semantic projection that excludes only generated name/hash/revision/UID fields, with seven mutation controls passing. Across four isolated workers, the graph proposal passes all 32 outcomes on eight previously unscored cardinal positions (offsets 2 and 4), with valid receipts, primary preservation, and no-cue abstention. Exactly one of six host candidates succeeds per worker; all eight analyzer gates pass. Median graph selection is slower (140.3ms vs 79.1ms), and the repetitions share one authored rule/fixture. Obstacle variation, new task families, independent environments, and autonomous learning remain open ([v1 result](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_RESULTS_20261002.md), [v1.1 result](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_1_RESULTS_20261002.md), [v1.2 scoring failure](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_2_RESULTS_20261002.md), [v1.3 result](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_3_RESULTS_20261002.md), [v1.4 result](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_4_RESULTS_20261002.md), [v1.4 analysis](../../../evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_4_analysis_20261002.json))",
                   "The production correction hook now persists typed success and failure outcomes in the graph; a later native fork inherits both without harness-created records or explicit transport. Across three fresh workers, the cold branch needs two trials while the experience branch ranks the previously successful repair first and passes in one (11/11 gates). This demonstrates automatic persistence and narrow cross-family search-effort benefit under authored candidate classes and utility oracle. The task, candidate fixes, outcome class, and oracle remain authored; automatic class discovery, attribution robustness, broader transfer, and natural-task prevalence are unmeasured ([results](THOUGHTEXPERIMENT_AUTOMATIC_OUTCOME_PERSISTENCE_TRANSFER_V1_RESULTS_20261001.md), [protocol](THOUGHTEXPERIMENT_AUTOMATIC_OUTCOME_PERSISTENCE_TRANSFER_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py), [raw capture](../../../evaluation/reports/thoughtexperiment_automatic_outcome_persistence_transfer_v1_raw_20261001.json)).",
                   "The v1.1 node-identity gate generates all eight edge/node-attribute guards from the shared edit-operator algebra. Across four workers, the native graph-Term selector chooses the actor+verb guard from training outcomes, and every selected proposal passes held-outs while seven alternatives fail. V1's duplicated-recipient fixture is excluded. The candidate pool still receives a harness-selected target and task; candidates run in fresh task contexts rather than a shared-page CoW branch. This is bounded candidate acquisition, not autonomous self-improvement ([results](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_V1_1_RESULTS_20261003.md), [protocol](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_V1_1_PREREG_20261003.md), [source lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1_1_lock_20261003.json), [orders](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_orders_20261003.json), [scores](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_scores_20261003.json), [analysis](../../../evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_analysis_20261003.json))",
                   "The v1.1 node-identity CoW integration runs all eight generated guards on isolated full-copy/shared-page branches. Across four workers the native graph-Term choice matches between backends; the selected actor+verb proposal passes every held-out, and its proposal receipt returns to the primary with exact content parity and atomic stale-retry rejection. Median eight-branch train/held-out lifecycles are 3.18/3.20 ms full-copy and 3.08/2.98 ms shared-page. The primary active rule remains unchanged; the receipt is proposal evidence, not production adoption. This is one harness-authored task family and not autonomous self-improvement ([results](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_COW_V1_1_RESULTS_20261003.md), [protocol](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_COW_V1_1_PREREG_20261003.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1.py), [source lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1_lock_20261003.json), [orders](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_orders_20261003.json), [scores](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_scores_20261003.json), [analysis](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_analysis_20261003.json))",
                   "The paired revision/receipt panel removes five whole-graph exports and digests from the candidate lifecycle: 28x/320x median lifecycle speedups for full-copy/shared-page at 200k/1m, and 2.3x–2.5x after adding back the exact post-lifecycle branch/primary digest audit. All 16 workers match the monolithic oracle and pass stale-revision, isolation, rule, and quiescence checks. This engineering result is conditional on tracked writes and complete journal coverage; the audit is on one synthetic workload and two replicates/cell, not a general production speedup claim ([results](THOUGHTEXPERIMENT_REVISION_RECEIPT_VALIDATION_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/thoughtexperiment_revision_receipt_validation_v1_analysis_20261004.json))."],
    },
    "production_visual_image_ingestion_and_frame_scoped_settling": {
        "status": "partially_audited",
        "canonical_state_owner": "Rust Substrate TypedGraph owns retinal luminance, drive, burst, and unit response attributes; WaveWorld holds NodeID references for one Retina and its cells.",
        "python_shadow_or_indexes": "WaveWorld.cells and its ordered cell-ID arrays are Python adapter indexes over Rust-owned graph nodes. Adapter frame arrays and the WaveWorld RNG live in Python; the measured trials use no random ignition.",
        "normal_entrypoints": [
            ("domains/wave_world.py", "WaveWorld::step", "explicit production adapter step; calls the normal tick after image ingest"),
            ("domains/wave_world.py", "WaveWorld::drive", "called by step when a frame is supplied; writes image facts for graph rules"),
            ("runners/dsl/src/py.rs", "PySubstrate::tick", "native graph rule-closure entrypoint used by WaveWorld.step"),
            ("runners/dsl/src/py.rs", "PySubstrate::tick_with_rule_state_trace", "opt-in native observer; follows the default cognitive-cycle plan and snapshots selected node attributes after complete named-rule invocations"),
            ("scripts/substrate_natural_image_rotation_equivariance_v1.py", "trial", "locked low-level natural-image transformation task through WaveWorld.step; compares original and rotated retinotopic SUnit response maps with an independent blank arm"),
            ("scripts/substrate_natural_image_act_rate_phase_diagnostic_v1.py", "capture_arm", "default-versus-traced natural-image input; records whole-rule `oo_sunit_rate` and settlement snapshots with final graph parity"),
            ("scripts/substrate_natural_image_rate_refresh_intervention_v1_1.py", "main", "diagnostic post-settlement intervention; re-invokes existing non-batch rate rule to no progress and checks the exact graph write footprint"),
            ("scripts/substrate_natural_image_rate_refresh_intervention_v1_2.py", "main", "eight-image replication of post-settlement rate refresh with exact 180-degree transform pairs and blank controls"),
        ],
        "alternate_entrypoints": [
            ("domains/wave_world.py", "WaveWorld::replay_step", "temporal replay path; directly writes bursts and bypasses luminance/change ingestion"),
            ("domains/complex_cells.py", "present", "isolated probe path; directly writes retinal bursts rather than calling WaveWorld.step(frame=...)"),
        ],
        "limits": ["Frame ownership is supplied by the task adapter; discovery and maintenance cost are not measured.",
                   "The default adapter does not expose per-rule internal phase snapshots or closure termination in its return value; an opt-in native whole-rule observer has exact final-graph parity on six paired checkpoint/scope fixtures, but does not expose per-binding writes.",
                   "A low-level 180-degree spatial-equivariance pilot covers eight BSDS300 patches and three adapted checkpoints; semantic recognition, broader natural-image prevalence, and frame-discovery cost remain unmeasured.",
                   "In the pilot, root-scoped act maps track the known spatial permutation while rate maps do not; output-specific task/readout agreement is unresolved.",
                   "A phase-local follow-up finds the rate rule runs before final settlement in all 18 calls; settlement then changes act after rate is stamped for that step.",
                   "An eight-image post-settlement refresh replication favors the expected rotation map in 22/24 root-scoped image/checkpoint pairs; global refresh is nonzero in only one checkpoint and does not favor the transform. The intervention is not the production schedule, and semantic recognition remains unmeasured."],
    },
    "typed_graph_node_edge_state": {
        "status": "partially_audited",
        "canonical_state_owner": "Rust Substrate.graph (TypedGraph); PySubstrate stores the Rust Substrate behind Arc<Mutex<...>>.",
        "python_shadow_or_indexes": "substrate.graph.TypedGraph maintains Python indexes and a per-node shadow for values the native Value type cannot serialize; serializable graph attributes are written through to Rust.",
        "normal_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::add_node", "default Python API"),
            ("runners/dsl/src/py.rs", "PySubstrate::add_edge", "default checked Γ API"),
            ("runners/dsl/src/py.rs", "PySubstrate::remove_edge", "default Python API"),
            ("runners/dsl/src/py.rs", "PySubstrate::remove_node", "default Python API"),
            ("runners/dsl/src/py.rs", "PySubstrate::set_attr", "default Python API"),
            ("runners/dsl/src/graph.rs", "TypedGraph::insert_node", "Rust storage primitive; called through Substrate"),
            ("runners/dsl/src/graph.rs", "TypedGraph::insert_edge", "Rust storage primitive; called through Substrate"),
            ("runners/dsl/src/graph.rs", "TypedGraph::delete_edge", "Rust storage primitive; called through Substrate"),
            ("runners/dsl/src/graph.rs", "TypedGraph::set_node_attr", "Rust storage primitive; called through Substrate"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::add_edge_unchecked", "explicit unchecked path; bypasses Γ admissibility"),
            ("runners/dsl/src/py.rs", "PySubstrate::remove_edge_unchecked", "explicit unchecked path"),
            ("substrate/graph.py", "TypedGraph::_insert_edge", "Python compatibility/internal path; delegates to unchecked native mutation"),
        ],
        "limits": ["Direct Rust TypedGraph primitives are public and can bypass Substrate-level admissibility and dirty tracking if called outside the intended owner path.",
                   "Persistence, all adapters, and the complete set of shadow attributes have not been audited in this row."],
    },
    "terms_and_value_evaluation": {
        "status": "partially_audited",
        "canonical_state_owner": "Rust Substrate.terms owns the TermArena; evaluate reads the Rust TypedGraph through EvalCtx.",
        "python_shadow_or_indexes": "No separate Python term-value store was identified in the audited evaluation path; host term construction/loading remains outside this row's audit.",
        "normal_entrypoints": [
            ("runners/dsl/src/term.rs", "evaluate", "Rust evaluator; invoked by interpreted rule matching and effect evaluation"),
            ("domains/substrate_extension.py", "build_primitive", "host-authored Term-tree construction, admission, native evaluation, and installation of registered computational primitives"),
            ("runners/dsl/src/rewrite.rs", "match_rule_each", "default rule matching; uses a compiled JIT predicate automatically when the where-clause is eligible, otherwise interprets Terms"),
            ("runners/dsl/src/rewrite.rs", "apply_rule_full", "rule effect application; evaluates Term-valued effects"),
            ("evaluation/substrate_capability/spectral_io_oracle_v1_6.py", "main", "current-source, locked forward-construction and inverse-refusal replay"),
            ("evaluation/substrate_capability/analyze_spectral_io_oracle_v1_6.py", "main", "amended independent native-term versus direct-DFT verification"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::scale_audit_set_enabled", "opt-in instrumentation; counters are off by default"),
            ("runners/dsl/src/py.rs", "PySubstrate::scale_audit_set_per_rule_enabled", "opt-in attribution; requires global audit"),
        ],
        "limits": ["Eligible where clauses can execute through JIT instead of term::evaluate.",
                   "The current substrate_extension computational builder registry contains one fixed spectral_value recipe. Its formula and negative control are authored in Python; v1.6 verifies current-source execution/refusal behavior but not substrate selection or invention ([results](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_RESULTS_20261001.md), [preregistration](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_PREREG_20261001.md), [analysis amendment](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_ANALYSIS_AMENDMENT_20261001.md), [raw](../../../evaluation/reports/spectral_io_oracle_v1_6_raw_20261001.json), [analysis](../../../evaluation/reports/spectral_io_oracle_v1_6_analysis_20261001.json)).",
                   "Term variants with host callbacks, framebuffer, concept resolution, caches, and derivation dispatch are not all audited here."],
    },
    "rule_matching_effects_fixpoint": {
        "status": "partially_audited",
        "canonical_state_owner": "Rust Substrate owns the TypedGraph, TermArena, and loaded RewriteRule vector during execution; Python seed loading and orchestration construct/configure the workload.",
        "python_shadow_or_indexes": "PySubstrate holds the Rust Substrate behind Arc<Mutex<...>>; Python seed manifests are input/configuration, not the live rule-execution state.",
        "normal_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::run_rules", "default Python rule-closure API"),
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules", "default Rust rule-closure API"),
            ("runners/dsl/src/rewrite.rs", "run_rules_opts", "default native matching/fixpoint engine"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::run_rules_report", "explicit reporting API"),
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules_report", "explicit typed status/report API"),
            ("runners/dsl/src/py.rs", "PySubstrate::run_rules_scoped", "explicit scoped scheduling API; opt-in"),
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules_scoped", "explicit scoped scheduling API; opt-in"),
            ("runners/dsl/src/py.rs", "PySubstrate::run_rules_scoped_delta_report", "scoped fixed point plus pending deferred-effect reporting; measured multi-binding behavior is not equivalent to global closure"),
            ("scripts/substrate_all_queue_scoped_fallback_v1.py", "worker", "27-worker full/scoped/scoped-plus-fallback five-queue semantic and work comparison"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v1.py", "main", "checks exact settled graph and five-family counter parity across full and scoped/fallback arms"),
            ("scripts/substrate_all_queue_scoped_fallback_v2.py", "worker", "27-worker distinct-write and dependent-rule scoped/full parity workload"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v2.py", "main", "strict byte-order graph, dependent-rule, and five-queue semantic checks"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v2_state_order.py", "main", "post-hoc separates canonical edge-fact equality from insertion-order equality"),
            ("scripts/substrate_all_queue_scoped_fallback_v3.py", "worker", "27-worker one-shot last-match continuation over distinct scoped/full bindings"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v3.py", "main", "checks strict graph order and order-sensitive selected-node parity"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v3_state_order.py", "main", "post-hoc canonical edge-fact and graph-order comparison"),
            ("scripts/substrate_all_queue_scoped_fallback_v4.py", "worker", "27-worker direct handled_mid-first matcher continuation under full and scoped closure"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v4.py", "main", "strict graph wire, matcher-selected edge, and five-queue gates"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v4_state_order.py", "main", "post-hoc distinguishes slab serialization order from matcher-selected order"),
            ("scripts/substrate_all_queue_scoped_fallback_v5_1.py", "worker", "27-worker cross-binding unique-driver deletion with M=1 single-binding control"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v5_1.py", "main", "300 semantic, five-queue, and trace-reconciliation gates; canonical facts separated from wire order"),
            ("scripts/substrate_all_queue_scoped_fallback_v6.py", "worker", "27-worker pre-mutation where-snapshot probe with successor predicate invalidation"),
            ("scripts/analyze_substrate_all_queue_scoped_fallback_v6.py", "main", "300 where-invalidation, canonical parity, queue, and trace gates"),
            ("evaluation/substrate_capability/can_coactivation_population_join_order_v1.py", "worker", "45-worker read-only CAN Hebbian matcher panel across independently varied Q and sparse-first clause order"),
            ("scripts/analyze_can_coactivation_population_join_order_v1.py", "main", "installed-order, exact graph, fixed-point, and 90-arm per-rule candidate reconciliation gates"),
            ("evaluation/substrate_capability/can_productive_coactivation_closure_v1.py", "worker", "45-worker productive mint/reweight closure over N and Q, with audited and uninstrumented arms"),
            ("scripts/analyze_can_productive_coactivation_closure_v1.py", "main", "per-pair mint/reweight oracle, graph growth, canonical order parity, instrumentation parity, and counter gates"),
            ("evaluation/substrate_capability/can_install_time_join_order_v1.py", "worker", "graph-first CAN rule installation over the productive Q ladder, compared with locked empty-graph controls"),
            ("scripts/analyze_can_install_time_join_order_v1.py", "main", "independent installed-order replay, cross-capture graph parity, productive outcomes, and counter reconciliation"),
            ("evaluation/substrate_capability/substrate_matcher_prefix_work_v1.py", "run_worker", "108-worker path/star/cycle matcher-prefix work panel on independent graph topologies"),
            ("scripts/analyze_substrate_matcher_prefix_work_v1.py", "main", "exact independent adjacency enumeration versus native per-clause candidate counts"),
            ("evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1.py", "arm", "90-worker sparse/balanced typed-relation matcher panel across path/star/cycle rules"),
            ("scripts/analyze_substrate_mixed_relation_join_cost_v1.py", "main", "independent prefix simulation and exhaustive 24-order work comparison per graph"),
            ("evaluation/substrate_capability/can_mixed_degree_join_order_v1.py", "run_arm", "effect-free native enumeration of production CAN Hebbian pattern across uniform and source-skewed pair layouts"),
            ("scripts/analyze_can_mixed_degree_join_order_v1.py", "main", "typed prefix-work reconciliation and exhaustive 24-order CAN clause comparison"),
        ],
        "limits": ["The exact active rule set and Python/native ownership boundary vary by seed and application.",
                   "The legacy run_rules count may exceed max_steps at a pass boundary; use report status for budget semantics.",
                   "Termination guarantees for unrestricted fresh-node minting and broad interacting rule families are not established.",
                   "A 36-worker exhaustive 24-order probe of the production CAN Hebbian pattern matches all native prefix counters and finds 2.58–8.33× installed-order regret. The minimum sequence is one membership edge, both coactivation links, then the second membership edge; at N=32,Q=248 it reduces tests from 70,496 to 8,464. Uniform and source-skewed populations are identical on this fixture. This is effect-free and N≤32; production guards/effects and other rule families remain unmeasured (CAN_MIXED_DEGREE_JOIN_ORDER_V1_RESULTS_20261001.md).",
                   "A 90-worker mixed-relation synthetic positive control finds the rarest-edge/connected-edge install order minimum-work in all 90 uniform, nested-support path/star/cycle cases after exhaustive 24-order comparison. One N relation among three 4N relations cuts work 75%; doubling N doubles tests. This does not transfer to nonnested/skewed support or repeated-edge/two-hop production patterns; the CAN Hebbian profile still shows 2.28–2.89× avoidable work (SUBSTRATE_MIXED_RELATION_JOIN_COST_V1_RESULTS_20261001.md).",
                   "The 108-worker matcher prefix panel validates exact candidate-test counts for four-clause one-relation path/star/cycle patterns at N≤32; star4-on-star grows 17.6× from N=16 to 32, while path and ring controls are near 2×. Reversed order is neutral in these homogeneous controls. Mixed-relation selectivity, productive arbitrary patterns, and larger graphs remain unmeasured (SUBSTRATE_MATCHER_PREFIX_WORK_V1_RESULTS_20261001.md).",
                   "A source-locked 45-worker controlled CAN panel confirms the two production Hebbian rules can productively mint and reweight to an independently checked fixed point. Sparse-first order reduces candidate tests 72.74–99.19% across tested nonempty Q; at N=128,Q=16,256 the authored-order arm tests 668M candidates and takes 57.3s instrumented versus 5.40M and 2.37s sparse-first. A graph-first installation replay predicts all 180 installed orders and finds the cardinality heuristic chooses `has_concept` first for Q>N even when the pattern is sparse-authored, costing 2.28–2.89× explicit sparse-first candidate work. This is synthetic one-family evidence, not natural distribution or asymptotic tractability; other rule shapes and topologies remain open (CAN_PRODUCTIVE_COACTIVATION_CLOSURE_V1_RESULTS_20261001.md; CAN_COACTIVATION_POPULATION_JOIN_ORDER_V1_RESULTS_20261001.md; CAN_INSTALL_TIME_JOIN_ORDER_V1_RESULTS_20261001.md).",
                   "An initial locked R={1,8,32}, M={1,4,16} five-queue probe exposed a scoped first-binding bug for non-batch rules; the scoped path was changed to drain all distinct snapshotted bindings. The rebuilt v1.1 replay passes 300/300 checks on one positive-join/direct-owner fixture. A v2 dependent-rule fixture has identical canonical node/edge facts in 27/27 workers, but exact graph edge order matches in only 9/27. V3/v4 matcher continuations select the same NodeID in all 27 full/scoped-plus-fallback pairs. Source audit clarifies that graph serialization uses edge-slab slot order while matcher scans use per-type/adjacency indexes; v4's last-slab-edge oracle was invalid and is disclosed. The first pre-fix raw capture was overwritten and is disclosed as unauditable. V5 introduced a self-loop M=1 fixture with no matches under injective variable bindings and retained an invalid serialized-tail oracle; corrected v5.1 uses M=1 only as a single-binding control and tests cross-binding deletion at M=4/16, passing canonical fact parity in 27/27 workers and 300/300 gates, with exact wire parity 9/27. V6 additionally turns each later binding's where predicate false after snapshot and passes all 300 gates with canonical parity 27/27; this is one attribute-where pattern, not arbitrary-predicate semantics. Projection deduplication and general frame scopes remain open (SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V1_1_AMENDMENT_20261001.md; SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V2_RESULTS_20261001.md; SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V3_RESULTS_20261001.md; SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V4_RESULTS_20261001.md; SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V5_1_RESULTS_20261001.md; SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V6_RESULTS_20261001.md)."],
    },
    "structural_width_frame_cuts_and_hierarchy": {
        "status": "partially_audited",
        "canonical_state_owner": "Offline graph-width and census routines own no persistent substrate state; they consume copied node/edge lists. The selected solver-dispatch path reads/writes through the Python WorldAdapter, while problem_decomposition returns clique bags and a refusal/attempt report.",
        "python_shadow_or_indexes": "The synthetic and rule-dependency censuses are standalone Python diagnostics. They do not create runtime frames or partition native rule execution. race_projections additionally mints graph-resident ProjectionCandidate bookkeeping nodes.",
        "normal_entrypoints": [
            ("domains/graph_treewidth.py", "exact_treewidth", "bounded exact diagnostic; returns no exact result above max_exact_n"),
            ("domains/graph_treewidth.py", "min_fill_upper_bound", "direct heuristic API; used by selected solver paths"),
            ("domains/graph_treewidth.py", "treewidth_bound_check", "caller-invoked bounded-width gate; exact only below max_exact_n, otherwise upper-bound gate"),
            ("domains/graph_treewidth.py", "build_elimination_triangulation", "called after the decomposition gate accepts"),
            ("domains/can_junction_tree.py", "junction_tree_exact_settle", "explicit exact-inference entrypoint with width gate; commits selected state by default"),
            ("scripts/substrate_live_frame_rule_scope_capture_v1_2.py", "run", "current-source three-worker live frame and native RuleUID scope capture after provenance-checked engine rebuild"),
            ("scripts/analyze_live_frame_rule_scope_capture_v1_2.py", "main", "independent analysis of repeated current-source request traces and same-request rule-definition coverage"),
            ("scripts/analyze_live_frame_rule_scope_structural_v1_2.py", "main", "recomputes protocol-declared task-cut sizes, boundaries, width bounds, and cross-worker stability from raw capture"),
            ("evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py", "main", "current-source, provenance-guarded full-graph replay across five authored task routes and two fresh workers each"),
            ("evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py", "main", "independent explicit Goal/Event ownership reconstruction, task outcome, boundaries, and per-condition replica parity"),
            ("evaluation/substrate_capability/analyze_live_conversation_task_anchor_paths_v2.py", "main", "current-source typed-path diagnostic; reachability remains candidate evidence, not ownership"),
            ("evaluation/substrate_capability/build_live_task_anchor_review_packet_v2.py", "main", "blinded one-worker-per-task ownership review packet with second replicate held out"),
        ],
        "alternate_entrypoints": [
            ("domains/problem_decomposition.py", "decompose_problem", "explicit projection-race/decompose-or-refuse API; refinement defaults off"),
            ("domains/solver_dispatch.py", "solve_decompose", "opt-in resolver selected by solver-dispatch goal"),
            ("scripts/substrate_structural_census_pilot.py", "recursive_partition", "offline synthetic structural diagnostic only"),
            ("scripts/substrate_rule_dependency_census.py", "native_access_audit", "offline static rule-access census diagnostic"),
        ],
        "limits": ["No general learned/authored frame hierarchy is consumed by the native rule engine.",
                   "The partition census uses synthetic inputs and hand-selected ID-contiguous/shuffled orders; it does not prove natural cheap cuts.",
                   "The decomposition result builds clique bags but does not itself dispatch a per-clique solver.",
                   "Current-source live task cuts are only 3 and 8 nodes with 20 and 38 crossing incidences; their induced min-fill upper bounds of 1 and 2 do not bound rule-factor width. 93/401 active runtime rule definitions contain whole-population terms. Discovery cost and complete task-relevant dependencies/domains remain unmeasured (SUBSTRATE_LIVE_FRAME_RULE_SCOPE_CAPTURE_V1_2_RESULTS_20261004.md).",
                   "The current-source five-task harvest finds explicit prompt-linked Goals in only two conditions; no-hub graph reachability overassigns plausible Goals, and single-request graphs produce trivial one-frame projections. The blinded current packet has no independent human labels, so do not treat path scores as validated accuracy (SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V2_RESULTS_20261004.md)."],
    },
    "exact_approximate_inference_and_optimization": {
        "status": "partially_audited",
        "canonical_state_owner": "The CAN Microtheory, Concepts, and causal edges live in the Rust substrate. Relaxation uses loaded graph rules; junction-tree and BP compute over Python-side snapshots/messages and write the winning state only at their commit boundary. Solver Goal/report attrs are written through the Python adapter.",
        "python_shadow_or_indexes": "Loopy BP messages/beliefs and exact junction-tree potentials/bags are local Python data during inference. Native mt_energy/mt_frustration operations score candidate states without committing those maps.",
        "normal_entrypoints": [
            ("domains/can_native_orchestration.py", "scoped_settle", "explicit single-start CAN relaxation; default k_starts=1 at solver dispatch; commits rule-updated graph state"),
            ("domains/can_junction_tree.py", "junction_tree_exact_settle", "explicit exact toolbox path; width-gated; commit=True by default"),
            ("domains/can_native_bp.py", "run_loopy_bp", "explicit bounded BP path; max_product default; commit=False by default"),
            ("runners/dsl/src/can_ops.rs", "mt_energy", "native scoring primitive; no inference/commit"),
            ("runners/dsl/src/can_ops.rs", "mt_frustration_given_state", "native scoring primitive; no inference/commit"),
            ("runners/dsl/src/py.rs", "PySubstrate::mt_energy", "native score exposed to Python callers"),
            ("runners/dsl/src/py.rs", "PySubstrate::mt_frustration_given_state", "native score exposed to Python callers"),
        ],
        "alternate_entrypoints": [
            ("domains/can_native_orchestration.py", "multi_start_settle_and_pick_best", "explicit multi-start optimization when k_starts>1; random unless caller seeds rng; commits selected state"),
            ("domains/solver_dispatch.py", "solve_can_relax", "explicit solve Goal resolver; requires a populated Microtheory and CAN update rules already loaded"),
            ("domains/solver_dispatch.py", "solve_can_exact", "explicit solve Goal resolver; honest refusal above width bound"),
            ("domains/solver_dispatch.py", "solve_can_bp", "explicit solve Goal resolver; reports convergence and commit is opt-in"),
            ("domains/solver_dispatch.py", "ensure_can_native_engine_loaded", "explicit idempotent load helper for self_load_only CAN rules; not part of generic boot"),
        ],
        "limits": ["These are selected CAN tools, not a substrate-wide inference API; solve goals require an already-built Microtheory.",
                   "The native discrete update seed is self_load_only; relaxation correctness depends on loading the rules first.",
                   "Exact inference refuses beyond its declared width bound; BP is bounded and may return unconverged; multi-start is stochastic unless rng is seeded.",
                   "Existing result envelopes are workload-specific and do not establish general inference quality or a general CPU cost bound."],
    },
    "shape_decode_recognition_transform_dimension_inference": {
        "status": "partially_audited",
        "canonical_state_owner": "Shape/signature/codebook state and graph-authored rule state reside in the Rust substrate graph and TermArena. Rust shape_decode evaluators compute Terms; Python adapters seed the codebooks, construct observations, and orchestrate selected applications.",
        "python_shadow_or_indexes": "The audited rung results are returned as native Value/Term results and graph effects; some application-specific ingestion and faculty orchestration remain Python-owned.",
        "normal_entrypoints": [
            ("runners/dsl/src/shape_decode.rs", "eval_shape_decode", "ShapeDecode Term arm; invoked when a shape_decode_loop rule evaluates it"),
            ("runners/dsl/src/shape_decode.rs", "eval_transform_decode", "TransformDecode Term arm; seed loop uses this before novelty mint"),
            ("runners/dsl/src/shape_decode.rs", "eval_dim_infer", "DimInfer Term arm; bounded generator/dimension hypothesis search"),
            ("runners/dsl/src/shape_decode.rs", "eval_gen_infer", "GenInfer Term arm; bounded generator-inference extension"),
            ("evaluation/substrate_capability/audit_shape_decode_seed_scope_v1.py", "main", "static count of frame-scoped and global helper Terms in the shape_decode_loop seed"),
            ("evaluation/substrate_capability/analyze_live_codebook_frame_provenance_v1.py", "main", "hash-checked runtime ShapeSignature frame-attribute audit on the v1.4 live helper capture"),
            ("evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1.py", "main", "24-worker source-locked traced/untraced ShapeDecode singleton-name-scope baseline across 33–145 effective codebook parts"),
            ("evaluation/substrate_capability/analyze_shapedecode_name_aperture_baseline_v1.py", "main", "independent worker/source parity, exact outcome, helper population-work, and timing analysis"),
            ("evaluation/substrate_capability/shapedecode_name_aperture_cache_v1.py", "main", "80-worker source-locked scan-versus-EvalCtx-cache panel for singleton name-scoped ShapeDecode"),
            ("evaluation/substrate_capability/analyze_shapedecode_name_aperture_cache_v1.py", "main", "independent source-lock, paired output/work parity, operation-count, and timing analysis"),
            ("evaluation/substrate_capability/shapedecode_name_aperture_semantics_v1.py", "main", "14-worker paired scan/cache semantic control panel for name casing, duplicates, scopes, and requested-name ordering"),
            ("evaluation/substrate_capability/analyze_shapedecode_name_aperture_semantics_v1.py", "main", "independent source-lock and exact Term-result parity analysis for semantic controls"),
            ("evaluation/substrate_capability/audit_shapedecode_seed_aperture_reuse_v1.py", "main", "source-hashed static census of name-scoped ShapeDecode Terms and repeated-evaluation contexts across checked-in seed JSON"),
            ("evaluation/substrate_capability/analyze_shapedecode_seed_aperture_reuse_v1.py", "main", "independent seed-tree walk verifying each scoped call, source digest, and context count"),
            ("evaluation/substrate_capability/shapedecode_verdict_comparator_cache_v1.py", "main", "80-worker current-source scan/cache end-to-end replay of the existing vision_verdict_comparator V0 seed arm across 16–128 VdSignature parts"),
            ("evaluation/substrate_capability/analyze_shapedecode_verdict_comparator_cache_v1.py", "main", "independent paired rule-output/work, source-lock, trace, population-visit, and timing analysis"),
            ("runners/dsl/src/shape_decode.rs", "eval_recognise_shape", "RecogniseShape Term arm; identity assignment/evidence path"),
            ("runners/dsl/src/term.rs", "evaluate", "default Term dispatch; shape variants invoke the corresponding native evaluator"),
            ("substrate/boot_all.py", "load_all_seeds", "loads the declared graph-authored shape rules/codebooks and dependencies"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/shape_decode.rs", "eval_meta_shape_mint", "explicit rung-four MetaShapeMint Term; active only where a seed/rule invokes it"),
            ("domains/reflective_faculty.py", "_ensure_shape_decode_loop", "idempotent host seed loader for selected reflective-faculty path"),
            ("domains/reflective_faculty.py", "shape_frame", "application-specific reflective-faculty orchestration, not a general cognition entrypoint"),
        ],
        "limits": ["These are bounded, named Term families and graph-authored pipelines, not open-ended structure induction.",
                   "The exact active rungs depend on the seed/codebook and application; reaching mint is workload-specific.",
                   "The EvalCtx-local parsed-codebook cache improves two authored candidate-at-a-time routes, including an existing comparator seed and two codebook types. However, the active shape_decode_loop has zero name-scoped ShapeDecode calls, so the cache does not apply to its three global ShapeDecode Terms. Selected casing, duplicate, None/empty-scope, and requested-name-order controls pass; Surface(Text), malformed-entry, exclude, mutation-lifecycle, direct one-shot cost, and natural-task prevalence remain unmeasured.",
                   "Selected held-out novelty results do not establish general transfer, low false-mint rate, or tractability over rich hypothesis classes.",
                   "Native Term execution is mixed with Python observation ingestion and seed/faculty orchestration."],
    },
    "program_synthesis_induction": {
        "status": "partially_audited",
        "canonical_state_owner": "The Rust Substrate owns the graph and TermArena used by native SynthEnumerate and ProgEval Terms. The graph-authored program_synthesis seed owns rule-level proposal/evaluation/status transitions; Python domains/prog_synthesis.py adapts task specifications, examples, and codebooks, invokes workload helpers, and records results.",
        "python_shadow_or_indexes": "Specification ingestion, dataset/example preparation, orchestration, result recording, and some candidate construction are Python-owned. domains/prog_ir_rust.py is a separate source-to-Program-IR reader for supported source syntax, not the enumerative learner.",
        "normal_entrypoints": [
            ("runners/dsl/src/synth_enumerate.rs", "eval_synth_enumerate", "bounded native bottom-up candidate enumeration Term; requires an operator grammar, examples, and caller-provided budget/candidate limits"),
            ("runners/dsl/src/prog_eval.rs", "eval_prog_eval", "native fueled Program-IR interpreter Term; execution/evaluation, not induction"),
            ("domains/cegis_faculty.py", "cegis_synthesize", "domain-general Python CEGIS loop over native synthesis/evaluation; accepts caller-provided descriptors, oracle, known rows, and ordered input family"),
            ("domains/cegis_faculty.py", "find_counterexample", "selects the first disagreement in supplied family order and obtains its label from the callable oracle"),
            ("domains/query_selection.py", "rank_queries_by_disagreement", "label-blind finite-pool query ranking by predictive entropy over an explicit equal-weight hypothesis set"),
            ("domains/contract_query.py", "select_discriminating_input", "native-Term maximum-entropy query selection over generated bounded version spaces; candidate evaluation exceptions form an explicit prediction bucket"),
            ("domains/contract_query.py", "partition_hypotheses_by_behavior", "finite typed prediction partition with probe digest and explicit limits; does not certify equivalence outside supplied probes"),
            ("evaluation/substrate_capability/numeric_opposition_model_misspecification_v1.py", "worker", "diagnostic out-of-grammar capture; synthesis/holdout findings retained, query-policy results invalid due row-list input binding"),
            ("evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_1.py", "worker", "corrected out-of-grammar additive relation evaluation with paired query policies, explicit evaluator-error control, and fractional holdouts"),
            ("evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1.py", "worker", "source-locked additive/product grammar-mismatch panels plus coverage-directed in-grammar opposition control, paired with finite challenge auditing"),
            ("evaluation/substrate_capability/grammar_widening_depth_v1.py", "worker", "source-locked size-7/size-9 replay on ten frozen out-of-grammar panels with supplied operator hints and exact fractional holdouts"),
            ("evaluation/substrate_capability/primitive_family_selection_v1.py", "worker", "source-locked paired maximum-entropy/fixed-order selection over generated Plus/Times operator-family hypothesis unions"),
            ("evaluation/substrate_capability/primitive_menu_help_policy_v1_1.py", "worker", "source-locked five-task menu evaluation with paired query policies, singleton challenge probes, and explicit teacher-hint recovery"),
            ("evaluation/substrate_capability/primitive_semantic_equivalence_v1.py", "worker", "source-locked replay on original and zero-aware query domains with finite typed prediction-equivalence classes and teacher-hint comparison"),
            ("scripts/substrate_label_blind_query_ranking_v1.py", "worker", "three-task selector evaluation against fixed-first, seeded-random, and oracle-best controls"),
            ("scripts/analyze_substrate_label_blind_query_ranking_v1.py", "main", "independent schedule, entropy, oracle-call, survivor, and task-label reconstruction gates"),
            ("scripts/cegis_query_order_sensitivity_v1.py", "worker", "paired fixed-order versus seeded-permutation sensitivity probe for the current first-disagreement CEGIS policy"),
            ("scripts/analyze_cegis_query_order_sensitivity_v1.py", "main", "independent schedule, order, query-call, row, and heldout reconstruction checks"),
            ("scripts/cegis_query_order_sensitivity_v2.py", "worker", "matched query-order sensitivity probe forcing a shared output-independent synthesis literal set"),
            ("scripts/analyze_cegis_query_order_sensitivity_v2.py", "main", "independent order, literal-set, query-call, synthesis-work, and heldout reconstruction checks"),
            ("scripts/cegis_cross_task_query_order_v1.py", "worker", "cross-task first-disagreement order sensitivity across triangular numbers and population variance with output-independent literals"),
            ("scripts/analyze_cegis_cross_task_query_order_v1.py", "main", "independent 20-cell schedule, label, query-order, native-work, and heldout audit"),
            ("domains/prog_synthesis.py", "ensure_program_synthesis", "loads/configures graph-authored synthesis rules and initial state for the selected workload"),
            ("domains/prog_synthesis.py", "ingest_spec", "host adapter for task specification and examples"),
            ("domains/prog_synthesis.py", "eval_and_record", "host adapter invokes evaluation and records graph-visible outcomes"),
            ("domains/prog_synthesis.py", "run_enumerate", "host adapter for the bounded enumeration workload path"),
            ("scripts/program_ir_candidate_snapshot_transfer_v1.py", "worker", "isolated Rung 3 Program/IR acquisition followed by eager and shared-graph-page child execution against an exact clamp oracle"),
            ("scripts/analyze_program_ir_candidate_snapshot_transfer_v1.py", "main", "independent task, oracle, branch-isolation, candidate-identity, and backend-parity checks"),
            ("scripts/synthesis_ambiguity_counterexample_v1.py", "worker", "source-locked sparse-fit false acceptance, one counterexample, default search cap, and oracle-grammar contrast inside isolated candidate snapshots"),
            ("scripts/analyze_synthesis_ambiguity_counterexample_v1.py", "main", "independent training/holdout oracle, false-accept, search-cost, isolation, and backend-parity analysis"),
            ("evaluation/substrate_capability/term_literal_probe_repair_v1.py", "worker", "paired edge-only versus Term-literal-boundary query policy on three frozen numeric panels"),
            ("evaluation/substrate_capability/analyze_term_literal_probe_repair_v1.py", "main", "independent source, proposal, selector, class, holdout, and cost replay for literal-directed probes"),
            ("evaluation/substrate_capability/term_literal_adversarial_family_v1.py", "main", "locked six-cell point/interval guard family across two, three, and four variables"),
            ("evaluation/substrate_capability/analyze_term_literal_adversarial_family_v1.py", "main", "independent candidate, witness, proposal, selector, holdout, and cost replay"),
            ("evaluation/substrate_capability/term_literal_joint_proposals_v1.py", "main", "paired pairwise versus all-arity Cartesian literal proposals under fixed 64-row and eight-label caps"),
            ("evaluation/substrate_capability/analyze_term_literal_joint_proposals_v1.py", "main", "independent joint proposal, selector, holdout, and native-work replay"),
            ("evaluation/substrate_capability/literal_proposal_budget_stress_v1.py", "main", "256-row noise-padded literal Cartesian stress with exhaustive and 64-row fail-closed policies"),
            ("evaluation/substrate_capability/analyze_literal_proposal_budget_stress_v1.py", "main", "independent product, truncation, abstention, holdout, and native-work replay"),
            ("evaluation/substrate_capability/clause_aware_literal_proposals_v1.py", "main", "host-side direct-comparison clause solver paired with exhaustive and budgeted query slates"),
            ("evaluation/substrate_capability/analyze_clause_aware_literal_proposals_v1.py", "main", "independent clause extraction, witness, selector, holdout, and cost replay"),
            ("evaluation/substrate_capability/clause_aware_generated_guards_v1.py", "main", "six-panel direct-comparison transfer and fail-closed unsupported arithmetic guard evaluation"),
            ("evaluation/substrate_capability/analyze_clause_aware_generated_guards_v1.py", "main", "independent guard classification, proposal, selector, holdout, and abstention replay"),
            ("evaluation/substrate_capability/clause_contradiction_aliasing_v1.py", "main", "twelve-panel finite-binary64 contradiction, adjacent-float, repeated-bound, and variable-alias evaluation"),
            ("evaluation/substrate_capability/analyze_clause_contradiction_aliasing_v1.py", "main", "independent proof-fragment status, disjoint proposal, selector, holdout, and abstention replay"),
            ("evaluation/substrate_capability/finite_float_clause_audit_v1.py", "main", "4,096-case seeded unary/two-variable finite-binary64 clause audit with native witness checks"),
            ("evaluation/substrate_capability/analyze_finite_float_clause_audit_v1.py", "main", "independent lower/upper-bound oracle and native witness parity analysis"),
            ("evaluation/substrate_capability/finite_float_variable_relations_v1.py", "main", "1,024 generated two-variable relation cases over a finite representative search domain"),
            ("evaluation/substrate_capability/analyze_finite_float_variable_relations_v1.py", "main", "independent representative-witness and native Term parity replay"),
        ],
        "alternate_entrypoints": [
            ("domains/prog_synthesis.py", "synth_enumerate_live", "explicit live synthesis helper for selected configured workloads"),
            ("domains/prog_synthesis.py", "ensure_program_synthesis_opgrammar", "explicit operator-grammar setup path"),
            ("domains/prog_synthesis.py", "build_descent", "workload-specific descent/candidate construction path"),
            ("domains/prog_ir_rust.py", "read_source", "optional source-to-Program-IR reader; supports a bounded syntax subset and is not general code understanding"),
            ("domains/prog_ir_rust.py", "read_function", "optional function-level source-to-Program-IR reader"),
        ],
        "limits": ["SynthEnumerate is bounded by a supplied grammar, examples, budget, and candidate cap; it is not open-ended induction.",
                   "Integrated proposal/evaluation/exhaustion behavior depends on the loaded seed, Python task adapter, and workload-specific codebook.",
                   "ProgEval executes supported Program IR under fuel; successful execution does not establish synthesis or generalization.",
                   "Integrated `cegis_synthesize` still selects first disagreement in caller order; the separate label-blind entropy ranker has been measured only over authored, supplied hypothesis sets and is not integrated with hypothesis generation or CEGIS version-space updates ([results](SUBSTRATE_LABEL_BLIND_QUERY_RANKING_V1_RESULTS_20260930.md)).",
                   "The five-pair order-sensitivity probe changes query sequences but is one triangular-number task; its search-cost contrast is confounded because revealed integer outputs enter the synthesis literal set ([results](CEGIS_QUERY_ORDER_SENSITIVITY_V1_RESULTS_20260930.md)).",
                   "The follow-up holds the 15-literal vocabulary fixed and again finds fewer queries/candidate evaluations under seeded permutations on the same task; synthesis takes 102-152 seconds median. This is one authored function, not policy superiority evidence ([results](CEGIS_QUERY_ORDER_SENSITIVITY_V2_RESULTS_20260930.md)).",
                   "A 20-worker cross-task order panel finds sensitivity in a scalar integer function and a list-statistic function; seeded permutations retain exact heldout transfer on 5/5 versus 4/5 variance workers, with approximately 2.8M candidates and 84-119 seconds median variance cost. The fixed-seed order is not a general query-policy comparison ([results](CEGIS_CROSS_TASK_QUERY_ORDER_V1_RESULTS_20260930.md)).",
                   "The source reader handles a supported syntax subset and must not be conflated with synthesis.",
                   "Existing results are task-family-specific; transfer, false acceptance, acquisition cost, and scaling across grammars remain open.",
                   "The corrected out-of-grammar additive-relation panel shows both maximum-entropy and sequential selection end in false singleton Terms on 3/5 repeated panels; the original v1 query capture is invalid because it passed row lists instead of feature maps. A controlled evaluator-failure input verifies explicit error buckets, but no adequacy guarantee follows ([v1.1 results](NUMERIC_OPPOSITION_MODEL_MISSPECIFICATION_V1_1_RESULTS_20261003.md), [analysis](../../../evaluation/reports/numeric_opposition_model_misspecification_v1_1_analysis_20261003.json)).",
                   "A new 10-worker isolated scalar-synthesis snapshot panel accepts one Program/IR per clamp task and executes it exactly on 60/60 held-out values in eager and shared-page CoW branches, with source-snapshot isolation and complete state-digest parity. The frozen base and examples-ingested/no-pump control have no task-specific Program. This is two shallow bound pairs under the fixed numeric grammar, not broad induction evidence ([results](SUBSTRATE_PROGRAM_IR_CANDIDATE_SNAPSHOT_TRANSFER_V1_RESULTS_20260930.md), [analysis](../../../evaluation/reports/program_ir_candidate_snapshot_transfer_v1_analysis_20260930.json)).",
                   "A locked three-arm hinge study repeats a concrete ambiguity failure: sparse examples produce the same predicate shortcut and 30/30 held-out errors; one known counterexample makes broad search gap at 200,000 candidates in 5/5 workers; supplying a compact oracle grammar yields exact 30/30 held-out transfer in 5/5. This demonstrates the correction/search-cost tradeoff for one authored function, not autonomous query or grammar selection ([results](SUBSTRATE_SYNTHESIS_AMBIGUITY_COUNTEREXAMPLE_V1_RESULTS_20260930.md), [analysis](../../../evaluation/reports/synthesis_ambiguity_counterexample_v1_analysis_20260930.json)).",
                   "A paired literal-boundary probe study reproduces edge-only false acceptance of a structured interval alias, then rejects it with one additional label after querying a Term-derived comparison boundary. This is one narrow guard family and does not make finite behavior-class acceptance generally safe ([results](TERM_LITERAL_PROBE_REPAIR_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/term_literal_probe_repair_v1_analysis_20261004.json)).",
                   "A locked six-cell guard sweep shows pairwise literal probes reject two-variable point and interval exceptions but accept all four three- and four-variable exceptions. This measures a proposal-combinatorics limit on authored controls, not a natural-task miss rate ([results](TERM_LITERAL_ADVERSARIAL_FAMILY_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/term_literal_adversarial_family_v1_analysis_20261004.json)).",
                   "The paired joint-literal follow-up rejects all six false guard candidates, including the higher-arity cases, within one label. Cartesian products add 1–16 new rows here under a 64-row cap; general combinatorial scaling, broader guard coverage, and natural-task rates remain open ([results](TERM_LITERAL_JOINT_PROPOSALS_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/term_literal_joint_proposals_v1_analysis_20261004.json)).",
                   "A noise-padded four-variable guard expands the literal product to 256 rows. Exhaustive proposals reject it in one label; a 64-row truncation misses it, but an explicit incomplete-slate guard abstains rather than falsely accepting. This is one stress case and leaves efficient search open ([results](LITERAL_PROPOSAL_BUDGET_STRESS_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/literal_proposal_budget_stress_v1_analysis_20261004.json)).",
                   "A host-side direct-comparison clause solver derives one separating row for that noise-padded guard using 60 scalar checks, versus 256 Cartesian proposals. It reduces native Term evaluations on this case but is tested on one authored formula and is not substrate-owned learning or general clause coverage ([results](CLAUSE_AWARE_LITERAL_PROPOSALS_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/clause_aware_literal_proposals_v1_analysis_20261004.json)).",
                   "A six-panel follow-up resolves three interval arities and one nested disjunction; it requests help on unsupported Plus/Times guards rather than accepting the surviving false candidates. The syntax recognizer remains harness-authored, and supported-form completeness is not proved ([results](CLAUSE_AWARE_GENERATED_GUARDS_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/clause_aware_generated_guards_v1_analysis_20261004.json)).",
                   "A twelve-panel extension proves three direct unary comparison conjunctions empty over finite binary64 values, handles repeated bounds, and abstains on unresolved variable aliases if a false candidate survives. This is a narrow proof fragment and does not imply general Term equivalence ([results](CLAUSE_CONTRADICTION_ALIASING_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/clause_contradiction_aliasing_v1_analysis_20261004.json)).",
                   "A seeded 4,096-clause differential audit has zero satisfiability-status disagreement with an independent bound oracle and zero native-witness rejection across 690 solutions. Coverage remains restricted to direct unary comparisons over finite binary64 values ([results](FINITE_FLOAT_CLAUSE_AUDIT_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/finite_float_clause_audit_v1_analysis_20261004.json)).",
                   "In 1,024 generated two-variable relation conjunctions, the direct-unary solver abstains on all cases and all 395 representative witnesses pass native Term evaluation; 629 cases have no witness in the finite representative set, which is not an unrestricted unsatisfiability proof ([results](FINITE_FLOAT_VARIABLE_RELATIONS_V1_RESULTS_20261004.md), [analysis](../../../evaluation/reports/finite_float_variable_relations_v1_analysis_20261004.json))."],
    },
    "memory_and_persistence_of_experience": {
        "status": "partially_audited",
        "canonical_state_owner": "Episodic/working-memory episodes and policies are graph-resident Rust Substrate state transformed by graph-authored rules. The separate long-term MemoryFaculty is lazily owned by each PySubstrate instance and holds growth history, disposable-ring state, hot tracking, and ShapeIndex in process memory; consolidated record attributes are written as JSON files.",
        "python_shadow_or_indexes": "domains/long_term_memory.py is an opt-in adapter: it projects record attributes to feature vectors and calls the native faculty. On first bind it scans durable JSON record files, rebuilds native ShapeIndex entries, and repopulates the adapter-local _known set; exact-key recall pages the containing cluster. The adapter remains process-local and stats reports disk_bytes and resident_in_ram as unknown.",
        "normal_entrypoints": [
            ("substrate/boot_core.py", "boot_core", "default core seed assembly includes episodic_working_memory_core; the graph rules act only when matching event/request/cycle facts are present"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_observe_and_bound", "explicit host-invoked working-memory budget/census operation; not implicit on every graph mutation"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_roll_disposable", "explicit host-invoked disposable ring maintenance"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_consolidate", "explicit host-invoked durable record write and in-process shape indexing"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_recall_by_shape", "explicit shape-based long-term recall/page-in on the same live PySubstrate"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_index_disk_record", "rebuild one native nonresident shape-index entry from a durable record"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_unindex_disk_record", "remove an ambiguous restored key from all shape clusters"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_recall_by_key", "exact-key lookup and cluster page-in after the adapter restores the index"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::memory_bound", "explicit budget configuration; lazily creates faculty and defaults to 5,000 nodes / 64 MiB"),
            ("runners/dsl/src/py.rs", "PySubstrate::memory_shuffle", "explicit long-term cold-cluster eviction from graph RAM; does not delete JSON records"),
            ("runners/dsl/src/memory.rs", "MemoryFaculty::forget_over_budget", "native keep-value-per-byte eviction path"),
            ("runners/dsl/src/memory.rs", "MemoryFaculty::consolidate", "native JSON encode/write plus ShapeIndex insertion"),
            ("runners/dsl/src/memory.rs", "MemoryFaculty::recall_by_shape", "native order-N shape descent and cluster page-in"),
            ("runners/dsl/src/memory.rs", "MemoryFaculty::index_disk_record", "native insertion of nonresident entries backed by existing record files"),
            ("runners/dsl/src/memory.rs", "MemoryFaculty::unindex_disk_record", "native removal of ambiguous restored keys"),
            ("runners/dsl/src/memory.rs", "MemoryFaculty::recall_by_key", "exact-key lookup followed by whole-cluster page-in"),
            ("domains/long_term_memory.py", "LongTermMemory::consolidate", "opt-in host adapter for consolidation; computes category/leaf feature vectors"),
            ("domains/long_term_memory.py", "LongTermMemory::recall_by_shape", "opt-in host adapter for native shape recall"),
            ("domains/long_term_memory.py", "LongTermMemory::_bind", "first-bind disk scan rebuilds the native shape index from valid JSON records"),
            ("domains/long_term_memory.py", "LongTermMemory::recall", "exact-key recall delegates to native cluster page-in"),
            ("substrate/graph.py", "TypedGraph::node", "generic optional recall-on-miss hook; no installer for the historical paged-memory hook exists in this checkout"),
        ],
        "limits": ["PySubstrate.memory and its ShapeIndex remain process-local; the host adapter reconstructs them by scanning JSON record files on first bind, rather than persisting a native index snapshot.",
                   "Locked fresh-process probes establish exact-key and shape-based attribute recall through 50,000 tiny records in a synthetic family. A direct integrity probe verifies duplicate-key refusal and skipping malformed JSON/missing-attrs records. The host adapter's three-value category signature permits at most six ordinal-rank clusters; larger stores, larger payloads, cold-cache I/O, checksums/truncated semantic corruption, concurrent writers, and realistic retrieval quality remain unmeasured.",
                   "Same-process shape page-in reconstructs an attribute-only node; a one-record probe reused its original NodeID, but the record file does not preserve incident graph edges. ID reuse under interleaved allocation is unmeasured.",
                   "A historical online-plan note claims transparent same-ID recall with edges intact via domains/paged_memory.py; this probe confirms same-ID reuse for one record but contradicts edge restoration, and the referenced module is absent from this checkout. substrate/graph.py only contains an optional generic hook with no current installer found.",
                   "Episodic/working-memory tests cover selected graph-rule mechanisms, not long-term disk/index lifecycle, corruption recovery, retrieval quality, interference, or general scale. Paired exact-cue query variants at N<=192 remove a demonstrated global pair-scan cost and preserve response identity/confidence on two synthetic workloads, but change persistent episode collision marks. The native Episode.cue_key index removes repeated cue Filter Terms. An isolated indexed-join hint now prunes the retrieval rule's own Episode candidates to cue matches (measured at N<=192); this is not yet a production seed change and other rules remain unoptimized. Both prototypes change persistent collision marks. See docs/research/engine_substrate/SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_RESULTS.md, SUBSTRATE_EPISODIC_CUE_NATIVE_INDEX_RESULTS.md, and SUBSTRATE_EPISODIC_CUE_INDEXED_JOIN_RESULTS.md.",
                   "The row combines distinct memory subsystems; do not transfer episodic rule evidence to the long-term native faculty."],
    },
    "learning_self_modification_proposals": {
        "status": "partially_audited",
        "canonical_state_owner": "There is no single learning state owner. GammaLearner keeps Python Counter/dict observations and a Python Grammar for a narrow Life-like toy; selected vision, shape, program, and curriculum learning decisions are graph-authored rules over Rust Substrate state; P3-R0 proposal/evaluation/receipt/rollback coordination is Python evaluation infrastructure; runtime primitive installation is a separate host operation that edits Rust source and rebuilds only after its guardrails and supplied approver path.",
        "python_shadow_or_indexes": "Observation extraction, toy GammaLearner state, proposal adapters, evaluation protocol, installer, and some domain curricula are Python-owned. Native P3 structs are serialized data-plane types and validation/snapshot primitives; repository call-site search found no integration from them into GammaLearner, graph learning rules, or proposal_install.",
        "normal_entrypoints": [
            ("substrate/learner.py", "GammaLearner::observe", "standalone Python toy update; not the default WorldAdapter learning path"),
            ("substrate/learner.py", "GammaLearner::observe_transition", "standalone Life-like board-to-Gamma observation adapter"),
            ("substrate/learner.py", "GammaLearner::predict", "toy learned rule lookup"),
            ("runners/dsl/src/p3_graph.rs", "validate_proposal", "native P3 proposal validation primitive; no integration call site found outside its module tests"),
            ("runners/dsl/src/p3_graph.rs", "snapshot", "native content-addressed candidate snapshot primitive"),
            ("runners/dsl/src/p3_graph.rs", "restore", "native exact-byte candidate restore primitive"),
            ("domains/proposal_install.py", "install_proposal", "explicit host proposal installation path; fresh sandbox validation and touched-file allowlist precede source mutation/rebuild; supplied approver does not itself establish independent evaluation"),
            ("scripts/learning_aperture_measure.py", "main", "opt-in mechanism benchmark; graph rules make the learning/attention decisions"),
            ("evaluation/substrate_capability/vision_eye_orientation_native_association_v1_2.py", "run_case", "source-locked supervised graph-native prototype-distance association/readout on fixed position-heldout bars; external teacher and readout remain supplied"),
            ("evaluation/substrate_capability/analyze_vision_eye_orientation_native_association_v1_2.py", "main", "independent six-seed state-parity, trace-reconstruction, paired-control, and held-out analysis"),
            ("evaluation/substrate_capability/native_primitive_family_selection_transfer_v1.py", "run_panel", "native graph-rule candidate predictions, validation agreement scoring, ArgminUnique family choice, and sealed numeric-grid transfer"),
            ("evaluation/substrate_capability/analyze_native_primitive_family_selection_transfer_v1.py", "main", "independent ten-panel prediction, score, native-selection, task-label isolation, and 1,296-row holdout replay"),
            ("evaluation/substrate_capability/native_candidate_adequacy_v1.py", "run_panel", "native validation-threshold adequacy diagnosis and gated candidate choice across positive and out-of-menu numeric panels"),
            ("evaluation/substrate_capability/analyze_native_candidate_adequacy_v1.py", "main", "independent threshold replay, false-accept/false-mismatch accounting, and sealed-grid candidate adequacy audit"),
            ("evaluation/substrate_capability/native_candidate_adequacy_v2.py", "run_panel", "class-balanced native candidate scoring, mismatch request-help, and held-out transfer across four numeric relations"),
            ("evaluation/substrate_capability/analyze_native_candidate_adequacy_v2.py", "main", "independent balanced-score replay, policy audit, and sealed integer/fractional grid transfer analysis"),
            ("evaluation/substrate_capability/native_candidate_adequacy_v3.py", "run_panel", "native minimum-class-accuracy adequacy gate with explicit request-help and fresh held-out transfer"),
            ("evaluation/substrate_capability/analyze_native_candidate_adequacy_v3.py", "main", "independent per-class score replay, decision-policy audit, and sealed-grid transfer analysis"),
            ("evaluation/substrate_capability/analyze_native_candidate_adequacy_probe_utility_v1.py", "main", "post-hoc target-blind candidate-positive versus uniform counterexample-query utility over v3 held-out captures"),
            ("evaluation/substrate_capability/native_candidate_adequacy_query_v1_1.py", "worker", "paired target-blind host query arms with native adequacy scoring and explicit mismatch-to-request-help graph rules"),
            ("evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_1.py", "main", "independent paired-panel query-order, native help, disjointness, and held-out transfer replay"),
            ("evaluation/substrate_capability/native_candidate_adequacy_query_v1_2.py", "worker", "native candidate-positive probe eligibility and ArgminUnique query selection paired with host controls and native mismatch-to-help"),
            ("evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_2.py", "main", "independent native/host query parity, help policy, task blindness, costs, and held-out transfer replay"),
            ("domains/code_write_growth.py", "teach_write_shape_from_example", "reads an externally supplied runnable function, validates its Term, and teaches a reusable code-write ShapeSignature"),
            ("domains/code_writing.py", "compose_function_from_request", "graph-native shape decode selects a held code-write construction for a request"),
            ("domains/code_writing.py", "write_function_from_request", "renders a selected held Term construction as executable Python"),
            ("domains/code_reading.py", "read_function", "ingests supported Python source and emits a Term representation through the held code-reading path"),
            ("domains/contract_query.py", "select_discriminating_input", "chooses a maximum-entropy input over a finite caller-supplied native-Term hypothesis set; requires an external oracle label"),
            ("evaluation/substrate_capability/measure_numeric_opposition_active_query_v1.py", "run_worker", "source-locked synthesis, max-entropy/fixed/random query replay, and sealed held-out scoring for a finite numeric relation version space"),
            ("evaluation/substrate_capability/analyze_numeric_opposition_active_query_v1.py", "main", "independent source, typed prediction, policy, stopping, survivor, and held-out replay"),
            ("evaluation/substrate_capability/measure_numeric_opposition_active_query_v1_1.py", "worker", "150 paired maximum-entropy versus sequential randomized-order replays over synthesized hypothesis pools"),
            ("evaluation/substrate_capability/analyze_numeric_opposition_active_query_v1_1.py", "main", "independent paired-order, query-policy, typed-filtering, stopping, and held-out replay"),
            ("evaluation/substrate_capability/substrate_code_write_example_acquisition_v1.py", "worker", "source-locked fresh-process example-teaching and held-out transfer panel"),
            ("evaluation/substrate_capability/analyze_substrate_code_write_example_acquisition_v1.py", "main", "independent analytic oracle for native Term and generated-Python outputs"),
            ("evaluation/substrate_capability/substrate_contract_query_selection_v1_1.py", "worker", "locked maximum-disagreement query selection versus seeded random input orders on finite Term hypothesis sets"),
            ("evaluation/substrate_capability/analyze_substrate_contract_query_selection_v1_1.py", "main", "independent entropy, task-label, and random-query replay"),
            ("evaluation/substrate_capability/substrate_contract_query_scaling_v1.py", "worker", "locked H=8/32/128 query-cost scaling plus direct contradiction and observational-alias controls"),
            ("evaluation/substrate_capability/analyze_substrate_contract_query_scaling_v1.py", "main", "independent operation-count, random-baseline, and open-world adequacy analysis"),
            ("evaluation/substrate_capability/substrate_contract_query_scale_factors_v1.py", "worker", "14-worker H/depth/input-grid factor sweep through H=512, Term depth 69, and N=500"),
            ("evaluation/substrate_capability/analyze_substrate_contract_query_scale_factors_v1.py", "main", "independent maximum-entropy and native evaluation-call count replay by factor"),
        ],
        "alternate_entrypoints": [
            ("domains/auto_approve.py", "scan_and_auto_approve", "separate opt-in policy caller for install_proposal; bounded by policy checks and not independent evaluator custody"),
            ("domains/self_correct_dispatch.py", "scan_and_self_correct", "domain-specific host orchestration of ranked corrections"),
            ("evaluation/p3/runner.py", "P3R0Runner::run", "local preregistered preflight path; mandatory rejection and rollback, never adoption"),
            ("evaluation/p3/runner.py", "P3R0Runner::run_e1_local_test", "gated local E1 harness; requires signed P0/P1/P2 evidence, seals results, forces no-go and rollback because custody is local"),
            ("evaluation/p3/admission.py", "validate_and_stage", "explicit candidate staging after lock/proposal validation"),
            ("evaluation/p3/admission.py", "reject_and_rollback", "explicit rejection path with exact pre-snapshot restoration"),
            ("domains/runtime_design.py", "emit_primitive_rust", "host-side proposal renderer; rendering is not adoption or evidence of usefulness"),
        ],
        "limits": ["GammaLearner is restricted to a two-state Life-like alphabet and alive-neighbour-count feature; it is Python state, not a general substrate induction service.",
                   "The current learning-aperture recheck is a focused observation/attention mechanism study, not evidence of held-out task learning, cross-domain transfer, or learned-rule adoption.",
                   "Native P3 structs and P3-R0 evaluator scaffolding are not wired into the domain learners or installer; P3-R0 explicitly cannot adopt and the preregistration states there is no P3-E1 result or independent evaluator custody.",
                   "Self-modification can cross into Rust source/build through proposal_install after explicit host authorization and fresh validation; this is a separate path from graph-native codebook/rule growth and its acquisition/evaluation cost is not measured end-to-end here.",
                   "A ten-worker full-boot code-writing study teaches one new ShapeSignature per externally supplied parity/clamp example and gets exact independent held-out transfer on 305/305 native and generated-Python calls. This is supervised source ingestion and codebook reuse, not autonomous proposal generation or broad code synthesis; full-boot peak RSS is about 1.68 GiB ([results](SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_RESULTS_20261001.md), [protocol](SUBSTRATE_CODE_WRITE_EXAMPLE_ACQUISITION_V1_PREREG_20261001.md), [raw](../../../evaluation/reports/substrate_code_write_example_acquisition_v1_raw_20261001.json), [analysis](../../../evaluation/reports/substrate_code_write_example_acquisition_v1_analysis_20261001.json)).",
                   "A four-worker source-locked control finds exposure alone adds no write construction (0/2), while deliberately teaching a parity function under a clamp request is admitted and selected in 2/2 workers but fails an independent clamp oracle on 24/24 cases. This identifies a request/example semantic alignment gap in the current teaching route for the tested mismatch, not its population rate; require semantic validation or calibrated refusal before generalizing acquisition claims ([results](SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_RESULTS_20261001.md), [protocol](SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_PREREG_20261001.md), [analysis amendment](SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_ANALYSIS_AMENDMENT_20261001.md), [raw](../../../evaluation/reports/substrate_code_write_acquisition_controls_v1_raw_20261001.json), [analysis](../../../evaluation/reports/substrate_code_write_acquisition_controls_v1_analysis_20261001.json)).",
                   "An opt-in contract-example gate now requires caller-supplied input/output rows to match both native Term and emitted Python before codebook growth. In a locked four-worker panel it admits aligned parity 2/2 (10/10 exact oracle rows) and refuses same-arity parity-as-square 2/2 with zero shape growth. Contract correctness/coverage remain external and legacy no-contract callers remain ungated; this is a bounded guarded-acquisition result ([results](SUBSTRATE_CODE_WRITE_CONTRACT_VALIDATION_V1_RESULTS_20261001.md), [protocol](SUBSTRATE_CODE_WRITE_CONTRACT_VALIDATION_V1_PREREG_20261001.md), [raw](../../../evaluation/reports/substrate_code_write_contract_validation_v1_raw_20261001.json), [analysis](../../../evaluation/reports/substrate_code_write_contract_validation_v1_analysis_20261001.json)).",
                   "Contract coverage itself is a separate limit: identity mislabeled as square passes the correct but non-discriminating 0→0 and 1→1 observations, is selected, then scores 0/8 on held-out inputs; adding 2→4 causes refusal before the named construction is created. This demonstrates the need to select informative probes, not merely accumulate labeled cases. Aggregate ShapeSignature deltas in this panel are not attributed because the capture lacks a post-read/pre-teach checkpoint ([results](SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_RESULTS_20261001.md), [protocol](SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_PREREG_20261001.md), [analysis amendment](SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_ANALYSIS_AMENDMENT_20261001.md), [raw](../../../evaluation/reports/substrate_code_write_contract_coverage_v1_raw_20261001.json), [analysis](../../../evaluation/reports/substrate_code_write_contract_coverage_v1_analysis_20261001.json)).",
                   "A native-Term finite-version-space selector maximizes output-partition entropy over candidate inputs. It identifies hidden targets in one query on three easy 3-hypothesis arithmetic families, where random baselines also average 1.071 queries. In a sparse 8-hypothesis coded family it identifies the target in 3/3 queries across two workers versus a 7.496 mean over 4,000 seeded random query sequences. The task and hypotheses are harness-supplied, and the easy-family control shows no general advantage claim; native loop median is 168.6 microseconds on one host ([results](SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_1_RESULTS_20261001.md), [protocol](SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/substrate_contract_query_selection_v1_1.py), [analysis](../../../evaluation/reports/substrate_contract_query_selection_v1_1_analysis_20261001.json)).",
                   "At H=8/32/128, the finite query selector identifies supplied coded targets in K=3/5/7 labels with measured loops 2.16/22.85/178.59 ms and 226/1,638/9,434 native Term evaluations. A direct contradiction yields an empty-set refusal, but observational aliasing yields a false singleton (candidate predicts 15 where held-out oracle returns 115). This documents scaling costs and a closed-world model-adequacy gap; no general tractability or open-world inference claim follows ([results](SUBSTRATE_CONTRACT_QUERY_SCALING_V1_RESULTS_20261001.md), [protocol](SUBSTRATE_CONTRACT_QUERY_SCALING_V1_PREREG_20261001.md), [analysis amendment](SUBSTRATE_CONTRACT_QUERY_SCALING_V1_ANALYSIS_AMENDMENT_20261001.md), [raw](../../../evaluation/reports/substrate_contract_query_scaling_v1_raw_20261001.json), [analysis](../../../evaluation/reports/substrate_contract_query_scaling_v1_analysis_20261001.json)).",
                   "Independent-factor measurements raise the same selector to 1.30 s at H=512, 304 ms at neutral Term depth 69, or 467 ms at a 500-input grid; call counts isolate H and grid work, while depth raises per-evaluation cost. Only two repetitions per cell and one synthetic family were measured, so this is a workload envelope rather than an asymptotic law ([results](SUBSTRATE_CONTRACT_QUERY_SCALE_FACTORS_V1_RESULTS_20261001.md), [protocol](SUBSTRATE_CONTRACT_QUERY_SCALE_FACTORS_V1_PREREG_20261001.md), [raw](../../../evaluation/reports/substrate_contract_query_scale_factors_v1_raw_20261001.json), [analysis](../../../evaluation/reports/substrate_contract_query_scale_factors_v1_analysis_20261001.json)).",
                   "A source-locked active-query integration uses hypotheses generated by the current term synthesizer rather than a manually listed set. On five sparse numeric-relation panels (9–10 hypotheses), every max-entropy, fixed-first, and seeded-random arm identifies an exact survivor. Max-entropy uses a median of two oracle labels versus one for fixed-first and four for random; its measured selector cost is higher than both. This does not show an active-query efficiency gain and remains conditional on a harness-supplied grammar, relation, and small pool ([results](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_RESULTS_20261003.md), [protocol](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_PREREG_20261003.md), [amendment](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_AMENDMENT_20261003.md), [lock](../../../evaluation/substrate_capability/numeric_opposition_active_query_v1_lock_20261003.json), [capture](../../../evaluation/reports/numeric_opposition_active_query_v1_20261003.json), [analysis](../../../evaluation/reports/numeric_opposition_active_query_v1_analysis_20261003.json)).",
                   "An order-balanced follow-up freezes 30 candidate permutations for each of five generated 9–10-hypothesis numeric panels. Across 150 paired blocks, maximum entropy uniquely identifies the exact survivor in 150/150, versus 111/150 for sequential randomized-order queries; it uses fewer labels in 102 blocks, ties in 32, and uses more in 16. Worker-cluster median call savings range from zero to two labels. Entropy selection costs 3.74 ms median versus 0.40 ms sequential, and labels are simulated from the known relation. This supports a bounded selection advantage conditional on the candidate pool, not real-oracle economics or broad active learning ([results](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_RESULTS_20261003.md), [protocol](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_PREREG_20261003.md), [lock](../../../evaluation/substrate_capability/numeric_opposition_active_query_v1_1_lock_20261003.json), [capture](../../../evaluation/reports/numeric_opposition_active_query_v1_1_20261003.json), [analysis](../../../evaluation/reports/numeric_opposition_active_query_v1_1_analysis_20261003.json)).",
                   "A corrected source-locked model-adequacy audit passes all six gates: challenge queries leave false additive singletons in 2/5 panels, empty product candidates in 5/5, and retain exact in-grammar opposition candidates in 5/5. Opposition uses 16 coverage-directed examples versus four for the out-of-grammar targets, so it is a candidate-available control, not a sample-size-matched comparison. Finite challenge audits do not diagnose every false singleton or autonomously widen the grammar ([results](NUMERIC_RELATION_MODEL_ADEQUACY_AUDIT_V1_1_RESULTS_20261003.md), [amendment](NUMERIC_RELATION_MODEL_ADEQUACY_AUDIT_V1_1_AMENDMENT_20261003.md), [analysis](../../../evaluation/reports/numeric_relation_model_adequacy_audit_v1_1_analysis_20261003.json)).",
                   "A source-locked ten-panel grammar-widening study finds exact candidates in all additive/product panels at size 7 (median 1.82–2.21 s, no timeouts); size 9 also finds exact candidates but all ten searches hit the 12 s cap and return larger partial spaces. The operator hint is supplied by task identity, so this measures bounded recovery and search-depth cost rather than autonomous grammar discovery ([results](GRAMMAR_WIDENING_DEPTH_V1_RESULTS_20261003.md), [analysis](../../../evaluation/reports/grammar_widening_depth_v1_analysis_20261003.json)).",
                   "A follow-up offers both Plus and Times expansions in all ten panels: maximum-entropy querying selects a correct exact singleton in 10/10, median two labels per task, versus 6/10 and median five/six labels for fixed order. The operator menu is supplied and labels come from a local oracle, so this is bounded two-family selection, not open-ended primitive invention ([results](PRIMITIVE_FAMILY_SELECTION_V1_RESULTS_20261003.md), [analysis](../../../evaluation/reports/primitive_family_selection_v1_analysis_20261003.json)).",
                   "A five-family, 25-panel query/help audit passes 7/7 gates. Entropy resolves additive, product, and ordering panels; selector abstention requests help on opposition and inequality. Post-capture zero-inclusive rescoring finds all opposition survivors exact and exact-plus-false survivors for inequality, so syntactic ambiguity is not equivalent to semantic failure and the hint sometimes adds no coverage. V1's analyzer failed to validate abstention and is diagnostic; v1.1 corrects the replay. This remains harness-authored numeric evidence with oracle labels and an upper-bound teacher hint ([results](PRIMITIVE_MENU_HELP_POLICY_V1_1_RESULTS_20261003.md), [analysis](../../../evaluation/reports/primitive_menu_help_policy_v1_1_analysis_20261003.json), [semantic addendum](../../../evaluation/reports/primitive_menu_help_policy_v1_1_semantic_addendum_20261003.json)).",
                   "A paired zero-aware query-domain replay passes 7/7 gates and reproduces v1.1's original transcript. Zero probes resolve the inequality false/exact alias in all five panels at median four labels; opposition remains one finite behavior class with all four survivors exact on the expanded holdout, despite five redundant help calls. This is finite-domain evidence only: a behavior class over a weak probe set can conceal off-domain error ([results](PRIMITIVE_SEMANTIC_EQUIVALENCE_V1_RESULTS_20261003.md), [analysis](../../../evaluation/reports/primitive_semantic_equivalence_v1_analysis_20261003.json)).",
                   "The query layer now exposes a typed finite behavior-partition API with a probe digest. A source-locked measurement replays 50 actual survivor sets and 175 H×P scaling cells; partitions match the reference and evaluation calls equal H×P. At H=64,P=64, median latency is 36.55 ms for 4,096 evaluations. This readout does not certify equivalence outside probes or determine whether returning a class is safe ([results](BEHAVIOR_EQUIVALENCE_PARTITION_V1_RESULTS_20261003.md), [analysis](../../../evaluation/reports/behavior_equivalence_partition_v1_analysis_20261003.json)).",
                   "A worker-0 exploratory grammar-widening pilot finds exact additive/product candidates after a task-informed primitive hint; retaining baseline operators at size 9 times out at 12 s, while size 7 recovers within 1.9–2.2 s. This is single-panel search-depth evidence, not autonomous grammar discovery or a reliability estimate ([pilot](GRAMMAR_WIDENING_DEPTH_PILOT_20261003.md)).",
                   "A six-seed source-locked orientation experiment scores 34/48 with a graph-native prototype-distance reader versus 30/48 for v1.1 dot product; four paired seeds improve, one declines, one ties. This is post-result calibration on one supervised synthetic task, not autonomous rule/readout invention or general transfer ([results](SUBSTRATE_VISION_EYE_ORIENTATION_NATIVE_ASSOCIATION_V1_2_RESULTS_20261005.md), [analysis](../../../evaluation/reports/vision_eye_orientation_native_association_v1_2_analysis_20261005.json)). A source-locked native reader-selection experiment then uses disjoint fit/validation/corner partitions. The graph-side unique selector chooses in 3/6 seeds and explicitly abstains on three validation ties; conditional corner accuracy is 21/24 (87.5%), with 50% coverage, while full-coverage prototype distance scores 37/48. Thus native selection is demonstrated, but its ties reduce unconditional utility under ordinary accuracy scoring ([results](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_1_RESULTS_20261005.md), [initial protocol](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_PREREG_20261005.md), [v1.1 amendment](SUBSTRATE_NATIVE_READOUT_SELECTION_GATE_V1_1_AMENDMENT_20261005.md), [runner](../../../evaluation/substrate_capability/vision_eye_native_reader_selection_v1_1.py), [capture](../../../evaluation/reports/vision_eye_native_reader_selection_v1_1_20261005.json), [analysis](../../../evaluation/reports/vision_eye_native_reader_selection_v1_1_analysis_20261005.json)).",
                   "A fresh seeds 46–51 validation-breadth cohort doubles distinct validation positions while keeping the fit schedule fixed. Ties fall from 3/6 to 1/6 seeds, but conditional corner accuracy is 24/40 at 83.3% coverage and overall yield is 24/48, below fixed prototype distance at 32/48. Wider validation reduced abstention but did not improve transfer utility ([results](SUBSTRATE_NATIVE_READOUT_SELECTION_VALIDATION_BREADTH_V1_RESULTS_20261005.md), [protocol](SUBSTRATE_NATIVE_READOUT_SELECTION_VALIDATION_BREADTH_V1_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/vision_eye_native_reader_selection_v1_2.py), [capture](../../../evaluation/reports/vision_eye_native_reader_selection_v1_2_20261005.json), [analysis](../../../evaluation/reports/vision_eye_native_reader_selection_v1_2_analysis_20261005.json)).",
                   "A numeric-family transfer replay applies the native graph-rule scorer and ArgminUnique to ten existing panels. It uniquely selects the correct supplied additive/product candidate in 10/10 panels, transfers exactly on 12,960/12,960 sealed-grid rows, and has no ties. The known useful family is always present in the two-item menu; the panel family is reused from earlier work and does not establish open-ended discovery ([results](SUBSTRATE_NATIVE_PRIMITIVE_FAMILY_SELECTION_TRANSFER_V1_RESULTS_20261005.md), [protocol](SUBSTRATE_NATIVE_PRIMITIVE_FAMILY_SELECTION_TRANSFER_V1_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_primitive_family_selection_transfer_v1.py), [capture](../../../evaluation/reports/native_primitive_family_selection_transfer_v1_20261005.json), [analysis](../../../evaluation/reports/native_primitive_family_selection_transfer_v1_analysis_20261005.json)).",
                   "A source-locked 75% raw validation-accuracy adequacy gate accepts all 10 additive/product controls but falsely accepts all 5 componentwise-opposition panels: the best supplied candidate scores 25–31/32 despite neither being exact on the sealed grid. Opposition validation is severely class-imbalanced (29–31 negatives of 32), exposing a model-adequacy and calibration gap rather than a graph-rule execution failure ([results](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V1_RESULTS_20261005.md), [protocol](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V1_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_candidate_adequacy_v1.py), [capture](../../../evaluation/reports/native_candidate_adequacy_v1_20261005.json), [analysis](../../../evaluation/reports/native_candidate_adequacy_v1_analysis_20261005.json)).",
                   "The 40-panel balanced-accuracy follow-up selects the correct additive/product controls 20/20 and requests help on inequality 10/10, but falsely accepts opposition 10/10; the product candidate averages 0.9719 balanced accuracy and 91.18% held-out raw accuracy while expressing the wrong relation. This shows class balancing fixes the earlier skew artifact but a fixed threshold still misses near-neighbor models ([results](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V2_RESULTS_20261005.md), [protocol](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V2_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_candidate_adequacy_v2.py), [capture](../../../evaluation/reports/native_candidate_adequacy_v2_20261005.json), [analysis](../../../evaluation/reports/native_candidate_adequacy_v2_analysis_20261005.json)).",
                   "A 40-panel minimum-class-accuracy gate preserves the 20/20 controls and rejects 7/10 opposition panels. In a fresh paired three-arm run, native ArgminUnique candidate-positive query selection exactly matches its host control across all 40 panels. Both candidate-positive arms catch the three observed opposition false accepts with four labels total; uniform catches one and leaves two selected. The native selector is slower: median selected-worker CPU is 1.29 s versus 0.30 s host-side, with 0.92 s median spent in repeated native selection closures. Correctness responsibility moved into graph rules, while performance and challenge prevalence require follow-up ([query results](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_2_RESULTS_20261005.md), [protocol](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_2_PREREG_20261005.md), [query analysis](../../../evaluation/reports/native_candidate_adequacy_query_v1_2_analysis_20261005.json)).",
                   "Domain-specific learning results, source-mutation proposal results, supervised codebook growth, and P3 safety readiness must remain separate evidence rows/claims; no general continual-learning or transfer guarantee follows."],
    },
    "rule_dependency_and_scheduling": {
        "status": "partially_audited",
        "canonical_state_owner": "The Rust Substrate owns the live RewriteRule vector, derived access sets, dirty flags, match cursors, graph, and scheduler state. Python seed manifests configure rules before execution; scoped and alternative schedulers are explicit calls into the same Rust owner.",
        "python_shadow_or_indexes": "PySubstrate holds the Rust Substrate behind its native wrapper. The Python rule IR and seed manifests are loading/configuration representations, not live scheduler state. Optional audit counters are process-global or thread-local Rust state and are exposed through explicit PyO3 methods.",
        "normal_entrypoints": [
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules", "default native closure entrypoint; uses the ordinary dirty-rule scheduler"),
            ("runners/dsl/src/rewrite.rs", "RewriteRule::derive_access", "called while installing rules to derive conservative static read/write resources"),
            ("runners/dsl/src/py.rs", "PySubstrate::rule_access_sets", "explicit read-only diagnostic; reports derived resources and wildcard flags"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/substrate.rs", "Substrate::run_rules_scoped", "explicit opt-in settlement restricted to caller-supplied rule indices"),
            ("runners/dsl/src/area_scheduler.rs", "derive", "alternative dependency-SCC schedule derivation; not the default closure loop"),
            ("runners/dsl/src/wave_stencil.rs", "stencil_tick", "guarded opt-in batched stencil path with optional residual closure"),
            ("runners/dsl/src/stage_a.rs", "set_compare_mode", "opt-in diagnostic comparison of eligible Stage A proposals with committed execution"),
        ],
        "limits": ["The native resource model is conservative and global by edge/type/attribute keys, not a measured per-node dynamic access trace.",
                   "Attribute-only effect readers have a documented stale-output boundary under suppression; a settled scheduler state is not truth maintenance.",
                   "Alternative scheduler mechanisms have workload-specific evidence and are not interchangeable with the default path."],
    },
    "graph_persistence_and_seed_loading": {
        "status": "partially_audited",
        "canonical_state_owner": "The live graph and installed native rules reside in Rust Substrate. Python boot/load code selects and orders seed manifests; WorldAdapter owns additional host-side world-to-graph indexes and serializes them with the native graph/rules in explicit checkpoints.",
        "python_shadow_or_indexes": "substrate.persistence reconstructs Python TypedGraph indexes from native graph snapshots. WorldAdapter separately owns instance/concept/body-type indexes and mirrors; seed-index caches and boot observations are host-side loading metadata, not graph contents.",
        "normal_entrypoints": [
            ("substrate/boot_core.py", "boot_core", "explicit minimal/core boot; creates a native substrate and loads dependency-ordered core seeds"),
            ("substrate/boot_all.py", "load_all_seeds", "host orchestration for the configured full or selected seed set"),
            ("substrate/boot_all.py", "load_one_seed", "explicit single-seed installation path"),
            ("runners/dsl/src/py.rs", "PySubstrate::graph_to_dict", "native graph snapshot readback, preserving node identifiers and edge attributes"),
            ("substrate/persistence.py", "graph_from_dict", "Python graph wrapper reconstruction from a native snapshot"),
        ],
        "alternate_entrypoints": [
            ("substrate/world_adapter.py", "WorldAdapter::save", "explicit whole-adapter checkpoint write, including graph, grammar, rules, and selected indexes"),
            ("substrate/world_adapter.py", "WorldAdapter::load", "explicit checkpoint restore; host indexes are reconstructed around a fresh native substrate"),
            ("runners/dsl/src/persist.rs", "graph_diff", "native JSON graph-difference utility; not the normal boot path"),
        ],
        "limits": ["Seed loading, native graph serialization, Python graph wrappers, and full WorldAdapter checkpoints are distinct persistence paths.",
                   "This source map does not establish durable atomic writes, corruption detection, complete restoration of all session state, or large-graph performance.",
                   "Seed caches and optional profiles can change boot work; their cold-start and invalidation costs require separate measurement."],
    },
    "vision_perception_primitives": {
        "status": "partially_audited",
        "canonical_state_owner": "Image and shape observations enter through Python WorldAdapter or vision-domain adapters. Native ChangeDetect/Foveate term evaluation reads graph-backed image/kernel values, calls pure Rust arithmetic, then returns a Value to the rule evaluator; the primitive module itself owns no persistent graph state.",
        "python_shadow_or_indexes": "WorldAdapter holds frame/session caches and projects upload-derived shapes into the native graph. domains.vision_graph has its own Python RGBEye processing path with NumPy arrays. These paths are separate from the pure Rust vision_primitives functions and must not be pooled as one implementation.",
        "normal_entrypoints": [
            ("substrate/world_adapter.py", "WorldAdapter::update_vision", "host-managed live-frame pathway; activation depends on configured vision adapter"),
            ("runners/dsl/src/term.rs", "evaluate", "native Term evaluator; ChangeDetect/Foveate arms call pure Rust vision primitives"),
            ("runners/dsl/src/vision_primitives.rs", "convolve", "pure arithmetic primitive invoked by ChangeDetect; not a standalone perception system"),
            ("runners/dsl/src/vision_primitives.rs", "foveate", "pure arithmetic primitive invoked by the Foveate term"),
            ("substrate/world_adapter.py", "WorldAdapter::perceive_upload_image", "explicit upload-image ingestion and graph projection path"),
        ],
        "alternate_entrypoints": [
            ("domains/vision_graph.py", "RGBEye::_process_frame", "Python/NumPy frame processing path, distinct from native Term evaluation"),
            ("runners/dsl/src/vision_primitives.rs", "temporal_diff", "pure elementwise frame-difference primitive; called by the native ChangeDetect term"),
            ("substrate/world_adapter.py", "WorldAdapter::refresh_upload_vision_if_needed", "explicit cached upload reprocessing path"),
        ],
        "limits": ["The Rust primitives are arithmetic building blocks; their existence does not establish end-to-end visual recognition or a default sensor path.",
                   "Live-frame Python processing, uploaded-image segmentation, graph-authored recognition, and native Term primitives have different state owners and quality criteria.",
                   "The inventory does not establish performance or robustness under resolution, lighting, noise, modality, and distribution shifts."],
    },
    "determinism_trace_and_scale_instrumentation": {
        "status": "partially_audited",
        "canonical_state_owner": "Instrumentation state is split across native process-global atomics/mutexes, thread-local attribution, per-Substrate debug state, and Python probes. Counter ownership and reset scope therefore depend on the instrument; there is no single trace store.",
        "python_shadow_or_indexes": "PyO3 exposes selected enable/reset/snapshot methods. Python benchmark scripts add wall/CPU/RSS records and may write JSON reports; those records are separate from native counters. Some counters are disabled by default while selected diagnostics have their own global mode.",
        "normal_entrypoints": [
            ("runners/dsl/src/py.rs", "PySubstrate::scale_audit_snapshot", "explicit opt-in audit readback; aggregate native counters"),
            ("runners/dsl/src/py.rs", "PySubstrate::scale_audit_per_rule_snapshot", "explicit opt-in per-rule attribution readback"),
            ("runners/dsl/src/py.rs", "scale_audit_rule_identity_snapshot", "maps process-local audit IDs to store instance and local rule index"),
            ("runners/dsl/src/py.rs", "scale_audit_mode_snapshot", "reads process, calling-thread, and per-rule audit gates"),
            ("runners/dsl/src/py.rs", "scale_audit_mode_trace_snapshot", "opt-in history of audit setter transitions during a measured call"),
            ("runners/dsl/src/py.rs", "PySubstrate::evaluate", "direct host Term evaluation, classified separately from matcher-owned rule work"),
            ("runners/dsl/src/scale_audit.rs", "register_rule_audit_metadata_in_store", "store-qualified matcher identity and metadata registration"),
            ("runners/dsl/src/py.rs", "PySubstrate::fallback_attr_totals", "explicit readback of fallback instrumentation counters; separate defaulted/absence report methods are also available"),
            ("evaluation/substrate_capability/live_runtime_pre_request_state_v1.py", "main", "source-locked full primary graph/rule snapshots at each request boundary with parent route parity gates"),
            ("evaluation/substrate_capability/analyze_live_runtime_pre_request_state_v1.py", "main", "independent checkpoint digest, graph integrity, and request-boundary equality validation"),
            ("evaluation/substrate_capability/live_runtime_store_states_v1_2.py", "main", "source-locked capture of per-request matcher-store graphs and cumulative scoped rule slots"),
            ("evaluation/substrate_capability/analyze_live_runtime_store_states_v1_2.py", "main", "independent store payload integrity and all-identity-to-rule-slot reconciliation"),
            ("evaluation/substrate_capability/live_runtime_closure_entry_states_v1_1.py", "main", "source-locked exact graph/rule snapshots before each primary live run_rules call"),
            ("evaluation/substrate_capability/analyze_live_runtime_closure_entry_states_v1_1.py", "main", "independent closure-entry payload integrity and route parity checks"),
            ("evaluation/substrate_capability/live_runtime_closure_entry_replay_v1.py", "main", "restore and replay each primary closure call from its captured entry state"),
            ("evaluation/substrate_capability/analyze_live_runtime_closure_entry_replay_v1.py", "main", "per-rule counter reconciliation of replay against selected-route counters"),
            ("evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1.py", "main", "read dirty-rule count and names immediately before each primary closure call"),
            ("evaluation/substrate_capability/analyze_live_runtime_dirty_rule_entry_audit_v1_1.py", "main", "aligns live dirty-rule counts with first-pass scheduler selection and later-pass residuals"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/scale_audit.rs", "set_enabled", "native aggregate audit enable switch; off by default"),
            ("runners/dsl/src/scale_audit.rs", "set_per_rule_enabled", "native per-rule attribution switch; opt-in and adds map/mutex cost"),
            ("runners/dsl/src/stage_a.rs", "set_compare_mode", "opt-in Stage A compare instrumentation"),
            ("substrate/control_trace_probe.py", "reduce_trace", "pure Python trace reducer; consumes supplied records and does not instrument the native engine"),
        ],
        "limits": ["Counter families differ in scope, reset semantics, attribution, and overhead; a snapshot is not a complete execution trace.",
                   "Deterministic replay and cross-process equivalence have not been established for the substrate as a whole.",
                   "Instrumented-versus-uninstrumented ratios remain workload- and host-dependent; no unified provenance wrapper is yet mandatory for all runners.",
                   "Store-qualified rule attribution passes focused serial/Rayon and PyO3 controls (live runtime closure attribution control v1.1). V1.4 audit-off counts came from three nested producer-event measurement windows that enabled and reset the same process-global audit; v1.5 delegates those inner operations to the outer request scope and passes zero-work audit-off on all six requests. V1.6 classifies all 145/134 unassigned Term evaluations as direct host `PySubstrate.evaluate` calls; matcher-context loss and ambiguous identities are zero, and per-rule + host + global Term counts conserve on the selected route (SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_6_RESULTS_20261004.md). A derived census of 2,357 exported rules classifies only 2 within the finite-key checker fragment; those had zero measured work in the fixed two-request route. One request counter snapshot omitted 13 baseline identities; they remain marked unobserved (SUBSTRATE_LIVE_RUNTIME_RULESET_CENSUS_V1_RESULTS_20261004.md). Four exact primary graph/rule request-boundary checkpoints and 14 first-graph/cumulative-rule store snapshots now match the selected route's outputs; the independent analyzer reconciles all 4,745 observed store-qualified identities (SUBSTRATE_LIVE_RUNTIME_PRE_REQUEST_STATE_V1_RESULTS_20261004.md; SUBSTRATE_LIVE_RUNTIME_STORE_STATES_V1_2_RESULTS_20261004.md). A primary call-entry replay restores all 15 graphs and ordered rule bodies but remains 10–21% high on aggregate candidate/Term work; the dirty-rule audit verifies that entry dirty bits match first-pass scheduler selections exactly and later passes account for the residual selections (SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V1_RESULTS_20261004.md; SUBSTRATE_LIVE_RUNTIME_DIRTY_RULE_ENTRY_AUDIT_V1_RESULTS_20261004.md). Remaining scheduler state, simultaneous secondary-store boundary state, natural workload frequency, and broad scaling remain unmeasured."],
    },
    "planning_and_action_selection": {
        "status": "partially_audited",
        "canonical_state_owner": "P2-B1 bounded planning records and selection are pure Rust values/functions. P2-Native constructs a proposal from a bounded public envelope, while a separate evaluator reconstructs and scores expected output. Neither grants or executes a world action. domains/operational_planning.py is a separate Python/graph orchestration path.",
        "python_shadow_or_indexes": "P2-Native communicates through JSON envelopes and proposals; no Python mirror owns bounded selection state. operational_planning uses Python graph/host objects and may dispatch configured capabilities, so it must not be conflated with P2 proposal generation.",
        "normal_entrypoints": [
            ("runners/dsl/src/p2_bounded.rs", "revise_belief", "bounded belief revision; monotonic epoch and confidence partition checks"),
            ("runners/dsl/src/p2_bounded.rs", "simulate_one_action", "one-step imagined transition; requires a legal action and transition witness"),
            ("runners/dsl/src/p2_bounded.rs", "select_all_actions", "all-actions feasibility/minimality/tie selection; max four actions"),
            ("runners/dsl/src/p2_native.rs", "worker_reply", "JSON worker proposal path; bounded graph and action set"),
            ("runners/dsl/src/p2_native.rs", "evaluator_reply", "separate evaluator reconstructs expected proposal and scores worker match"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/p4_readiness.rs", "advance_p4_r0", "gated readiness state machine; not evidence of long-horizon planning"),
            ("domains/operational_planning.py", "run_plan", "legacy/domain Python orchestration; separate capability and effect path"),
        ],
        "limits": ["P2-B1 fixes horizon and branching to one, allows at most four actions and eight nodes per action, and does not measure open-ended search complexity.",
                   "The P2 evaluator scores a sealed toy transition vocabulary; it is not a held-out-world planning result.",
                   "P2 selection provides no action authority or external execution; operational_planning and host-I/O adapters require separate route and containment evaluation.",
                   "P4-R0 readiness protocol is staged evidence plumbing, not a demonstrated long-horizon planner."],
    },
    "tools_external_i_o_and_world_adapters": {
        "status": "partially_audited",
        "canonical_state_owner": "Host effects execute in Python adapters/handlers. Native Term::UseTool only evaluates arguments and crosses the GIL into a process-global Python callback registry; it does not own the effect or enforce an authority grant. Effect results and call history may be projected back into graph state by the Python wrapper.",
        "python_shadow_or_indexes": "domains/tool_use.py owns a process-local handler dictionary keyed by handler_key and graph ToolSpec metadata; runners/dsl/src/tools.rs separately owns a process-global Rust name-to-Python-callable registry. domains/agent_tools.py owns ToolBox configuration and an in-memory log. WorldAdapter pending-request scanning delegates to fetch/upload adapters and catches broad exceptions.",
        "normal_entrypoints": [
            ("domains/tool_use.py", "use_tool", "typed graph-visible host dispatch; typecheck then handler call and result recording"),
            ("runners/dsl/src/tools.rs", "call_tool", "native Term callback into Python; missing handler/errors become integer zero"),
            ("substrate/world_adapter.py", "_dispatch_pending_io", "host fulfillment of graph-minted search/detail/grounding/upload requests; direct-I/O guard denies only inside an activated P0-A context"),
            ("domains/http_transport.py", "http_get", "bounded GET transport with scheme/redirect restrictions, timeouts, and connection pooling"),
            ("domains/agent_tools.py", "install_tools", "explicit opt-in installation of read/write/shell capabilities"),
        ],
        "alternate_entrypoints": [
            ("domains/tool_use.py", "register_real_tools", "explicit demo registry includes library and subprocess handlers"),
            ("domains/tool_use.py", "register_native_handlers", "explicitly mirrors Python handlers into native process-global callback registry"),
            ("domains/agent_tools.py", "ToolBox::read_file", "reads any path readable by process user; workspace restriction does not apply to reads"),
            ("domains/agent_tools.py", "ToolBox::write_file", "workspace-scoped writes unless override is enabled"),
            ("domains/agent_tools.py", "ToolBox::run_command", "shell=True in workspace cwd with inherited process environment; cwd is not a sandbox"),
            ("scripts/substrate_external_effect_census.py", "main", "read-only AST source census; does not import or execute effects"),
            ("scripts/substrate_p0a_denial_probe.py", "run_probe", "fresh-process local P0-A compatibility guard probe; no handler invocation or OS-sandbox claim"),
        ],
        "limits": ["A typed ToolSpec and graph-visible ToolCall record document an effect; they do not provide authorization, isolation, or a receipt-backed transaction.",
                   "Native call_tool maps absent handlers, poisoned registry, handler exceptions, None, and unsupported return values to Value::Int(0), which can conflate failure with a valid zero result.",
                   "process_handler uses argv without shell interpolation but does not require zero exit status; ToolBox.run_command uses shell=True and inherits environment, while reads are unrestricted by workspace.",
                   "WorldAdapter catches dispatch errors; direct-I/O denial is conditional on the ContextVar guard being active under the P0-A entrypoint, so ordinary workflows are not shown to be default-deny.",
                   "The 2026-09-25 AST census parses 832 files and finds 37 process, 19 network, 6 explicit guard, and 14 tool-registration call sites; two process calls share a function scope with a guard, while the fetch guard is separate from its fallback urlopen call. This is source-level candidate evidence, not dynamic route coverage.",
                   "A fresh-process denial-only probe blocks all eight named guard routes and nine patched low-level primitives (17/17), with zero handler calls. A 747-node default WorldAdapter core boot has zero ToolSpecs and empty Python/native handler registries, with four introspection capabilities. Separately registering the explicit tool-use demo pack creates five ToolSpecs and five handlers in both registries, with no ToolCall and no native fire-count increase. Optional profiles and daemon startup remain unmeasured; this is local compatibility interception, not OS isolation or evaluator custody.",
                   "Static route inventory is not exhaustive dynamic reachability or containment evidence; quotas, authorization, replay, effect/receipt parity, and native/host state divergence remain unmeasured."],
    },
    "conversation_goal_lifecycle_and_event_identity": {
        "status": "partially_audited",
        "canonical_state_owner": "Conversation DiscourseState, Goal, and DiscourseEvent facts live in the Rust TypedGraph through PySubstrate. Python discourse/conversation/WorldAdapter functions produce inputs and read/write the graph; the native rule engine executes the seeded lifecycle transitions.",
        "python_shadow_or_indexes": "No separate durable Python shadow owns the lifecycle. WorldAdapter reads discourse_state_id/discourse_event_id from the inbound Message and binds live cognition to graph nodes; conversation_action passes the Goal handle directly to record_event, which writes for_goal in the graph. Phase 4A execution traces are a separate graph relation and are not discourse lifecycle events.",
        "normal_entrypoints": [
            ("substrate/world_adapter.py", "converse", "live text conversation entrypoint; records inbound discourse event and routes action faculty"),
            ("domains/conversation_action.py", "_record_live_goal_event", "self-report route records explicitly Goal-bound selection/execution/result or failure events"),
            ("domains/discourse_state.py", "record_event", "graph event writer; optional Goal handle becomes an explicit for_goal edge"),
            ("runners/dsl/src/py.rs", "parse_effect_json", "seed rule effects, including DelEdge, are parsed into native rewrite effects"),
            ("runners/dsl/src/substrate.rs", "run_rules", "native fixed-point execution of the discourse lifecycle seed rules"),
            ("substrate/world_adapter.py", "_bind_live_goals_and_deliberation", "binds cognition and preserves terminal active/closed Goal membership invariants"),
        ],
        "alternate_entrypoints": [
            ("domains/discourse_state.py", "open_goal", "direct Goal creation helper; caller supplies the origin event"),
            ("domains/discourse_state.py", "transition_goal", "explicit Python lifecycle transition helper; not the native live route used by the integration capture"),
            ("scripts/substrate_live_self_report_lifecycle_identity_integration_v1.py", "controls", "measurement harness for correct/omitted/swapped identity, duplicate result, and faculty-failure controls"),
        ],
        "limits": ["The confirmatory producer integration covers only the live held self-report branch; scene, concern, goal-only, operational-planning, and external-I/O action routes remain unaudited for lifecycle production.",
                   "The two live requests execute sequentially; interleaved concurrent active Goals, cancellation, recovery after process failure, and effect receipt durability remain unmeasured.",
                   "The native transition rules require explicit for_goal identity, but full transition coverage and state invariants are measured only on the named live route and bounded controls."],
    },
    "conversation_cognition_interlocutor_models_and_production": {
        "status": "partially_audited",
        "canonical_state_owner": "Conversation observations, audience/interlocutor models, self-model facts, and deliberation records are represented in the Rust TypedGraph through PySubstrate. Python domain functions interpret those records, propose communicative content, and apply the configured production gate.",
        "python_shadow_or_indexes": "Audience, interlocutor, context, self-model, and production helpers maintain derived Python views/caches over graph records. This row covers conversation cognition/production components, not the separate Goal/event identity transition contract.",
        "normal_entrypoints": [
            ("domains/conceptualizer.py", "conceptualize_reply", "live response conceptualization path"),
            ("domains/audience_driven_production.py", "select_utterance", "audience-conditioned utterance selection"),
            ("domains/conversation_deliberation.py", "materialize_deliberation", "deliberative candidate materialization"),
            ("domains/self_model.py", "ensure_self_model", "self-model graph setup/read path"),
        ],
        "alternate_entrypoints": [
            ("domains/audience_adaptation.py", "adapt_concepts", "audience-relative content adaptation"),
            ("domains/interlocutor_model.py", "observe_turn", "interlocutor model update"),
            ("domains/production_gate.py", "release_if_gated", "explicit production release gate"),
            ("domains/self_organisation_reader.py", "run_self_organisation", "held-organization introspection"),
        ],
        "limits": ["The live module-activation panel covers five authored conversation routes with two workers each; four task contracts pass and concern authoring fails in both workers.",
                   "Python call traces do not establish causal necessity or native execution cost; audience/model quality, cross-recipient transfer, and natural route prevalence remain unmeasured.",
                   "Goal/event ownership and lifecycle correctness are covered by a separate capability row and must not be inferred from this activation trace."],
    },
    "language_understanding_and_lexical_grounding": {
        "status": "partially_audited",
        "canonical_state_owner": "Python language-domain functions perform selected parsing, construction, lexical, and reference operations; graph-resident language/concept facts are held in the Rust TypedGraph. WordNet/Wiktionary reference data and mmap slab indexes are external or host-side supporting state.",
        "python_shadow_or_indexes": "The language layer has Python lexicon/reference helpers and graph adapters. Seed registration and lexical slabs support multiple language routes but are not independent semantic reasoning capabilities.",
        "normal_entrypoints": [
            ("domains/comprehend_text.py", "comprehend_text", "general text comprehension entrypoint"),
            ("domains/comprehend_question.py", "comprehend_know", "question/knowledge comprehension route"),
            ("domains/language.py", "ingest", "language graph ingestion"),
            ("domains/construction_grammar.py", "apply_constructions", "construction application"),
            ("domains/sense_of_reference.py", "decode_reference", "reference interpretation"),
        ],
        "alternate_entrypoints": [
            ("domains/instruction_reading.py", "gather_lexicon", "instruction vocabulary path"),
            ("domains/function_word_reference.py", "classify", "function-word reference lookup"),
            ("domains/wordnet_membership.py", "lemmas", "WordNet lemma lookup over warmed external index"),
            ("domains/wiktionary_reference.py", "wiktionary_gloss", "Wiktionary-derived lexical lookup"),
            ("domains/wordplay.py", "detect_coinage", "coinage/novel-word detection"),
        ],
        "limits": ["The current live activation result covers selected conversation wording and lexical clarification, not a representative language benchmark or broad semantic accuracy.",
                   "The WordNet index was prebuilt and locked; cold index construction cost is not part of the task timing.",
                   "External lexical data, file-backed slabs, seed registry, graph-authored rules, and Python parsing are separate ownership/cost paths and require their own failure and resource controls.",
                   "Transfer across paraphrase, discourse state, domains, languages, and malformed/noisy input remains open."],
    },
    "graph_resident_frame_and_context_representation": {
        "status": "partially_audited",
        "canonical_state_owner": "Concept dimensions, frame membership, and context facts are represented in the Rust TypedGraph; Python DomainPlug functions compute context/interlocutor projections and collapse inputs for selected reasoning/communication paths.",
        "python_shadow_or_indexes": "Frame/context helpers consume graph snapshots and can maintain local derived maps; these structures are not established as mandatory native rule partitions or separators.",
        "normal_entrypoints": [
            ("domains/frame.py", "build_frame", "graph-resident frame construction"),
            ("domains/concept_graph.py", "world_dimension", "concept graph dimension readout"),
            ("domains/context_model.py", "context_frame", "context-frame construction"),
            ("domains/context_collapse_plug.py", "collapse_context", "context DomainPlug projection"),
        ],
        "alternate_entrypoints": [
            ("domains/interlocutor_collapse_plug.py", "collapse_residual", "interlocutor-model DomainPlug projection"),
        ],
        "limits": ["The conversation task trace establishes that selected frame/context Python paths execute, not that their representations are semantically complete or necessary.",
                   "Graph-resident frames and context plugs are not evidence of cheap separators, bounded treewidth, factorized native inference, or natural hierarchical sparsity.",
                   "Frame induction, boundary-size distribution, cross-scale consistency, mutation invalidation, and frame-construction cost remain unmeasured."],
    },
    "native_cognitive_runtime_and_scheduling": {
        "status": "partially_audited",
        "canonical_state_owner": "The Rust Substrate owns graph-resident CognitiveTask lifecycle state. Native schedulers, worker pools, and cache utilities own their local queues/caches; Python supplies requests and worker capacity.",
        "python_shadow_or_indexes": "Python adapters construct graph requests and invoke native ticks. Native work-stealing/EDF utility schedulers are not necessarily the same route as graph-requested task execution.",
        "normal_entrypoints": [
            ("runners/dsl/src/cognitive_cycle.rs", "execute", "native cognitive cycle"),
            ("runners/dsl/src/cognitive_tasks.rs", "run_requested", "graph-requested worker execution"),
            ("runners/dsl/src/l2_dispatch.rs", "submit", "native scheduler utility"),
            ("runners/dsl/src/reflex_runtime.rs", "next_ready", "ready-task selection"),
        ],
        "alternate_entrypoints": [
            ("runners/dsl/src/l2_dispatch_work_stealing.rs", "submit", "alternate work-stealing scheduler"),
            ("runners/dsl/src/effort_dial.rs", "blend_effort", "effort allocation utility"),
        ],
        "limits": ["Historical async-core performance has not been verified against the current source snapshot.", "Queueing, cancellation, starvation, and mixed-workload behavior remain unmeasured."],
    },
    "feedback_control_and_viability": {
        "status": "partially_audited",
        "canonical_state_owner": "Numerical controller state is held in native Rust structures; selected viability and future-manifold paths read graph snapshots or explicit inputs. System integration remains workload-specific.",
        "python_shadow_or_indexes": "Python simulation and flight-control harnesses provide inputs and collect outputs; they are not a universal native control loop.",
        "normal_entrypoints": [
            ("runners/dsl/src/l3_drives.rs", "step_sum", "multi-drive aggregation"),
            ("runners/dsl/src/l3_kalman_nd.rs", "predict", "Kalman prediction"),
            ("runners/dsl/src/l3_lqr.rs", "compute_lqr_gain", "LQR gain computation"),
            ("runners/dsl/src/l3_mpc.rs", "solve", "scalar MPC solve"),
            ("runners/dsl/src/l6_cybernetic_feedback.rs", "tick", "feedback loop update"),
            ("runners/dsl/src/future_manifold.rs", "projection_field", "future projection"),
        ],
        "alternate_entrypoints": [("runners/dsl/src/l4_subsystem_boundaries.rs", "", "boundary utilities"), ("runners/dsl/src/l6_ashby_variety.rs", "", "variety utilities"), ("runners/dsl/src/l6_essential_variables.rs", "", "essential-variable viability")],
        "limits": ["The measured flight-control study includes negative fault-regime outcomes and does not validate every controller in this family.", "Stability, robustness, and integration cost need independent oracles and task coverage."],
    },
    "motor_program_synthesis_and_trajectory_generation": {
        "status": "partially_audited",
        "canonical_state_owner": "Native motor composition and trajectory functions compute candidates from explicit inputs; graph rules and host adapters supply task, body, and cost context.",
        "python_shadow_or_indexes": "Embodied simulation and task harnesses own environment state and evaluate generated movement; a generated plan is not itself enacted control.",
        "normal_entrypoints": [("runners/dsl/src/motor_compose.rs", "motor_compose_member", "native composition candidate")],
        "alternate_entrypoints": [("runners/dsl/src/sigma_lognormal.rs", "", "trajectory primitive"), ("runners/dsl/src/strokes.rs", "", "stroke quantization")],
        "limits": ["Selected tests and one frozen controller stack do not estimate general synthesis success or transfer.", "Measure search cost, movement constraints, and perception-to-action performance."],
    },
    "auditory_signal_processing_and_learned_speech_representations": {
        "status": "partially_audited",
        "canonical_state_owner": "Auditory signal stages and APC model routines are native Rust functions; training data and evaluation harness state are owned by their application runners.",
        "python_shadow_or_indexes": "Python data pipelines prepare examples and collect representation metrics; no default integrated conversation-audio route is established by these modules.",
        "normal_entrypoints": [("runners/dsl/src/audio_primitives.rs", "gammatone_band", "filterbank primitive"), ("runners/dsl/src/auditory_cortex.rs", "process_audio", "auditory cortical stage"), ("runners/dsl/src/cochlear_nucleus.rs", "process_audio", "cochlear stage"), ("runners/dsl/src/inferior_colliculus.rs", "process_audio", "midbrain stage"), ("runners/dsl/src/apc.rs", "encode", "APC representation encoder")],
        "alternate_entrypoints": [("runners/dsl/src/apc.rs", "train_masked_cpc", "masked CPC training path")],
        "limits": ["The fair-pool representation study reports a substantial gap versus wav2vec2; it is not an ASR or dialogue benchmark.", "Current-source provenance and downstream integration remain unverified."],
    },
    "video_codec_and_transcoding_pipeline": {
        "status": "partially_audited",
        "canonical_state_owner": "Bitstream and frame buffers are passed through native codec/transcoding routines; graph-resident FieldSpec rules are separately installed in the Rust Substrate.",
        "python_shadow_or_indexes": "Python harnesses provide bitstreams, reference codec calls, and result comparisons; this does not imply complete standards-conformant native decoding.",
        "normal_entrypoints": [("runners/dsl/src/h264_cabac_mb.rs", "decode_i_macroblock", "H.264 intra macroblock decode"), ("runners/dsl/src/h264_deblock.rs", "deblock_i_frame", "H.264 deblocking"), ("runners/dsl/src/h264_slice_header.rs", "walk_h264_slice_header", "H.264 slice-header walk"), ("runners/dsl/src/h265_slice_header.rs", "emit_h265_slice_header", "H.265 slice-header emission"), ("runners/dsl/src/h265_transcode_driver.rs", "transcode_slice", "slice transcode path"), ("runners/dsl/src/codec.rs", "install_field_grammar_rules", "graph-resident codec grammar installation")],
        "alternate_entrypoints": [("runners/dsl/src/cabac.rs", "", "CABAC primitive"), ("runners/dsl/src/h264_dct.rs", "", "H.264 transform"), ("runners/dsl/src/h264_inter_pred.rs", "", "H.264 inter prediction"), ("runners/dsl/src/h265_cabac.rs", "", "HEVC CABAC primitive"), ("runners/dsl/src/h265_ctu_quadtree.rs", "", "HEVC CTU quadtree")],
        "limits": ["The activation study retains eight HEVC/fixed-array failures and one vacuous prior pass.", "Broad standards conformance, throughput, malformed-stream handling, and memory scaling remain unmeasured."],
    },
    "graph_resident_neural_and_operation_pipeline_execution": {
        "status": "partially_audited",
        "canonical_state_owner": "Graph-authored network and pipeline specifications reside in the Rust Substrate; native evaluators execute numerical operations over the supplied structures.",
        "python_shadow_or_indexes": "Python adapters construct/select graph specifications and provide selected reference implementations; learned-weight training is outside the audited native path.",
        "normal_entrypoints": [("runners/dsl/src/net_forward.rs", "net_forward_core", "native graph neural forward pass"), ("runners/dsl/src/pipeline_runtime.rs", "run_pipeline", "native operation pipeline")],
        "alternate_entrypoints": [],
        "limits": ["Parity tests do not establish training, robust generalization, large-network scaling, or end-to-end utility."],
    },
    "graph_resident_hypothesis_admissibility": {
        "status": "partially_audited",
        "canonical_state_owner": "Candidate/problem facts reside in the Rust Substrate graph; native admissibility predicates compute bounded constraint checks and witnesses.",
        "python_shadow_or_indexes": "Python test fixtures and application code construct candidate graph facts; predicates do not provide a general learner or complete solver.",
        "normal_entrypoints": [("runners/dsl/src/enigma.rs", "crib_admissible", "crib consistency predicate"), ("runners/dsl/src/enigma.rs", "bombe_admissible", "Bombe candidate filter"), ("runners/dsl/src/enigma.rs", "bombe_witness", "candidate witness extraction")],
        "alternate_entrypoints": [],
        "limits": ["Completeness, false acceptance/rejection, larger-instance scaling, and comparison to exhaustive oracles remain unmeasured."],
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_rows(text: str) -> list[list[str]]:
    section = text.split("## Initial map", 1)[1].split("## What this inventory establishes", 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] != "Capability area":
            rows.append(cells)
    return rows


def local_link_targets(cell: str) -> list[str]:
    targets = []
    for target in re.findall(r"\]\(([^)]+)\)", cell):
        if target.startswith(("http://", "https://", "#")):
            continue
        targets.append(target.split("#", 1)[0])
    return list(dict.fromkeys(targets))


def source_refs(cell: str) -> list[str]:
    refs = []
    for token in re.findall(r"`([^`]+)`", cell):
        if "/" in token and (token.endswith((".rs", ".py", ".json")) or "::" in token):
            refs.append(token)
    return list(dict.fromkeys(refs))


def source_link(ref: str) -> dict:
    path_text, sep, symbol = ref.partition("::")
    path = Path(path_text)
    candidates = [ROOT / path]
    if not path.is_absolute() and not path.exists() and len(path.parts) == 1:
        candidates += list((ROOT / "runners/dsl/src").glob(path.name))
        candidates += list((ROOT / "domains").glob(path.name))
        candidates += list((ROOT / "substrate").glob(path.name))
    existing = next((p.resolve() for p in candidates if p.is_file()), None)
    if existing is None:
        return {"ref": ref, "path": path_text, "symbol": symbol if sep else None,
                "resolved": False, "line": None}
    line = None
    if sep:
        leaf = symbol.split("::")[-1]
        pattern = re.compile(rf"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+{re.escape(leaf)}\b|\bdef\s+{re.escape(leaf)}\b")
        for number, text in enumerate(existing.read_text(errors="replace").splitlines(), 1):
            if pattern.search(text):
                line = number
                break
    return {"ref": ref, "path": str(existing.relative_to(ROOT)),
            "symbol": symbol if sep else None, "resolved": True, "line": line}


def classify_evidence_ref(ref: str) -> dict:
    """Classify each cited artifact without treating a benchmark as a test."""
    target = (MAP_DIR / ref).resolve()
    try:
        rel = target.relative_to(ROOT).as_posix()
    except ValueError:
        rel = None
    name = target.name.lower()
    if "tests" in target.parts and "evaluation" in target.parts:
        category = "evaluation_protocol_test"
    elif "tests" in target.parts:
        category = "test"
    elif "prereg" in name or "preregistration" in name or "_lock_" in name or name.endswith("_lock.json"):
        category = "protocol_or_lock"
    elif rel and rel.startswith("evaluation/reports/"):
        category = "raw_or_analysis_record"
    elif "results" in name and target.suffix.lower() in {".md", ".rst", ".txt"}:
        category = "result_document"
    elif rel and rel.startswith("scripts/"):
        category = "runner_or_analyzer"
    else:
        category = "supporting_reference"
    return {"ref": ref, "path": rel, "category": category, "exists": target.is_file()}


def discover_result_runners(refs: list[str]) -> list[dict]:
    """Follow result-document links to the runner/analyzer scripts they cite."""
    discovered: dict[str, dict] = {}
    for ref in refs:
        result_path = (MAP_DIR / ref).resolve()
        if not result_path.is_file() or result_path.suffix.lower() not in {".md", ".rst", ".txt"}:
            continue
        body = result_path.read_text(errors="replace")
        for target_text in re.findall(r"\]\(([^)]+)\)", body):
            target_text = target_text.split("#", 1)[0]
            if target_text.startswith(("http://", "https://", "mailto:")):
                continue
            target = (result_path.parent / target_text).resolve()
            try:
                rel = target.relative_to(ROOT).as_posix()
            except ValueError:
                continue
            if not rel.startswith("scripts/") or target.suffix != ".py":
                continue
            item = discovered.setdefault(rel, {
                "ref": "../../../" + rel,
                "path": rel,
                "category": "runner_or_analyzer",
                "exists": target.is_file(),
                "discovered_from": [],
            })
            item["discovered_from"].append(ref)
    for item in discovered.values():
        item["discovered_from"] = sorted(set(item["discovered_from"]))
    return [discovered[key] for key in sorted(discovered)]


def evidence_groups(refs: list[str]) -> dict:
    catalog = [classify_evidence_ref(ref) for ref in refs]
    runners = discover_result_runners(refs)
    tests = [item["ref"] for item in catalog if item["category"] == "test"]
    return {
        "evidence_catalog": catalog,
        "test_refs": tests,
        "evaluation_protocol_test_refs": [
            item["ref"] for item in catalog
            if item["category"] == "evaluation_protocol_test"],
        "result_refs": [item["ref"] for item in catalog if item["category"] == "result_document"],
        "protocol_refs": [item["ref"] for item in catalog if item["category"] == "protocol_or_lock"],
        "raw_record_refs": [item["ref"] for item in catalog if item["category"] == "raw_or_analysis_record"],
        "runner_catalog": runners,
        "runner_refs": sorted({item["ref"] for item in catalog if item["category"] == "runner_or_analyzer"}
                              | {item["ref"] for item in runners}),
        "supporting_refs": [item["ref"] for item in catalog if item["category"] == "supporting_reference"],
        "test_mapping_status": (
            "linked_tests_present; coverage not audited" if tests else
            "evaluation_protocol_only; functional coverage not audited"
            if any(item["category"] == "evaluation_protocol_test"
                   for item in catalog) else "no_test_link_in_map"),
    }


def build() -> dict:
    text = MAP.read_text()
    rows = table_rows(text)
    entries = []
    for area, implementation, ownership, evidence, open_measurement in rows:
        status_match = re.match(r"\*\*([^*]+)\*\*", evidence)
        status = status_match.group(1).strip() if status_match else "unclassified"
        slug = re.sub(r"[^a-z0-9]+", "_", area.lower()).strip("_")
        entrypoint_audit = AUDIT_NOTES.get(slug, {
            "status": "pending",
            "note": "Exact callable entrypoint, default/opt-in status, and state ownership require source-path audit.",
        })
        if "normal_entrypoints" in entrypoint_audit:
            entrypoint_audit = dict(entrypoint_audit)
            for key in ("normal_entrypoints", "alternate_entrypoints"):
                entrypoint_audit[key] = [
                    {**source_link(f"{path}::{symbol}"), "activation": activation}
                    for path, symbol, activation in entrypoint_audit.get(key, [])
                ]
        refs = local_link_targets(evidence)
        entries.append({
            "id": slug,
            "capability_area": area,
            "implementation_surface": implementation,
            "source_links": [source_link(ref) for ref in source_refs(implementation)],
            "ownership_and_path_shape": ownership,
            "evidence_status": status,
            "evidence_summary": evidence,
            "evidence_refs": refs,
            **evidence_groups(refs),
            "open_measurements": open_measurement,
            "claim_boundary": ("Evidence is limited to the named mechanism/workload and envelope; "
                               "the following measurements remain open: " + open_measurement),
            "entrypoint_audit": entrypoint_audit,
        })
    return {
        "schema_version": 1,
        "generated_from": "docs/research/engine_substrate/SUBSTRATE_CAPABILITY_MAP.md",
        "source_markdown_sha256": sha(MAP),
        "inventory_status": "initial_inventory_in_progress",
        "evidence_status_vocabulary": ["Implemented", "Mechanism tested", "Workload demonstrated",
                                       "Envelope measured", "Replicated / generalisation", "Partial",
                                       "unclassified"],
        "capabilities": entries,
    }


def validate(data: dict) -> list[str]:
    errors = []
    rows = table_rows(MAP.read_text())
    if len(rows) != len(data.get("capabilities", [])):
        errors.append(f"markdown/JSON row count differs: {len(rows)} != {len(data.get('capabilities', []))}")
    seen = set()
    for cap in data.get("capabilities", []):
        cid = cap.get("id")
        if not cid or cid in seen:
            errors.append(f"missing or duplicate capability id: {cid!r}")
        seen.add(cid)
        for field in ("implementation_surface", "ownership_and_path_shape", "evidence_status",
                      "evidence_summary", "evidence_refs", "open_measurements", "source_links",
                      "claim_boundary", "entrypoint_audit"):
            if field not in cap:
                errors.append(f"{cid}: missing {field}")
        for field in ("capability_area", "implementation_surface", "evidence_status",
                      "evidence_summary", "claim_boundary"):
            if not str(cap.get(field, "")).strip() or cap.get(field) == "unclassified":
                errors.append(f"{cid}: empty/unclassified {field}")
        for link in cap.get("source_links", []):
            if not link.get("resolved"):
                errors.append(f"{cid}: unresolved source {link.get('ref')}")
            elif link.get("symbol") and link.get("line") is None:
                errors.append(f"{cid}: unresolved callable anchor {link.get('ref')}")
        audit = cap.get("entrypoint_audit", {})
        if audit.get("status") == "pending":
            errors.append(f"{cid}: entrypoint/state-owner audit is still pending")
        if not audit.get("canonical_state_owner"):
            errors.append(f"{cid}: missing canonical state owner")
        if not audit.get("python_shadow_or_indexes"):
            errors.append(f"{cid}: missing host shadow/index ownership note")
        if not audit.get("normal_entrypoints"):
            errors.append(f"{cid}: missing callable entrypoint audit")
        for group in ("normal_entrypoints", "alternate_entrypoints"):
            for link in audit.get(group, []):
                if not link.get("resolved") or link.get("line") is None:
                    errors.append(f"{cid}: unresolved audited entrypoint {link.get('ref')}")
                if not link.get("activation"):
                    errors.append(f"{cid}: missing entrypoint activation/path status {link.get('ref')}")
        for ref in cap.get("evidence_refs", []):
            target = (MAP_DIR / ref).resolve()
            if not target.exists():
                errors.append(f"{cid}: missing evidence target {ref}")
        for item in cap.get("evidence_catalog", []):
            if not item.get("exists"):
                errors.append(f"{cid}: unresolved evidence catalog target {item.get('ref')}")
        for item in cap.get("runner_catalog", []):
            if not item.get("exists") or not str(item.get("path", "")).startswith("scripts/"):
                errors.append(f"{cid}: unresolved result-linked runner {item.get('ref')}")
        expected_tests = [item["ref"] for item in cap.get("evidence_catalog", [])
                          if item.get("category") == "test"]
        if cap.get("test_refs") != expected_tests:
            errors.append(f"{cid}: test_refs do not match the evidence catalog")
        expected_protocol_tests = [
            item["ref"] for item in cap.get("evidence_catalog", [])
            if item.get("category") == "evaluation_protocol_test"]
        if cap.get("evaluation_protocol_test_refs") != expected_protocol_tests:
            errors.append(
                f"{cid}: evaluation_protocol_test_refs do not match the evidence catalog")
        expected_status = (
            "linked_tests_present; coverage not audited" if expected_tests else
            "evaluation_protocol_only; functional coverage not audited"
            if expected_protocol_tests else "no_test_link_in_map")
        if cap.get("test_mapping_status") != expected_status:
            errors.append(f"{cid}: inaccurate or missing test mapping status")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="validate the committed JSON mirror without rewriting it")
    args = parser.parse_args()
    generated = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        if not OUT.exists():
            raise SystemExit(f"missing generated inventory: {OUT}")
        committed = json.loads(OUT.read_text())
        if committed != generated:
            raise SystemExit("capability_map.json is stale; regenerate it from the Markdown map")
    else:
        OUT.write_text(json.dumps(generated, indent=2, ensure_ascii=False) + "\n")
    errors = validate(generated)
    report = {"inventory_rows": len(generated["capabilities"]),
              "source_links": sum(len(c["source_links"]) for c in generated["capabilities"]),
              "linked_test_refs": sum(len(c["test_refs"]) for c in generated["capabilities"]),
              "result_linked_runners": sum(len(c["runner_catalog"]) for c in generated["capabilities"]),
              "rows_without_linked_tests": [c["id"] for c in generated["capabilities"]
                                             if not c["test_refs"]],
              "evidence_reference_counts": {
                  category: sum(item["category"] == category
                                for cap in generated["capabilities"]
                                for item in (cap["evidence_catalog"] + cap["runner_catalog"]))
                  for category in ("test", "result_document", "protocol_or_lock",
                                   "raw_or_analysis_record", "runner_or_analyzer",
                                   "supporting_reference")
              },
              "unresolved_source_links": [s["ref"] for c in generated["capabilities"]
                                          for s in c["source_links"] if not s["resolved"]],
              "missing_evidence": [e for e in errors if "missing evidence" in e],
              "validation_errors": errors,
              "json_sha256": sha(OUT)}
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
