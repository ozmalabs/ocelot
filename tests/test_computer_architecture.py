"""computer_architecture Mt + decomposition packs."""
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


def test_computer_architecture_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "computer_architecture"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_computer_architecture_carries_pipeline_concepts():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("instruction", "instruction_set_architecture",
                     "microarchitecture", "IPC_instructions_per_cycle",
                     "ILP_instruction_level_parallelism",
                     "pipelined_execution", "pipeline_depth",
                     "fetch_stage", "decode_stage", "execute_stage",
                     "memory_stage", "writeback_stage",
                     "superscalar", "out_of_order_execution",
                     "speculative_execution", "branch_prediction",
                     "register_renaming", "reorder_buffer",
                     "reservation_station", "microop",
                     "macro_op_fusion"):
        assert required in names, f"missing pipeline concept {required!r}"


def test_computer_architecture_carries_isa_families():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("RISC", "CISC", "x86_64", "AArch64",
                     "RISC_V", "POWER", "VLIW"):
        assert required in names


def test_computer_architecture_carries_memory_hierarchy():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("register_file", "L1_cache", "L2_cache",
                     "L3_cache", "DRAM", "HBM", "NVMe_SSD",
                     "cache_line", "cache_associativity",
                     "cache_coherence", "MESI", "false_sharing",
                     "prefetching"):
        assert required in names


def test_computer_architecture_carries_virtual_memory():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("TLB", "page", "page_table", "virtual_address",
                     "physical_address", "huge_page", "MMU", "IOMMU",
                     "page_fault", "copy_on_write", "mmap", "NUMA"):
        assert required in names


def test_computer_architecture_carries_memory_consistency():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("sequential_consistency", "total_store_order",
                     "weak_memory_model", "memory_barrier",
                     "atomic_operation", "compare_and_swap"):
        assert required in names


def test_computer_architecture_carries_dram_mechanics():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("DRAM_row", "DRAM_bank", "DRAM_refresh",
                     "row_hammer", "ECC_memory"):
        assert required in names


def test_computer_architecture_carries_memory_management():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("stack", "heap", "malloc", "jemalloc", "tcmalloc",
                     "garbage_collection", "generational_gc",
                     "concurrent_gc", "reference_counting"):
        assert required in names


def test_computer_architecture_carries_modern_microarchitectures():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Apple_M_series", "Intel_Golden_Cove",
                     "AMD_Zen_4", "AMD_Zen_5", "ARM_Neoverse",
                     "Tensor_Processing_Unit", "NPU_neural_processing_unit",
                     "GPU_streaming_multiprocessor"):
        assert required in names


def test_computer_architecture_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_architecture_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    ids = install_all_concept_expansions(s)
    for required in ("ooo_execution_decomposition",
                     "branch_prediction_decomposition",
                     "cache_coherence_decomposition",
                     "virtual_memory_decomposition",
                     "dram_operation_decomposition",
                     "memory_consistency_decomposition",
                     "allocator_decomposition",
                     "gpu_simt_decomposition",
                     "generational_gc_decomposition"):
        assert required in ids, f"arch pack {required!r} not loaded"


def test_architecture_pack_sub_mechanisms_mount():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # OoO pack
    for n in ("rename_stage", "physical_register_file",
              "register_alias_table", "common_data_bus",
              "memory_dependency_speculation", "store_buffer"):
        assert n in names
    # Branch prediction pack
    for n in ("branch_target_buffer", "TAGE_predictor",
              "perceptron_predictor", "return_address_stack"):
        assert n in names
    # Cache coherence pack
    for n in ("MESI_modified_state", "MESI_exclusive_state",
              "MOESI_owned_state", "MESIF_forwarder_state",
              "cache_invalidation", "read_for_ownership"):
        assert n in names
    # Virtual memory pack
    for n in ("address_split_VPN_offset", "TLB_associative_lookup",
              "PML4_top_level", "PCID_process_context_id",
              "huge_page_2MB"):
        assert n in names
    # DRAM operation pack
    for n in ("dram_cell_capacitor", "row_activation",
              "row_buffer", "row_hammer_attack",
              "memory_controller_scheduling"):
        assert n in names
    # Memory consistency pack
    for n in ("sequential_consistency_definition", "tso_total_store_order",
              "weak_ordering_arm_riscv", "acquire_semantics",
              "release_semantics", "relaxed_atomic"):
        assert n in names
    # Allocator pack
    for n in ("size_class_binning", "per_thread_arena",
              "slab_allocator", "buddy_allocator",
              "mmap_for_large_allocations"):
        assert n in names
    # GPU SIMT pack
    for n in ("warp_wavefront", "thread_block_cooperative",
              "branch_divergence", "occupancy_metric",
              "shared_memory_scratchpad", "memory_coalescing",
              "tensor_core_matrix_units"):
        assert n in names
    # GC pack
    for n in ("weak_generational_hypothesis", "eden_nursery_region",
              "survivor_space", "write_barrier", "card_table",
              "tenuring_threshold", "concurrent_marking"):
        assert n in names


def test_total_architecture_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "computer_architecture")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 200, f"only {n_concepts} concepts"
    assert n_rules >= 60, f"only {n_rules} rules"
