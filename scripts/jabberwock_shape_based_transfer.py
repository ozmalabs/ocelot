"""jabberwock_shape_based_transfer — iter-22: SHAPE-BASED (structural) transfer of
the agent's self-acquired re_represent shape onto the perceptual frame.

THE SITUATION (iter-21, commit aad5d9d6). The agent self-acquired the re_represent
shape (rule_derived__characterize_by_invariant_relations_among_parts, from invariant
theory / Erlangen, domains/invariant_representation.py). breadth-audit confirms
re_represent=1. But synthesize_gaps over the perceptual frame
(surface_feature_representation_frame) does NOT fire it, because transfer is LEXICAL
(match_mode='all' — a CONJUNCTION of the shape antecedent's content words): the
frame states the same proposition in DIFFERENT VOCABULARY than the shape's
transformation-group structure, so the word-conjunction never co-occurs.

THE FIX (this script). STRUCTURAL transfer via the codebase's existing
match_mode='shape' / shapes_compatible (runners/dsl/src/shape.rs) — match by
Term-tree SHAPE (recursion / order_n / abstraction), not words.

NO-DONKEY. The Term-tree expressions of the shape antecedent and the frame
antecedent are derived FAITHFULLY from the structure each ALREADY states in its
existing text (domains/invariant_representation.py rule if-clauses; the honest
surface_feature_representation_frame text used in iter-19/21). They are NOT rigged
to be identical — each is built independently from its own clauses. The agent's own
shape_of_term walker classifies each; shapes_compatible decides; both Term-trees are
reported VERBATIM so faithfulness can be audited. This script does NOT author the
relational representation; whatever synthesize_gaps surfaces is the agent's.

Run:  python scripts/jabberwock_shape_based_transfer.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_development import install_speech_development
from domains.speech_cortex import SpeechCortex
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.invariant_representation import install_invariant_representation_seed
from domains.code_authoring import _install_concept
from domains import breadth_audit
from domains import harvester_shape
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps


# The HONEST frame text (verbatim from iter-19/21 — surface_feature_representation_frame).
_FRAME_TEXT = (
    "Speech recognition represents each unit by its SURFACE acoustic features "
    "— the per-frame gammatone / cepstral VALUES measured directly off the "
    "waveform — and matches those raw feature values against stored exemplars, "
    "voting for the nearest. These surface VALUES depend on the speaker and the "
    "accent: a change of talker or accent SHIFTS and SCALES the measured "
    "feature values even when the spoken word is the same. The values vary with "
    "the talker; they are NON-INVARIANT to the speaker. With correct word "
    "boundaries this surface representation still CONFUSES instances of the "
    "same word spoken by different talkers, because the raw values it compares "
    "are not the same across talkers.")


# ---------------------------------------------------------------------------
# Step 2 — FAITHFUL Term-trees, each derived from its OWN existing text.
# ---------------------------------------------------------------------------
#
# JSON Term-tree helpers (the encoding term_from_json / shape_of_term expects).
def _var(n):
    return {"type": "Var", "name": n}


def _holds(concept, *nodes):
    return {"type": "Holds", "concept": concept,
            "node": nodes[0] if len(nodes) > 0 else None,
            "node2": nodes[1] if len(nodes) > 1 else None}


def _and(*items):
    return {"type": "And", "items": list(items)}


def _not(arg):
    return {"type": "Not", "arg": arg}


def _exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name,
            "predicate": predicate}


# --- (a) THE SHAPE's antecedent, faithful to invariant_representation.py's rule
#     `characterize_by_invariant_relations_among_parts` if-clauses:
#       IF1: "object instances are related by a transformation group that shifts
#             and scales the absolute coordinates of every part"
#       IF2: "the absolute coordinate values of the parts are non-invariant under
#             the transformation group"
#     Structure asserted by that prose:
#       (1) THERE EXISTS, over the instances of the object, a transform whose action
#           on EVERY part is (shifts AND scales) that part's absolute coordinate;
#       (2) AND the absolute coordinate values are NOT invariant under the group.
#     Read as a Term-tree: And( Exists(instances, part, And(shifts(part), scales(part))),
#                               Not(invariant_under_group(absolute_coordinate_values)) ).
SHAPE_ANTECEDENT_TERM = _and(
    _exists(
        _holds("instances_of_object"), "part",
        _and(
            _holds("shifts_absolute_coordinate", _var("part")),
            _holds("scales_absolute_coordinate", _var("part")),
        ),
    ),
    _not(_holds("invariant_under_transformation_group",
                _holds("absolute_coordinate_values"))),
)

# --- (b) THE FRAME's antecedent, faithful to surface_feature_representation_frame's
#     own text:
#       "a change of talker or accent SHIFTS and SCALES the measured feature values
#        even when the spoken word is the same" ;
#       "The values vary with the talker; they are NON-INVARIANT to the speaker."
#       (over instances of the same word spoken by different talkers).
#     Structure asserted by that prose:
#       (1) THERE EXISTS, over the instances [same word, different talkers], a transform
#           [talker/accent] whose action on EVERY measured feature is (shifts AND scales)
#           that feature's absolute value;
#       (2) AND the absolute feature values are NOT invariant to the speaker.
#     Read as a Term-tree, INDEPENDENTLY of the shape (same proposition, frame's own
#     vocabulary): And( Exists(instances, feature, And(shifts(feature), scales(feature))),
#                       Not(invariant_to_speaker(absolute_feature_values)) ).
FRAME_ANTECEDENT_TERM = _and(
    _exists(
        _holds("instances_same_word_diff_talkers"), "feature",
        _and(
            _holds("shifts_absolute_feature_value", _var("feature")),
            _holds("scales_absolute_feature_value", _var("feature")),
        ),
    ),
    _not(_holds("invariant_to_speaker",
                _holds("absolute_feature_values"))),
)


def _build(with_acquired: bool):
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_development(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    if with_acquired:
        install_invariant_representation_seed(sub)
    return sub


def _register_frame(sub):
    mt = sub.add_node("Microtheory", {
        "name": "perceptual_representation_paradigm",
        "origin": "jabberwock_shape_based_transfer"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "jabberwock_shape_based_transfer:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "surface_feature_representation_frame", _FRAME_TEXT)
    return mt


def _shape_aware_library(sub):
    """The agent's harvested library, with the re_represent donor LIFTED to a
    structural donor: its target_shape is the SHAPE of its own antecedent Term-tree
    (computed by the agent's shape_of_term walker), and match_mode='shape' so
    differentiate uses shapes_compatible instead of the word conjunction. Every
    other donor is untouched. NO-DONKEY: the donor's structural key is its own
    antecedent's shape, not a value picked to match the frame."""
    lib = harvest_shapes_combined(sub)
    shape_axes = sub.shape_of_term(SHAPE_ANTECEDENT_TERM)
    n_lifted = 0
    for d in lib:
        if d.get("name") == \
                "rule_derived__characterize_by_invariant_relations_among_parts":
            d["match_mode"] = "shape"
            d["target_shape"] = shape_axes
            n_lifted += 1
    return lib, shape_axes, n_lifted


def _show_gap(g, prefix=""):
    print(f"{prefix}    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"{prefix}       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"{prefix}       source_concepts={g.get('source_concepts')}")
    print(f"{prefix}       gap: {g['gap']}")


def main():
    print("=" * 78)
    print("ITER-22 — SHAPE-BASED (structural) TRANSFER of the re_represent shape")
    print("=" * 78)

    # ----- Step 1 recap (printed for the doc) -----------------------------
    print("\n[Step 1] match_mode='shape' / shapes_compatible (runners/dsl/src/shape.rs):")
    print("  A Term-tree's Shape = {recursion, order_n, abstraction}, computed by the")
    print("  agent's own walker (shape_of_term). shapes_compatible(candidate, target):")
    print("    recursion must be EQUAL; candidate.order_n >= target.order_n;")
    print("    Parametric satisfies Concrete (not vice-versa).")
    print("  In differentiate(): for a donor with match_mode='shape' + target_shape,")
    print("  it fires iff shapes_compatible(donor.target_shape, postulate_shape) — i.e.")
    print("  the DONOR (candidate) structurally subsumes the FRAME (target).")

    sub = _build(with_acquired=True)

    # ----- Step 2 — the two FAITHFUL Term-trees, VERBATIM -----------------
    print("\n" + "=" * 78)
    print("[Step 2] THE TWO FAITHFUL Term-trees (verbatim) — each from its OWN text")
    print("=" * 78)
    print("\n--- SHAPE antecedent (from invariant_representation.py rule if-clauses) ---")
    print(json.dumps(SHAPE_ANTECEDENT_TERM, indent=2))
    print("\n--- FRAME antecedent (from surface_feature_representation_frame text) ---")
    print(json.dumps(FRAME_ANTECEDENT_TERM, indent=2))

    shape_axes = sub.shape_of_term(SHAPE_ANTECEDENT_TERM)
    frame_axes = sub.shape_of_term(FRAME_ANTECEDENT_TERM)
    print("\n  shape_of_term(SHAPE antecedent) =", shape_axes)
    print("  shape_of_term(FRAME antecedent) =", frame_axes)

    # ----- Step 3 — does the structural matcher fire? ---------------------
    print("\n" + "=" * 78)
    print("[Step 3] STRUCTURAL transfer: shapes_compatible (the matcher decides)")
    print("=" * 78)
    fires = sub.shapes_compatible(shape_axes, frame_axes)
    print(f"  shapes_compatible(shape_donor, frame)  = {fires}")
    print(f"  shapes_compatible(frame, shape_donor)  = "
          f"{sub.shapes_compatible(frame_axes, shape_axes)}")
    # Discriminance controls — genuinely DIFFERENT structures, to show the
    # match is not trivial (any-vs-any). A flat cancel/eq frame has a SIMPLER
    # shape; the re_represent donor (order 4, parametric) subsumes it too, which
    # is exactly shapes_compatible's documented semantics (candidate could
    # produce target) — reported honestly.
    cancel_tree = {"type": "Minus", "a": _holds("formant_value"),
                   "b": _holds("mean_formant_value")}
    print("\n  [control] a flat 'cancel' tree (Minus(formant, mean_formant)):")
    print("    shape_of_term =", sub.shape_of_term(cancel_tree))
    print("    shapes_compatible(shape_donor, cancel) =",
          sub.shapes_compatible(shape_axes, sub.shape_of_term(cancel_tree)),
          "(donor subsumes simpler targets — shapes_compatible semantics)")
    print("    shapes_compatible(cancel, shape_donor) =",
          sub.shapes_compatible(sub.shape_of_term(cancel_tree), shape_axes),
          "(the SIMPLER cancel does NOT subsume the richer re_represent structure)")

    # ----- Step 4 — THE TEST: does synthesize_gaps now DERIVE it? ---------
    print("\n" + "=" * 78)
    print("[Step 4] THE TEST — synthesize_gaps over the perceptual frame")
    print("=" * 78)

    # Register the frame's faithful Term-tree so synthesize_gaps' Shape branch can
    # compute the frame's postulate_shape (world-adapter boundary).
    harvester_shape.register_postulate_term(
        "surface_feature_representation_frame", FRAME_ANTECEDENT_TERM)

    for label in ("LEXICAL transfer (iter-21: match_mode='all')",
                  "STRUCTURAL transfer (iter-22: match_mode='shape')"):
        structural = label.startswith("STRUCTURAL")
        s2 = _build(with_acquired=True)
        _register_frame(s2)
        if structural:
            lib, axes, n_lifted = _shape_aware_library(s2)
            print(f"\n  --- {label} ---")
            print(f"  (re_represent donor lifted to structural: {n_lifted}; "
                  f"target_shape={axes})")
            gaps = synthesize_gaps(s2, "surface_feature_representation_frame",
                                   shapes=lib, record=False, prune=False,
                                   max_order=3)
        else:
            print(f"\n  --- {label} ---")
            gaps = synthesize_gaps(s2, "surface_feature_representation_frame",
                                   shapes="harvested", record=False, prune=False,
                                   max_order=3)
        print(f"  n gaps surfaced: {len(gaps)}")
        change_side = []
        for g in gaps:
            roles = breadth_audit.classify_shape_role(
                breadth_audit._gap_to_shapelike(g))
            tag = ",".join(roles) or "unclassified"
            print(f"    [{tag:14}]")
            _show_gap(g)
            if "re_represent" in roles:
                change_side.append(g)
        print(f"  >>> change-side (re_represent) gaps surfaced: {len(change_side)}")
        if structural and change_side:
            print("\n  RE_REPRESENT GAP DERIVED (verbatim):")
            for g in change_side:
                print(f"    capability_keys = {g['capability_keys']}")
                print(f"    via_shapes      = {g['via_shapes']}")
                print(f"    source_concepts = {g.get('source_concepts')}")
                print(f"    gap             = {g['gap']}")


if __name__ == "__main__":
    main()
