"""concept_expansions — discovery loader + decomposition packs.

Verifies the loader picks up every pack under seeds/expansions/,
each pack mounts sub-mechanisms under the right Mt with `decomposes`
edges to the parent concept, and the loader is idempotent."""
from __future__ import annotations

import json
from pathlib import Path

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
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def _install_video_theory(s):
    """Helper — install video_coding_theory Mt + concepts (the parent
    concepts that expansion packs will decompose)."""
    from substrate.boot_all import load_one_seed
    return load_one_seed(s, "video_coding_theory")


def test_expansions_directory_exists():
    """The mechanism's home — packs are JSON files dropped here."""
    expansions_dir = (Path(__file__).resolve().parent.parent
                      / "seeds" / "expansions")
    assert expansions_dir.exists()
    packs = list(expansions_dir.glob("*.json"))
    assert len(packs) >= 23, f"only {len(packs)} packs found in {expansions_dir}"


def test_all_codec_decomposition_packs_present():
    """The expert-level codec decomposition packs that comprise the
    substrate's video-coding depth. Each is one JSON file in the
    expansions directory; adding more is a file-drop, not a code edit."""
    expansions_dir = (Path(__file__).resolve().parent.parent
                      / "seeds" / "expansions")
    expected = (
        # Entropy coders
        "ms_ac_decomposition.json", "ans_decomposition.json",
        # In-loop filters
        "deblocking_filter_decomposition.json",
        "cdef_decomposition.json", "alf_decomposition.json",
        # Motion / prediction
        "motion_estimation_decomposition.json",
        "vvc_affine_motion_decomposition.json",
        "bdof_decomposition.json",
        # Transforms
        "integer_dct_decomposition.json",
        "vvc_mts_lfnst_decomposition.json",
        "hadamard_transform_decomposition.json",
        # Cross-component
        "cclm_decomposition.json",
        # Block structure
        "av1_partition_tree_decomposition.json",
        "hevc_intra_modes_decomposition.json",
        # Bitstream structure
        "nal_unit_decomposition.json",
        # Perceptual metrics
        "vmaf_internals_decomposition.json",
        "ssim_internals_decomposition.json",
        # Rate control + parallelism
        "rate_control_decomposition.json",
        "parallelism_decomposition.json",
        # Color / HDR
        "color_spaces_decomposition.json",
        "hdr_metadata_decomposition.json",
        # Neural codecs
        "dcvc_architecture_decomposition.json",
        "inr_codec_decomposition.json",
    )
    for fname in expected:
        assert (expansions_dir / fname).exists(), f"missing pack {fname!r}"


def test_install_all_packs_loads_every_file():
    """The discovery loader picks up every JSON file in the directory."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    _install_video_theory(s)
    pack_ids = install_all_concept_expansions(s)
    # 5 packs we wrote.
    assert len(pack_ids) >= 5
    for required in ("ms_ac_decomposition",
                     "ans_decomposition",
                     "deblocking_filter_decomposition",
                     "motion_estimation_decomposition",
                     "integer_dct_decomposition"):
        assert required in pack_ids, f"pack {required!r} not loaded"


def test_pack_sub_mechanisms_mount_under_target_mt():
    """Each pack's sub-mechanisms become has_concept children of the
    Mt named in the pack's `in_microtheory` field."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = _install_video_theory(s)
    install_all_concept_expansions(s)
    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    # MS-AC sub-mechanisms.
    for required in ("cumulative_distribution_function",
                     "single_CDF_lookup_per_symbol",
                     "recursive_averaging_update",
                     "byte_renormalisation"):
        assert required in concept_names
    # ANS sub-mechanisms.
    for required in ("state_integer_x", "tANS_table_based",
                     "reverse_order_encoding"):
        assert required in concept_names
    # Deblocking sub-mechanisms.
    for required in ("boundary_strength", "alpha_beta_thresholds",
                     "clip_to_neighbourhood"):
        assert required in concept_names
    # Motion estimation sub-mechanisms.
    for required in ("diamond_search", "hexagon_search", "EPZS",
                     "SATD_cost_function", "subpel_refinement"):
        assert required in concept_names
    # Integer DCT sub-mechanisms.
    for required in ("integer_basis_matrix", "separable_2d_transform",
                     "butterfly_decomposition", "IDCT_byte_exact"):
        assert required in concept_names


def test_sub_mechanisms_carry_decomposes_edge_to_parent():
    """Each pack's sub-mechanisms have a `decomposes` edge pointing at
    the parent concept (e.g. MS-AC sub-mechanisms decompose
    multi_symbol_arithmetic_coder)."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = _install_video_theory(s)
    install_all_concept_expansions(s)
    # Find the multi_symbol_arithmetic_coder concept.
    parent = None
    for c in s.neighbours(mt, "has_concept"):
        if s.node(c)["attrs"]["name"] == "multi_symbol_arithmetic_coder":
            parent = c
            break
    assert parent is not None
    # Find any MS-AC sub-mechanism and check it decomposes the parent.
    sub = None
    for c in s.neighbours(mt, "has_concept"):
        if s.node(c)["attrs"]["name"] == "single_CDF_lookup_per_symbol":
            sub = c
            break
    assert sub is not None
    decompose_targets = s.neighbours(sub, "decomposes")
    assert parent in decompose_targets


def test_derivation_rules_mount_with_soundness_category():
    """Each pack's rules become has_rule children of the target Mt and
    carry soundness_category linking to compiler_theory."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = _install_video_theory(s)
    install_all_concept_expansions(s)
    rules_by_name = {}
    for r in s.neighbours(mt, "has_rule"):
        rules_by_name[s.node(r)["attrs"]["name"]] = s.node(r)["attrs"]
    # A handful of pack-installed rules.
    for required in ("single_lookup_replaces_log_n_bins",
                     "ans_state_carries_information_about_message",
                     "boundary_strength_derives_filter_decisions",
                     "predictive_start_skips_most_of_search",
                     "byte_exact_inverse_required_for_decoder_consistency"):
        assert required in rules_by_name, f"missing rule {required!r}"
        # And each has a soundness_category from the standard set.
        cat = rules_by_name[required].get("soundness_category", "")
        assert cat in {
            "denotational_equivalence", "algebraic_law",
            "extensional_equivalence", "cost_equivalence",
            "referential_transparency", "ub_preservation",
        }, f"rule {required!r} has bad soundness_category {cat!r}"


def test_loader_is_idempotent():
    """Running install_all twice should leave node counts unchanged."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    _install_video_theory(s)
    install_all_concept_expansions(s)
    n_concepts_1 = len(s.nodes("Concept"))
    n_rules_1 = len(s.nodes("Rule"))
    install_all_concept_expansions(s)
    n_concepts_2 = len(s.nodes("Concept"))
    n_rules_2 = len(s.nodes("Rule"))
    assert n_concepts_1 == n_concepts_2
    assert n_rules_1 == n_rules_2


def test_pack_marks_origin_for_data_drivenness_scorer():
    """Each pack-installed sub-mechanism carries origin='concept_expansion'
    so the architecture cortex's data_drivenness scorer counts them as
    graph-data (via the dynamic_data_origin_prefixes whitelist)."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = _install_video_theory(s)
    install_all_concept_expansions(s)
    # Find a known expansion sub-mechanism.
    target = None
    for c in s.neighbours(mt, "has_concept"):
        if s.node(c)["attrs"]["name"] == "diamond_search":
            target = c
            break
    assert target is not None
    attrs = s.node(target)["attrs"]
    assert attrs["origin"] == "concept_expansion"
    assert attrs["expansion_pack"] == "motion_estimation_decomposition"


def test_install_single_pack_directly():
    """install_concept_expansion handles one specific pack file."""
    from domains.concept_expansions import install_concept_expansion
    s = _fresh_substrate()
    _install_video_theory(s)
    pack_path = (Path(__file__).resolve().parent.parent
                 / "seeds" / "expansions"
                 / "motion_estimation_decomposition.json")
    parent = install_concept_expansion(s, pack_path)
    assert parent is not None
    # The motion_estimation parent concept.
    attrs = s.node(parent)["attrs"]
    assert attrs["name"] == "motion_estimation"


def test_total_concept_count_with_expansions():
    """Sanity: the substrate now carries 117 base + ~240+ expansion-pack
    sub-mechanisms across 23 packs = 350+ concepts in video_coding_theory."""
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = _install_video_theory(s)
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 340, f"only {n_concepts} concepts"
    assert n_rules >= 130, f"only {n_rules} rules"


def test_packs_have_well_formed_shape():
    """Every pack file declares the required schema fields."""
    expansions_dir = (Path(__file__).resolve().parent.parent
                      / "seeds" / "expansions")
    for pack_path in expansions_dir.glob("*.json"):
        with pack_path.open() as f:
            pack = json.load(f)
        for required in ("id", "version", "expands_concept",
                         "in_microtheory", "description",
                         "sub_mechanisms", "derivation_rules"):
            assert required in pack, (
                f"{pack_path.name}: missing field {required!r}")
        # sub_mechanisms each have name + definition + why + category.
        for sm in pack["sub_mechanisms"]:
            for f in ("name", "definition", "why", "category"):
                assert f in sm, f"{pack_path.name} sub_mechanism {sm.get('name')!r} missing {f!r}"
