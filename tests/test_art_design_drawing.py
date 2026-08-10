"""art_design_drawing Mt."""
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


def test_art_installs():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "art_design_drawing"


def test_art_carries_drawing_color_composition():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("line_quality", "shape_form", "value_tonal_range",
                     "linear_perspective", "atmospheric_perspective",
                     "foreshortening", "gesture_drawing",
                     "color_wheel", "complementary_colors",
                     "analogous_colors", "color_temperature",
                     "saturation_chroma", "color_value_relationship",
                     "rule_of_thirds", "golden_ratio_composition",
                     "focal_point", "leading_lines", "balance_symmetry",
                     "negative_space"):
        assert required in names


def test_art_carries_anatomy_perception_media():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("human_proportions", "skeletal_landmarks",
                     "muscle_groups", "facial_proportions", "hands_feet",
                     "gestalt_principles", "figure_ground",
                     "optical_illusions", "pencil_graphite", "charcoal",
                     "ink_drawing", "watercolor", "oil_painting",
                     "acrylic_painting", "raster_image",
                     "vector_graphics", "layers_blend_modes",
                     "digital_brushes", "graphics_tablet"):
        assert required in names


def test_art_carries_3d_typography_design():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("3D_modeling_polygon", "subdivision_surfaces",
                     "sculpting_3D", "UV_mapping", "rigging_skeleton",
                     "PBR_materials", "type_anatomy", "serif_sans_serif",
                     "kerning_tracking_leading", "typographic_hierarchy",
                     "type_classification", "grid_systems",
                     "brand_identity", "design_principles",
                     "affordances_Norman", "Norman_seven_actions",
                     "Nielsen_heuristics", "WCAG_accessibility",
                     "design_thinking", "Fitts_law", "Hicks_law"):
        assert required in names


def test_art_carries_history_animation_film():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Renaissance_perspective", "Baroque", "Impressionism",
                     "Post_Impressionism", "Cubism", "Abstract_Expressionism",
                     "Pop_Art", "Bauhaus", "twelve_animation_principles",
                     "key_frames_inbetweens", "timing_spacing",
                     "cinematography_basics", "lighting_three_point",
                     "color_grading_film", "exposure_triangle",
                     "depth_of_field", "industrial_design_DFM",
                     "ergonomics_anthropometry", "modernist_architecture",
                     "vernacular_architecture", "sustainable_design",
                     "generative_art", "procedural_textures",
                     "AI_image_generation", "style_transfer"):
        assert required in names


def test_art_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_total_art_concept_count():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "art_design_drawing")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 90, f"only {n_concepts} concepts"
    assert n_rules >= 20, f"only {n_rules} rules"
