"""ArchitectureCortex — the agent assessing its own shape.

Same shape verifications as for code-writing: the data (qualities,
smells) is graph-resident, the cortex's reasoning is graph queries,
the output (Assessment + QualityScore + SmellInstance) is graph data
that downstream cortices can read.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native


_NODE_TYPES = (
    "ArchitectureCortex", "CodeWritingCortex", "SpeechCortex",
    "ArchitecturalQuality", "ArchitecturalSmell",
    "Assessment", "QualityScore", "SmellInstance",
    "Microtheory", "Concept", "Reflex",
    "CodeAuthoringRoot", "ReplacementTarget", "CodeDraft",
    "ValidationResult", "CodeInstallation", "DesignPattern",
    "ProgrammingLanguage", "CodeTarget", "DesignExclusion",
    "LanguageExclusion", "LanguageScoringConfig",
)
_EDGE_TYPES = (
    "owns_microtheory", "owns_root", "has_reflex",
    "assesses", "produced", "scored_on", "detected_smell",
    "for_quality", "for_smell", "genlMt", "in_category",
    "subClassOf", "current_target", "has_draft", "validated_by",
    "installed_as", "authored_in", "uses_pattern", "lexicon",
    "has_concept",
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
    return s


def test_install_creates_cortex_and_quality_nodes():
    from domains.architecture_cortex import ArchitectureCortex
    s = _fresh_substrate()
    cortex = ArchitectureCortex(s).install()
    assert cortex.cortex_nid is not None
    # Qualities + smells installed from the seed.
    assert len(s.nodes("ArchitecturalQuality")) >= 5
    assert len(s.nodes("ArchitecturalSmell")) >= 5
    # Mt installed with parent inheritance.
    arch_mt = next(n for n in s.nodes("Microtheory")
                   if s.node(n)["attrs"]["name"] == "architecture_assessment")
    # The Mt has genlMt parents (if compiler_theory/design_patterns exist).
    assert arch_mt is not None


def test_qualities_and_smells_are_graph_native():
    """All assessment vocabulary lives in the graph — no Python dicts.
    Adding an `ArchitecturalQuality` at runtime should be visible to
    the scorer (it just won't have a scorer function for an
    unrecognised name, but the GRAPH side is fully extensible)."""
    from domains.architecture_cortex import ArchitectureCortex
    s = _fresh_substrate()
    ArchitectureCortex(s).install()

    s.add_node("ArchitecturalQuality", {
        "name": "synthetic_quality",
        "definition": "test-only",
        "max_score": 10,
        "origin": "test",
    })
    qualities = {s.node(n)["attrs"]["name"]
                 for n in s.nodes("ArchitecturalQuality")}
    assert "synthetic_quality" in qualities


def test_assess_emits_assessment_with_quality_scores():
    """Assessing the cortex itself emits an Assessment node + a
    QualityScore for every installed quality + 'scored_on' edges."""
    from domains.architecture_cortex import ArchitectureCortex
    s = _fresh_substrate()
    cortex = ArchitectureCortex(s).install()

    assessment = cortex.assess(cortex.cortex_nid)
    assert s.has_node(assessment)
    n_qualities = len(s.nodes("ArchitecturalQuality"))
    scored = s.neighbours(assessment, "scored_on")
    assert len(scored) == n_qualities
    for qs in scored:
        attrs = s.node(qs)["attrs"]
        assert "score" in attrs
        assert 0 <= attrs["score"] <= attrs["max_score"]
        assert attrs["rationale"]


def test_assess_links_quality_score_back_to_quality_node():
    """QualityScore.for_quality → ArchitecturalQuality. The agent can
    walk back from a score to the quality definition that produced
    it — graph-native traceability."""
    from domains.architecture_cortex import ArchitectureCortex
    s = _fresh_substrate()
    cortex = ArchitectureCortex(s).install()
    assessment = cortex.assess(cortex.cortex_nid)
    for qs in s.neighbours(assessment, "scored_on"):
        backrefs = s.neighbours(qs, "for_quality")
        assert len(backrefs) == 1
        assert s.node(backrefs[0])["type"] == "ArchitecturalQuality"


def test_render_assessment_reads_from_graph():
    """Output formatting reads attrs from graph nodes — no Python
    state. Lines should include the qualities' names + scores."""
    from domains.architecture_cortex import ArchitectureCortex
    s = _fresh_substrate()
    cortex = ArchitectureCortex(s).install()
    assessment = cortex.assess(cortex.cortex_nid)
    text = cortex.render_assessment(assessment)
    assert "Architecture Assessment" in text
    assert "data_drivenness" in text
    assert "introspectability" in text
