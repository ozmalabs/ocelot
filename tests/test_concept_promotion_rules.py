"""concept_promotion_rules — bootstrap walker promotes string-defined
Concepts whose definitions open with `<lhs> = <rhs>` to Term-tree
definitions, and the Shape harvester picks them up.

Locks the demonstrable principle: the substrate has Concept nodes with
prose definitions; the walker finds the equation-identity pattern,
promotes them to Eq(Lit(lhs), Lit(rhs)) Term-trees via
substrate.define_concept, and harvest_shape_donors enumerates them.

The walker is idempotent — a second run promotes nothing new.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from domains import concept_promotion_rules as cpr
from domains.harvester_shape import harvest_report_shape


# ---------------------------------------------------------------------------
# Pattern parse — pure function, no substrate needed.
# ---------------------------------------------------------------------------

def test_parse_simple_equation():
    # Newton's second law — the canonical example.
    assert cpr.parse_equation_identity("F = ma. Force equals mass times acceleration.") == ("F", "ma")


def test_parse_equation_with_greek_lhs():
    # The seed corpus uses Greek letters in lhs.
    assert cpr.parse_equation_identity("σ = My/I. Bending stress.") == ("σ", "My/I")


def test_parse_equation_with_phrase_lhs():
    # Multi-word lhs is allowed up to four words.
    parsed = cpr.parse_equation_identity("Stress σ = F/A. Force per area.")
    assert parsed == ("Stress σ", "F/A")


def test_parse_rejects_no_equation():
    assert cpr.parse_equation_identity("Patterned symbolic action. Turner's liminality.") is None


def test_parse_rejects_sentence_lhs():
    # A natural-language sentence is not an equation identity.
    assert cpr.parse_equation_identity("This is a definition that contains = somewhere") is None


def test_parse_empty_definition():
    assert cpr.parse_equation_identity("") is None


# ---------------------------------------------------------------------------
# Term composition — verifies the dict shape define_concept consumes.
# ---------------------------------------------------------------------------

def test_equation_term_shape():
    t = cpr.equation_term("F", "ma")
    assert t["type"] == "Eq"
    assert t["a"] == {"type": "Lit", "value": "F"}
    assert t["b"] == {"type": "Lit", "value": "ma"}


# ---------------------------------------------------------------------------
# End-to-end — the walker on a minimal synthetic substrate.
# ---------------------------------------------------------------------------

def _fresh_substrate_with_concepts(concepts: list[tuple[str, str]]):
    s = srs.Substrate()
    for name, defn in concepts:
        s._inner.add_node("Concept", {
            "name":       name,
            "definition": defn,
            "origin":     "test",
        })
    return s


def test_walker_promotes_matched_concepts():
    # Reset the module-level registry so tests don't bleed into each other.
    cpr.PROMOTED_CONCEPTS.clear()
    s = _fresh_substrate_with_concepts([
        ("newton_F", "F = ma. Force equals mass times acceleration."),
        ("ohm_V",    "V = IR. Voltage equals current times resistance."),
        ("prose",    "Patterned symbolic action. Not an equation."),
    ])
    report = cpr.install_concept_promotion_rules(s)
    assert report["n_walked"] == 3
    assert report["n_matched"] == 2
    assert report["n_promoted"] == 2
    assert report["n_failed"] == 0
    assert set(report["promoted"]) == {"newton_F", "ohm_V"}


def test_walker_is_idempotent():
    cpr.PROMOTED_CONCEPTS.clear()
    s = _fresh_substrate_with_concepts([
        ("newton_F", "F = ma. Force equals mass times acceleration."),
    ])
    cpr.install_concept_promotion_rules(s)
    report = cpr.install_concept_promotion_rules(s)
    # Second run sees the match again, but the registry de-dupes.
    assert report["n_matched"] == 1
    assert report["n_promoted"] == 0
    assert report["n_skipped"] == 1


def test_holds_dispatches_to_promoted_term_tree():
    # After promotion, Holds(concept, x) routes through the Eq Term-tree.
    # The seed Eq is a string-identity claim — Eq(Lit("F"), Lit("ma"))
    # — which evaluates to False (string comparison), not an error.
    # The point: the substrate's resolver acknowledges the concept.
    cpr.PROMOTED_CONCEPTS.clear()
    s = _fresh_substrate_with_concepts([
        ("newton_F", "F = ma. Force equals mass times acceleration."),
    ])
    cpr.install_concept_promotion_rules(s)
    out = s.evaluate(srs.Holds(concept="newton_F", node=srs.Lit(0)))
    # Eq("F", "ma") is False — strings differ — but dispatch succeeded.
    assert out is False


def test_harvester_picks_up_promoted_concepts():
    # The Shape harvester reads BOTH bootstrap + promoted registries.
    cpr.PROMOTED_CONCEPTS.clear()
    s = _fresh_substrate_with_concepts([
        ("newton_F", "F = ma."),
        ("ohm_V",    "V = IR."),
    ])
    before = harvest_report_shape(s._inner)
    cpr.install_concept_promotion_rules(s)
    after = harvest_report_shape(s._inner)
    # Two new donors, on top of the bootstrap baseline.
    assert after["n_donors"] - before["n_donors"] == 2
    # Post jabberwock-change-2: a flat Eq(Lit, Lit) walks at depth 1
    # (Eq bumps the syntactic axis once; the leaf Lits don't bump).
    # So promoted donors get Shape(none, 1, concrete) — distinct from
    # the depth-0 bare Lit baseline.
    assert ("none", 1, "concrete") in after["shape_distribution"]


# ---------------------------------------------------------------------------
# Pattern 2 — "X is the Y of Z" / "The Y of Z" / "A Y of Z" / bare.
# ---------------------------------------------------------------------------

def test_parse_is_the_of_the_form():
    # Definite-article form — the dominant shape in the corpus.
    assert cpr.parse_is_the_of(
        "The number of cycles per second. SI unit Hz."
    ) == ("number", "cycles per second")


def test_parse_is_the_of_a_form():
    assert cpr.parse_is_the_of(
        "A set of inputs processed together."
    ) == ("set", "inputs processed together")


def test_parse_is_the_of_bare_form():
    # No leading article, capitalised first word.
    assert cpr.parse_is_the_of(
        "Number of cycles per second. SI unit Hz."
    ) == ("Number", "cycles per second")


def test_parse_is_the_of_explicit_subject():
    # "X is the Y of Z" — rare in the corpus but supported.
    assert cpr.parse_is_the_of(
        "frequency is the rate of oscillation."
    ) == ("rate", "oscillation")


def test_parse_is_the_of_rejects_non_match():
    # Long subclauses without an "of" connector fall through.
    assert cpr.parse_is_the_of(
        "Defined by a list of axioms but not actually a Y of Z claim form."
    ) is None


def test_parse_is_the_of_rejects_equation():
    # An equation isn't this pattern.
    assert cpr.parse_is_the_of("F = ma. Newton's second law.") is None


def test_is_the_of_term_shape_with_z_concept():
    # When Z resolves to a Concept, the z half is Holds(z, x).
    t = cpr.is_the_of_term("firing_rate", "frequency",
                           "action potentials over time", None)
    # No z_concept provided → Lit fallback.
    assert t["type"] == "Eq"
    assert t["a"]["type"] == "Holds"
    assert t["a"]["concept"] == "firing_rate"
    assert t["b"]["type"] == "Attr"
    assert t["b"]["node"]["type"] == "Lit"
    assert t["b"]["key"] == "frequency"


def test_is_the_of_term_shape_with_z_holds():
    # When the caller passes a resolved Z concept, the z half is
    # Holds(Z, x) — the structurally richer form.
    t = cpr.is_the_of_term("pitch", "perceptual correlate",
                           "frequency", "frequency")
    assert t["b"]["node"]["type"] == "Holds"
    assert t["b"]["node"]["concept"] == "frequency"
    assert t["b"]["key"] == "perceptual_correlate"


def test_is_the_of_walker_promotes_clean_matches():
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        # Z resolves — also pre-existing concept "frequency"
        ("frequency", "Number of cycles per second."),
        ("pitch",     "Perceptual correlate of frequency."),
        # Z opaque — no concept named "rhythm_pattern"
        ("groove",    "The sustained urge of certain rhythm."),
        # Pattern 1 wins; this concept should be skipped.
        ("ohm_V",     "V = IR. Voltage."),
        # No match.
        ("prose",     "Patterned symbolic action. Turner's liminality."),
    ])
    # Run Pattern 1 first so "ohm_V" registers there.
    cpr.install_concept_promotion_rules(s)
    report = cpr.install_is_the_of_promotion(s)
    assert report["n_walked"] == 5
    # frequency, pitch, groove match; ohm_V skipped (eq won); prose
    # doesn't match.
    assert report["n_skipped_eq"] == 1
    assert report["n_promoted"] >= 3
    # pitch's Z resolves (frequency exists); groove's doesn't.
    assert report["n_z_resolved"] >= 1
    assert "pitch" in report["promoted"]


def test_is_the_of_walker_is_idempotent():
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("frequency", "Number of cycles per second."),
    ])
    cpr.install_is_the_of_promotion(s)
    report = cpr.install_is_the_of_promotion(s)
    # Second run sees the match again; the registry de-dupes.
    assert report["n_matched"] == 1
    assert report["n_promoted"] == 0
    assert report["n_skipped_dupe"] == 1


def test_z_resolves_via_last_word_singularised():
    # "languages" plural → singularise to "language". The new
    # resolver catches plural-Z cases that the old last-word-only
    # path missed.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("language",            "Symbolic communication system."),
        ("bilingual_acquisition", "Acquisition of two languages."),
    ])
    cpr.install_is_the_of_promotion(s)
    # bilingual_acquisition's Z phrase "two languages" should resolve
    # to the existing "language" Concept via singularisation, NOT a
    # Lit fallback.
    for nm, term in cpr.IS_THE_OF_PROMOTED:
        if nm == "bilingual_acquisition":
            assert term["b"]["node"]["type"] == "Holds"
            assert term["b"]["node"]["concept"] == "language"
            return
    assert False, "bilingual_acquisition was not promoted"


def test_z_resolves_via_first_word_singularised():
    # "comets ~2000-200" — head word "comets" with trailing number-junk;
    # the new resolver tries first-word singularisation as a backup
    # head-word fallback.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("comet",      "Icy body in the solar system."),
        ("oort_cloud", "Hypothesized spherical shell of comets ~2000-200 AU."),
    ])
    cpr.install_is_the_of_promotion(s)
    for nm, term in cpr.IS_THE_OF_PROMOTED:
        if nm == "oort_cloud":
            assert term["b"]["node"]["type"] == "Holds"
            assert term["b"]["node"]["concept"] == "comet"
            return
    assert False, "oort_cloud was not promoted"


def test_z_resolves_via_full_phrase_singularised():
    # "stellar masses" — full-phrase singularisation catches the
    # compound concept name "stellar_mass" when the bare last word
    # "mass" doesn't exist but the compound does.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("stellar_mass",          "The mass of a star."),
        ("stellar_mass_function", "Distribution of stellar masses."),
    ])
    cpr.install_is_the_of_promotion(s)
    for nm, term in cpr.IS_THE_OF_PROMOTED:
        if nm == "stellar_mass_function":
            assert term["b"]["node"]["type"] == "Holds"
            assert term["b"]["node"]["concept"] == "stellar_mass"
            return
    assert False, "stellar_mass_function was not promoted"


def test_z_resolves_via_trailing_ngram():
    # "plasma sustaining nuclear fusion" — neither the full phrase
    # nor any single head-word match a Concept, but the trailing
    # bigram "nuclear fusion" does. The N-gram strategy catches this.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("nuclear_fusion", "Energy-releasing nuclear reaction."),
        ("star",           "Self-gravitating ball of plasma sustaining nuclear fusion."),
    ])
    cpr.install_is_the_of_promotion(s)
    for nm, term in cpr.IS_THE_OF_PROMOTED:
        if nm == "star":
            assert term["b"]["node"]["type"] == "Holds"
            assert term["b"]["node"]["concept"] == "nuclear_fusion"
            return
    assert False, "star was not promoted"


def test_z_resolver_prefers_full_match_over_singular():
    # When both the full slug AND a singularised tail would match,
    # the full slug wins — the resolver is priority-ordered.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        # Both available — full slug "cycles_per_second" and singular "cycle".
        ("cycle",              "A periodic repetition."),
        ("cycles_per_second",  "SI unit of frequency."),
        ("frequency_demo",     "Number of cycles per second."),
    ])
    cpr.install_is_the_of_promotion(s)
    for nm, term in cpr.IS_THE_OF_PROMOTED:
        if nm == "frequency_demo":
            assert term["b"]["node"]["type"] == "Holds"
            # Full-phrase match wins over partial singular.
            assert term["b"]["node"]["concept"] == "cycles_per_second"
            return
    assert False, "frequency_demo was not promoted"


def test_singularize_unit():
    # _singularize is the cheap heuristic that drives the plural-Z
    # resolution path. Lock the cases that matter.
    assert cpr._singularize("languages") == "language"
    assert cpr._singularize("galaxies") == "galaxy"
    assert cpr._singularize("comets") == "comet"
    # -ss endings are NOT plural — left alone.
    assert cpr._singularize("mass") == "mass"
    # Short words are NOT mangled — "is" should stay "is".
    assert cpr._singularize("is") == "is"


# ---------------------------------------------------------------------------
# Pattern 3 — "X when Y" / "X if Y" CONDITIONAL.
# ---------------------------------------------------------------------------

def test_parse_conditional_when_form():
    # The dominant corpus shape — short X, short Y, sentence-local.
    assert cpr.parse_conditional(
        "Reduces gain when signal exceeds threshold."
    ) == ("Reduces gain", "signal exceeds threshold")


def test_parse_conditional_if_form():
    # The 'if' keyword variant.
    assert cpr.parse_conditional(
        "Optimal if heuristic is admissible.", keyword="if"
    ) == ("Optimal", "heuristic is admissible")


def test_parse_conditional_rejects_multi_clause():
    # Multi-clause sentences (comma in either half) fall through.
    assert cpr.parse_conditional(
        "Distortion caused, when sampled below Nyquist, "
        "appears as low frequencies."
    ) is None


def test_parse_conditional_rejects_no_keyword():
    assert cpr.parse_conditional(
        "Newton's second law. F equals ma."
    ) is None


def test_parse_conditional_uses_local_sentence():
    # Long preamble that doesn't contain 'when' is skipped; the walker
    # only reads the sentence with the keyword.
    parsed = cpr.parse_conditional(
        "Spill to stack. Performance critical case if no register available."
    , keyword="if")
    # The 'if' sentence is "Performance critical case if no register available".
    assert parsed == ("Performance critical case", "no register available")


def test_conditional_term_shape_with_lit_y():
    # Y unresolved → Holds(<slug(y)>, x) cond; concept-name Holds in then.
    t = cpr.conditional_term("compression_audio", "signal exceeds threshold",
                              None)
    assert t["type"] == "IfThenElse"
    assert t["cond"]["type"] == "Holds"
    assert t["cond"]["concept"] == "signal_exceeds_threshold"
    assert t["then"]["type"] == "Holds"
    assert t["then"]["concept"] == "compression_audio"
    assert t["other"]["type"] == "Lit"
    assert t["other"]["value"] is None


def test_conditional_term_shape_with_resolved_y():
    # Y resolved to a Concept → cond uses that concept name directly.
    t = cpr.conditional_term("compression_audio", "signal exceeds threshold",
                              "signal")
    assert t["cond"]["concept"] == "signal"


def test_conditional_walker_promotes_clean_matches():
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    cpr.CONDITIONAL_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        # Y resolves to existing "signal" concept.
        ("signal",            "A varying physical quantity."),
        ("compression_audio", "Reduces gain when signal exceeds threshold."),
        # Y opaque — no concept named "heuristic".
        ("a_star",            "Optimal if heuristic is admissible."),
        # Pattern 1 wins; this concept should be skipped from conditional.
        ("ohm_V",             "V = IR when nothing relevant. Voltage."),
        # No conditional pattern.
        ("prose",             "Patterned symbolic action. Turner's liminality."),
    ])
    cpr.install_concept_promotion_rules(s)  # Pattern 1 runs first.
    report = cpr.install_conditional_promotion(s)
    assert report["n_walked"] == 5
    # ohm_V skipped (eq won); compression_audio + a_star matched; prose skipped.
    # signal definition has no 'when'/'if' so falls through.
    assert report["n_skipped_eq"] == 1
    assert report["n_promoted"] >= 2
    # compression_audio's Y resolves to existing "signal" concept.
    assert report["n_y_resolved"] >= 1
    assert "compression_audio" in report["promoted"]
    assert "a_star" in report["promoted"]


def test_conditional_walker_is_idempotent():
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    cpr.CONDITIONAL_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("a_star", "Optimal if heuristic is admissible."),
    ])
    cpr.install_conditional_promotion(s)
    report = cpr.install_conditional_promotion(s)
    # Second run sees the match again; the registry de-dupes.
    assert report["n_matched"] == 1
    assert report["n_promoted"] == 0
    assert report["n_skipped_dupe"] == 1


def test_conditional_harvester_picks_up_ifthenelse_donors():
    # After Pattern 3 promotion, the harvester sees IfThenElse-bearing
    # donors — a Term variant NEITHER Pattern 1 nor Pattern 2 produces.
    # This is the structural diversification the conditional pattern
    # contributes.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    cpr.CONDITIONAL_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("a_star", "Optimal if heuristic is admissible."),
        ("comp",   "Reduces gain when signal exceeds threshold."),
    ])
    before = harvest_report_shape(s._inner)
    cpr.install_conditional_promotion(s)
    after = harvest_report_shape(s._inner)
    assert after["n_donors"] - before["n_donors"] >= 2
    # At least one promoted donor's term_json should be an IfThenElse.
    donors = after["donors"]
    ifthen_donors = [d for d in donors
                     if d["term_json"].get("type") == "IfThenElse"]
    assert len(ifthen_donors) >= 2, \
        "Pattern 3 should register IfThenElse-headed donors"


def test_conditional_lookup_postulate_term():
    # `lookup_postulate_term` should find CONDITIONAL_PROMOTED entries.
    from domains.harvester_shape import lookup_postulate_term
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    cpr.CONDITIONAL_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("a_star", "Optimal if heuristic is admissible."),
    ])
    cpr.install_conditional_promotion(s)
    term = lookup_postulate_term("a_star")
    assert term is not None
    assert term["type"] == "IfThenElse"


def test_is_the_of_harvester_picks_up_attr_donors():
    # After Pattern 2, the harvester sees Attr-bearing donors with a
    # DIFFERENT Shape than Pattern 1's flat Eq(Lit, Lit) — order_n
    # differs because Attr is a deeper recursion than bare Lit.
    cpr.PROMOTED_CONCEPTS.clear()
    cpr.IS_THE_OF_PROMOTED.clear()
    s = _fresh_substrate_with_concepts([
        ("frequency", "Number of cycles per second."),
        ("pitch",     "Perceptual correlate of frequency."),
    ])
    before = harvest_report_shape(s._inner)
    cpr.install_is_the_of_promotion(s)
    after = harvest_report_shape(s._inner)
    # Two new donors.
    assert after["n_donors"] - before["n_donors"] >= 2
    # The Attr-bearing donor has a non-{none,1,concrete} Shape
    # (Attr deepens the order_n axis past the equation form's depth-1).
    new_shapes = set(after["shape_distribution"].keys()) - set(before["shape_distribution"].keys())
    assert new_shapes, "Pattern 2 should introduce at least one new Shape axis"
