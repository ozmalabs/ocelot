"""compilers Mt + 9 decomposition packs."""
from __future__ import annotations

import pytest
from substrate_rs import _native


_NODE_TYPES = (
    "Microtheory", "Concept", "Rule",
    "DesignPattern", "ProgrammingLanguage", "CodeTarget",
    "DesignExclusion", "LanguageExclusion", "LanguageScoringConfig",
    "CodeWritingCortex", "CodeAuthoringRoot", "Reflex",
    "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "has_rule", "owns_microtheory",
    "owns_root", "has_reflex", "current_target", "has_draft",
    "validated_by", "installed_as", "authored_in", "uses_pattern",
    "subClassOf", "in_category", "decomposes",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et, "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def test_compilers_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "compilers"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_compilers_carries_frontend():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("lexer", "regular_language", "finite_automaton",
                     "longest_match_rule", "parser",
                     "context_free_grammar", "AST_abstract_syntax_tree",
                     "recursive_descent_parser", "LL_parsing",
                     "LR_parsing", "shift_reduce_conflict",
                     "PEG_parser", "packrat_parsing", "error_recovery",
                     "type_checking", "type_inference", "hindley_milner",
                     "unification", "subtyping"):
        assert required in names, f"missing frontend {required!r}"


def test_compilers_carries_midend_advanced():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("function_inlining", "loop_invariant_code_motion",
                     "loop_unrolling", "loop_vectorisation",
                     "alias_analysis", "andersen_alias_analysis",
                     "steensgaard_alias_analysis", "escape_analysis",
                     "tail_call_optimisation", "ssa_form",
                     "intermediate_representation",
                     "three_address_code", "control_flow_graph",
                     "dataflow_analysis", "dominator_tree", "phi_node",
                     "abstract_interpretation", "polyhedral_optimisation"):
        assert required in names, f"missing midend {required!r}"


def test_compilers_carries_backend():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("register_allocation", "graph_coloring_RA",
                     "linear_scan_RA", "greedy_RA",
                     "instruction_selection", "burs_bottom_up_rewriting",
                     "instruction_scheduling", "list_scheduling",
                     "software_pipelining", "LLVM_IR_to_assembly",
                     "stack_frame", "calling_convention",
                     "ABI_application_binary_interface",
                     "code_generation"):
        assert required in names, f"missing backend {required!r}"


def test_compilers_carries_jit():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("JIT_just_in_time", "method_JIT", "tracing_JIT",
                     "tiered_compilation", "OSR_on_stack_replacement",
                     "deoptimisation", "inline_cache", "hidden_class",
                     "profile_guided_optimisation",
                     "speculative_optimisation",
                     "ahead_of_time_compilation"):
        assert required in names


def test_compilers_carries_modern_infrastructure():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("MLIR", "MLIR_dialect", "Clang_frontend",
                     "GCC_GIMPLE", "Rust_MIR", "WebAssembly",
                     "GraalVM", "compiler_explorer"):
        assert required in names


def test_compilers_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_compiler_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "compilers")
    ids = install_all_concept_expansions(s)
    for required in ("parser_theory_decomposition",
                     "type_inference_decomposition",
                     "register_allocation_decomposition",
                     "instruction_selection_decomposition",
                     "loop_optimisation_decomposition",
                     "tracing_jit_decomposition",
                     "tiered_jit_decomposition",
                     "mlir_decomposition",
                     "dataflow_analysis_decomposition"):
        assert required in ids, f"compiler pack {required!r} not loaded"


def test_compiler_pack_sub_mechanisms_mount():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # Parser pack
    for n in ("FIRST_set", "FOLLOW_set", "LL1_parsing_table",
              "left_recursion_elimination", "left_factoring",
              "LR_item", "LR0_automaton", "SLR_LALR_LR1",
              "GLR_parser", "operator_precedence_parsing",
              "pratt_parser", "error_synchronisation"):
        assert n in names
    # Type inference pack
    for n in ("type_variable", "constraint_generation",
              "substitution", "occurs_check", "let_generalisation",
              "instantiation", "principal_type", "type_classes",
              "rank_N_polymorphism", "bidirectional_type_checking",
              "value_restriction", "row_polymorphism"):
        assert n in names
    # Register allocation pack
    for n in ("liveness_analysis", "interference_graph",
              "Chaitin_Briggs_algorithm", "spill_cost",
              "live_range_splitting", "coalescing",
              "iterated_register_coalescing",
              "linear_scan_algorithm", "LLVM_Greedy_allocator",
              "SSA_based_RA", "caller_callee_saved_registers",
              "register_pressure"):
        assert n in names
    # Instruction selection pack
    for n in ("instruction_pattern", "tree_pattern_matching",
              "DAG_pattern_matching", "BURS",
              "LLVM_SelectionDAG", "LLVM_GlobalISel",
              "peephole_optimisation", "TableGen",
              "addressing_mode_matching", "instruction_legalisation"):
        assert n in names
    # Loop optimisation pack
    for n in ("loop_invariant_detection", "induction_variable",
              "scalar_evolution_analysis", "loop_unrolling_factor",
              "loop_vectoriser", "SLP_vectoriser",
              "induction_variable_elimination", "loop_interchange",
              "loop_tiling", "loop_fusion", "loop_fission",
              "polyhedral_compilation"):
        assert n in names
    # Tracing JIT pack
    for n in ("trace_recording", "trace_anchor", "guard",
              "side_exit", "trace_compilation",
              "trace_specialisation", "trace_stitching",
              "trace_explosion", "LuaJIT_design",
              "PyPy_meta_tracing"):
        assert n in names
    # Tiered JIT pack
    for n in ("interpreter_tier", "baseline_JIT_tier",
              "optimising_JIT_tier", "tier_promotion_counter",
              "OSR_on_stack_replacement", "OSR_entry_point",
              "deoptimisation", "speculative_inlining",
              "code_cache", "JVM_HotSpot_tiered", "V8_tiered"):
        assert n in names
    # MLIR pack
    for n in ("MLIR_operation", "MLIR_dialect", "MLIR_type_system",
              "MLIR_attribute", "MLIR_region_block",
              "progressive_lowering", "linalg_dialect",
              "affine_dialect", "scf_dialect",
              "MLIR_pass_infrastructure",
              "MLIR_dialect_conversion"):
        assert n in names
    # Dataflow pack
    for n in ("lattice", "transfer_function", "meet_operator",
              "may_analysis", "must_analysis", "forward_analysis",
              "backward_analysis", "iterative_fixed_point",
              "monotone_framework", "reaching_definitions",
              "live_variable_analysis", "available_expressions"):
        assert n in names


def test_total_compiler_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "compilers")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 175, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"
