"""video_coding_theory — the WHY of H.264/H.265 as graph data.

Verifies the seed installs the Mt + Concepts + Rules and that the
'why' fields are reachable so the agent can answer codec-design
questions by graph query, not by Python lookup."""
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
    "subClassOf", "in_category",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def test_video_coding_theory_installs_mt_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "video_coding_theory"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_video_coding_theory_concepts_present_and_carry_why():
    """Each Concept carries a `why` field — the principle that makes
    the choice work. This is the graph-resident answer to 'why?'."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    # Foundational concepts the agent needs to derive WHY from.
    for required in ("information_content", "redundancy", "prediction",
                     "residual", "decorrelation", "quantisation",
                     "entropy_coding", "rate_distortion",
                     "intra_prediction", "inter_prediction",
                     "I_frame", "P_frame", "B_frame",
                     "macroblock", "coding_tree_unit",
                     "DCT", "CAVLC", "CABAC", "deblocking_filter",
                     "sample_adaptive_offset",
                     "H264", "H265"):
        assert required in concept_names, f"missing concept {required!r}"
    # Every concept has a non-empty `why` field.
    for c in s.neighbours(mt, "has_concept"):
        attrs = s.node(c)["attrs"]
        why = attrs.get("why", "")
        assert isinstance(why, str) and len(why) > 0, (
            f"concept {attrs['name']!r} missing 'why'")


def test_video_coding_theory_rules_present_with_derivations():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    rule_names = {s.node(r)["attrs"]["name"]
                  for r in s.neighbours(mt, "has_rule")}
    for required in ("redundancy_enables_compression",
                     "prediction_reduces_residual_magnitude",
                     "decorrelation_concentrates_energy",
                     "quantisation_introduces_distortion",
                     "larger_partitions_save_overhead",
                     "h265_dominates_h264_at_4k",
                     "encoder_decoder_asymmetry"):
        assert required in rule_names, f"missing rule {required!r}"


def test_video_coding_theory_av1_concepts_present():
    """AV1's distinctive tools should all be in the graph as concepts
    with WHY-fields explaining the design choice."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    for required in ("AV1", "superblock", "partition_tree_10_way",
                     "Paeth_predictor", "smooth_predictor",
                     "recursive_intra_filter", "chroma_from_luma",
                     "warped_motion", "global_motion", "OBMC",
                     "compound_prediction", "AV1_reference_frame_set",
                     "multi_symbol_arithmetic_coder",
                     "CDF_probability_table", "CDEF",
                     "loop_restoration_filter", "film_grain_synthesis"):
        assert required in concept_names, f"missing AV1 concept {required!r}"


def test_video_coding_theory_vvc_concepts_present():
    """VVC/H.266 tools each with their why."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    for required in ("VVC", "multi_type_tree", "affine_motion",
                     "sub_block_motion", "bidirectional_optical_flow",
                     "adaptive_loop_filter", "DST_7", "DCT_8",
                     "multiple_transform_selection", "LFNST"):
        assert required in concept_names, f"missing VVC concept {required!r}"


def test_video_coding_theory_vp9_present():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    assert "VP9" in concept_names
    assert "ADST" in concept_names


def test_video_coding_theory_neural_codec_family():
    """The DCVC family + INR-based codecs + diffusion-based codecs."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    for required in ("DCVC", "DCVC_DC", "DCVC_FM", "DCVC_RT",
                     "implicit_neural_representation", "HiNeRV",
                     "GIViC", "hybrid_neural_conventional_codec"):
        assert required in concept_names, f"missing neural codec {required!r}"


def test_video_coding_theory_perceptual_metrics():
    """PSNR / SSIM / MS-SSIM / VMAF / JND ladder."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    for required in ("PSNR", "SSIM", "MS_SSIM", "VMAF", "JND"):
        assert required in concept_names


def test_video_coding_theory_emerging_formats():
    """HDR variants + volumetric formats."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    for required in ("HDR10", "HDR10_plus", "Dolby_Vision",
                     "V_PCC", "G_PCC", "NeRF_compression"):
        assert required in concept_names


def test_video_coding_theory_codec_principles():
    """The cross-cutting meta-principles that shape codec design."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    for required in ("codec_generation_cadence",
                     "patent_landscape_drives_architecture",
                     "encoder_is_non_normative",
                     "hardware_lag_dictates_rollout",
                     "compounding_small_gains",
                     "metric_choice_is_silent_specification"):
        assert required in concept_names


def test_rules_carry_soundness_category_linking_to_compiler_theory():
    """Each rule now declares which compiler_theory category of
    equivalence it instantiates. This makes the cross-Mt linkage
    explicit + queryable, not just implicit."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    valid_categories = {
        "denotational_equivalence", "algebraic_law",
        "extensional_equivalence", "cost_equivalence",
        "referential_transparency", "ub_preservation",
    }
    n_with_category = 0
    for r in s.neighbours(mt, "has_rule"):
        attrs = s.node(r)["attrs"]
        if attrs.get("soundness_category") in valid_categories:
            n_with_category += 1
    # Vast majority of rules should now carry a soundness_category.
    assert n_with_category >= 20


def test_intra_modes_rule_carries_vision_crossover():
    """The intra_modes_expand_with_resolution rule is annotated with
    a vision_crossover field — explicit acknowledgement of the
    edge-density-scales-with-resolution insight."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    rule = None
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"]["name"] == "intra_modes_expand_with_resolution":
            rule = r
            break
    assert rule is not None
    attrs = s.node(rule)["attrs"]
    assert "vision_crossover" in attrs
    assert "edge" in attrs["vision_crossover"].lower()


def test_total_concept_and_rule_counts_for_expert_coverage():
    """An 'expert' Mt should carry breadth — verify the seed packs
    enough concepts + rules to count as comprehensive."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 75, f"only {n_concepts} concepts; expected ≥75"
    assert n_rules >= 20, f"only {n_rules} rules; expected ≥20"


def test_cabac_sub_mechanisms_all_present():
    """CABAC isn't just a named concept — it decomposes into 15 sub-
    mechanisms each with its own WHY. This is what 'understanding CABAC'
    looks like: the agent can name every piece + explain why each is
    there + how they compose."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    cabac_sub = ("arithmetic_coding", "range_coder",
                 "binarisation", "unary_binarisation",
                 "exp_golomb_binarisation", "context_index",
                 "context_state", "MPS_LPS", "probability_update",
                 "range_state", "renormalisation",
                 "carry_propagation", "bypass_mode",
                 "regular_mode", "termination_state")
    for required in cabac_sub:
        assert required in concept_names, f"missing CABAC sub-mechanism {required!r}"


def test_cabac_rules_derive_compression_from_first_principles():
    """The CABAC derivation rules form a chain:
       arithmetic coding → entropy bound
       binary alphabet → simple contexts
       context selection → lower conditional entropy
       adaptive state → tracks local statistics
       bypass → optimal for equiprobable
       renormalisation → commits bits
       carry propagation → streaming
       compounding → ~10-15% gain over CAVLC
    Each rule explains a piece of CABAC's compression story."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    rule_names = {s.node(r)["attrs"]["name"]
                  for r in s.neighbours(mt, "has_rule")}
    required = (
        "arithmetic_coding_approaches_entropy_bound",
        "binary_alphabet_simplifies_context_modeling",
        "context_selection_reduces_conditional_entropy",
        "adaptive_state_tracks_local_statistics",
        "bypass_doubles_speed_for_equiprobable_bins",
        "renormalisation_emits_when_committed",
        "carry_propagation_enables_streaming_arithmetic_coding",
        "cabac_efficiency_compounds_across_bins",
        "binarisation_method_matches_distribution",
    )
    for r in required:
        assert r in rule_names, f"missing CABAC rule {r!r}"


def test_cabac_mechanism_concepts_carry_real_explanation():
    """Each CABAC sub-mechanism concept's WHY field is substantive —
    explains the principle, not just 'because the standard says so'."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    sub_mechanisms = ("arithmetic_coding", "binarisation",
                      "context_index", "MPS_LPS",
                      "renormalisation", "carry_propagation",
                      "bypass_mode")
    for c in s.neighbours(mt, "has_concept"):
        attrs = s.node(c)["attrs"]
        if attrs["name"] not in sub_mechanisms:
            continue
        why = attrs.get("why", "")
        # WHY field should be a substantive explanation (≥150 chars).
        assert len(why) > 150, (
            f"concept {attrs['name']!r} has thin WHY ({len(why)} chars): "
            f"{why[:80]!r}…")
        # Should mention either a principle, a trade-off, or a mechanism.
        assert any(token in why.lower() for token in
                   ("shannon", "entropy", "probability", "bit", "stream",
                    "compress", "context", "interval", "narrow", "future",
                    "speculatively", "speed", "trade")), (
            f"concept {attrs['name']!r} WHY doesn't engage with the mechanism")


def test_total_concept_count_after_cabac_decomposition():
    """The seed now carries ≥115 concepts (102 base + 15 CABAC + buffer)."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 115, f"only {n_concepts} concepts"
    assert n_rules >= 33, f"only {n_rules} rules"


def test_why_h265_better_than_h264_derivable_by_graph_query():
    """Walk the graph to ANSWER 'why does H.265 outperform H.264 at 4K?'
    — read the h265_dominates_h264_at_4k Rule's why-field. The answer
    lives in graph data, not Python."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "video_coding_theory")
    # Locate the rule and read its why.
    rule_nid = None
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"]["name"] == "h265_dominates_h264_at_4k":
            rule_nid = r
            break
    assert rule_nid is not None
    why = s.node(rule_nid)["attrs"]["why"]
    # The answer mentions the key differentiators.
    assert "CTU" in why or "larger" in why.lower()
    assert "intra" in why.lower() or "modes" in why.lower()
    assert "CABAC" in why or "entropy" in why.lower()
