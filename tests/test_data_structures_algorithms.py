"""data_structures_algorithms Mt + 10 decomposition packs."""
from __future__ import annotations

import pytest
from substrate_rs import _native
from substrate.boot_all import load_one_seed


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


def test_dsa_installs_with_genlmt():
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "data_structures_algorithms"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_dsa_carries_complexity_foundations():
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("big_O_notation", "big_Theta_notation",
                     "big_Omega_notation", "time_complexity",
                     "space_complexity", "amortised_analysis",
                     "worst_case", "average_case", "best_case",
                     "P_class", "NP_class", "NP_complete",
                     "load_factor", "amortised_doubling",
                     "loop_invariant"):
        assert required in names, f"missing complexity concept {required!r}"


def test_dsa_carries_data_structures():
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("array", "dynamic_array", "linked_list", "stack",
                     "queue", "deque", "hash_table", "hash_function",
                     "set", "tree_general", "binary_tree",
                     "binary_search_tree", "self_balancing_BST",
                     "AVL_tree", "red_black_tree", "B_tree",
                     "B_plus_tree", "trie", "binary_heap",
                     "priority_queue", "graph", "adjacency_list",
                     "adjacency_matrix", "disjoint_set", "bloom_filter",
                     "skip_list", "LRU_cache", "segment_tree",
                     "fenwick_tree", "tree_rotation"):
        assert required in names, f"missing data structure {required!r}"


def test_dsa_carries_algorithms():
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("linear_search", "binary_search",
                     "bubble_sort", "insertion_sort", "merge_sort",
                     "quick_sort", "heap_sort", "radix_sort",
                     "TimSort", "introsort",
                     "BFS", "DFS", "Dijkstra_algorithm",
                     "Bellman_Ford", "Floyd_Warshall", "A_star_search",
                     "topological_sort", "MST_minimum_spanning_tree",
                     "SCC_strongly_connected_components",
                     "max_flow_min_cut",
                     "KMP_string_matching", "Rabin_Karp_string_matching",
                     "Boyer_Moore_string_matching", "Aho_Corasick"):
        assert required in names, f"missing algorithm {required!r}"


def test_dsa_carries_dp_and_paradigms():
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("dynamic_programming", "memoisation", "tabulation",
                     "longest_common_subsequence", "edit_distance",
                     "knapsack_problem", "greedy_paradigm",
                     "divide_and_conquer", "backtracking",
                     "branch_and_bound", "recursion", "tail_recursion",
                     "tree_traversal", "iterator", "generator",
                     "randomised_algorithm"):
        assert required in names


def test_dsa_rules_carry_soundness_category():
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_dsa_decomposition_packs_load():
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "data_structures_algorithms")
    ids = install_all_concept_expansions(s)
    for required in ("hash_table_decomposition",
                     "self_balancing_bst_decomposition",
                     "b_tree_decomposition",
                     "heap_priority_queue_decomposition",
                     "graph_algorithms_decomposition",
                     "sorting_algorithms_decomposition",
                     "dynamic_programming_decomposition",
                     "union_find_decomposition",
                     "trie_suffix_decomposition",
                     "complexity_theory_decomposition"):
        assert required in ids, f"DSA pack {required!r} not loaded"


def test_dsa_pack_sub_mechanisms_mount():
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # Hash table pack
    for n in ("separate_chaining", "open_addressing",
              "linear_probing", "quadratic_probing",
              "double_hashing", "robin_hood_hashing",
              "cuckoo_hashing", "swisstable_hashing",
              "tombstone_deletion", "resize_doubling",
              "hash_flooding_attack"):
        assert n in names
    # Self-balancing BST pack
    for n in ("BST_property", "left_rotation", "right_rotation",
              "AVL_balance_factor", "AVL_rebalance",
              "red_black_coloring", "red_black_insert_fixup",
              "splay_tree", "treap", "successor_predecessor"):
        assert n in names
    # B-tree pack
    for n in ("node_with_M_minus_1_keys", "internal_vs_leaf_nodes",
              "search_logarithmic_in_M", "split_on_overflow",
              "merge_on_underflow", "B_plus_leaf_linked_list",
              "B_plus_internal_only_keys", "page_caching",
              "write_amplification", "concurrent_B_tree_locking"):
        assert n in names
    # Heap pack
    for n in ("heap_property", "array_layout", "sift_up",
              "sift_down", "build_heap_bottom_up", "heapsort_use",
              "d_ary_heap", "fibonacci_heap", "pairing_heap",
              "heap_decrease_key"):
        assert n in names
    # Graph algorithms pack
    for n in ("BFS_via_queue", "DFS_via_stack_or_recursion",
              "Dijkstra_relaxation", "Dijkstra_priority_queue",
              "Bellman_Ford_relaxation_rounds", "Floyd_Warshall_DP",
              "Prim_MST_greedy", "Kruskal_MST_union_find",
              "Tarjan_SCC_with_low_link",
              "topological_sort_via_DFS_post_order"):
        assert n in names
    # Sorting pack
    for n in ("comparison_count_lower_bound", "quicksort_partition",
              "pivot_selection_strategy", "mergesort_merge",
              "mergesort_stable", "timsort_run_detection",
              "introsort_depth_limit", "radix_sort_LSB"):
        assert n in names
    # DP pack
    for n in ("optimal_substructure", "overlapping_subproblems",
              "memoisation_top_down", "tabulation_bottom_up",
              "DP_state_definition", "DP_recurrence",
              "rolling_array_space_optimisation",
              "knapsack_01_DP", "interval_DP", "bitmask_DP"):
        assert n in names
    # Union-find pack
    for n in ("parent_array_representation", "find_operation",
              "union_operation", "path_compression",
              "union_by_rank", "amortised_inverse_ackermann",
              "Kruskal_use_case"):
        assert n in names
    # Trie/suffix pack
    for n in ("trie_per_character_edge", "trie_end_of_word_marker",
              "compressed_trie_radix", "patricia_trie",
              "aho_corasick_automaton", "aho_corasick_failure_links",
              "suffix_tree", "suffix_array",
              "longest_common_prefix_LCP_array"):
        assert n in names
    # Complexity theory pack
    for n in ("P_polynomial_time", "NP_polynomial_verifiable",
              "polynomial_reduction", "NP_complete_definition",
              "Cook_Levin_theorem", "3_SAT_NP_complete",
              "NP_hard_definition", "coNP_class", "PSPACE_class",
              "approximation_algorithm", "FPT_fixed_parameter_tractable"):
        assert n in names


def test_total_dsa_concept_count():
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "data_structures_algorithms")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 195, f"only {n_concepts} concepts"
    assert n_rules >= 65, f"only {n_rules} rules"
