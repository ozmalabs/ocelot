"""iter-24 — the agent DERIVES the SCALE-invariant relation (analogical transfer of
difference-cancels-shift from the VALUE axis to the BAND-INDEX axis).

THE SITUATION (iter-23, commit a57ce7ae). The agent's self-derived relational
representation (band-VALUE difference rel_i = band_{i+1} - band_i) is invariant BY
CONSTRUCTION to the talker's additive LEVEL (a value shift). It does NOT lift the
0.20 ceiling, and cross-speaker stays at chance, because the DOMINANT cross-speaker
nuisance is VTL — a vocal-tract-length change SCALES the formant FREQUENCIES, which
on the log/mel band-INDEX axis is approximately a UNIFORM SHIFT ALONG THE BAND-INDEX
AXIS. A band-VALUE difference is invariant to a value shift, but NOT to a band-index
shift. (iter-23 doc, residual #1, verbatim.)

THE DERIVATION THIS SCRIPT DRIVES (NO-DONKEY). The agent already HOLDS:
  • the re_represent shape `characterize_by_invariant_relations_among_parts`
    (acquired iter-21, invariant theory / Erlangen): "represent the object by the
    invariant RELATIONS among its parts ... preserved under the transformation group
    ... rather than by the parts' absolute coordinate values"; and
  • the iter-23 RESIDUAL: the band-value relation cancels the VALUE shift but not the
    band-INDEX shift.

The agent's OWN move (analogical transfer, the same difference-cancels-shift shape it
already used on the VALUE axis) is to APPLY THE SAME re_represent SHAPE TO THE
RESIDUAL FRAME, whose transformation group now acts on the band-INDEX COORDINATE of
every part. This script does NOT assert the answer: it registers the residual as a
postulate (honest text + a FAITHFUL Term-tree built clause-by-clause from that text,
exactly as iter-22 did), then runs the agent's synthesize_gaps with the SAME
shape-aware library. Whatever re_represent gap synthesize_gaps surfaces ONTO THIS
FRAME is the agent's derivation, reported VERBATIM. The composition (Step 2) is then
read straight off that derived gap + the frame's own "parts = landmark positions"
identification, with no new design choice.

Run:  python scripts/iter24_scale_invariant_derive.py
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

# Reuse iter-22's faithful SHAPE antecedent + helpers (the agent's acquired shape).
from scripts.jabberwock_shape_based_transfer import (
    SHAPE_ANTECEDENT_TERM, _and, _not, _exists, _holds, _var,
)


# ---------------------------------------------------------------------------
# Step 1 — register the iter-23 RESIDUAL as a postulate the agent HOLDS.
#
# The text is the honest residual: a band-VALUE difference cancels an additive
# LEVEL shift of the band VALUES, but a VTL change scales the formant FREQUENCIES =
# a uniform shift along the band-INDEX axis, to which band-VALUE differences are NOT
# invariant. NOTHING here names the answer (no "spacing", no "landmark relation as a
# fix"); it states the residual + identifies the parts whose POSITIONS the band-index
# transform moves, exactly as the surface frame stated the parts whose VALUES the
# talker level moved.
# ---------------------------------------------------------------------------
_RESIDUAL_TEXT = (
    "The unit's relational representation takes the band-to-band VALUE difference, "
    "which cancels an additive LEVEL shift of the band values by construction and is "
    "invariant to the talker's channel / loudness. But a change of talker also "
    "changes the vocal-tract length, and a VTL change SCALES the formant FREQUENCIES "
    "— on the log / mel / bark band-INDEX axis this scaling is approximately a "
    "UNIFORM SHIFT ALONG THE BAND-INDEX AXIS: the whole spectral pattern, and the "
    "POSITIONS of its spectral landmarks (peaks) along the band-index axis, are "
    "translated together by the same number of bands. The band-VALUE differences are "
    "invariant to the value shift but they are NOT invariant to this band-INDEX "
    "shift: the landmark POSITIONS — the absolute band-index COORDINATES of the parts "
    "— move under the VTL transform, even when the spoken word is the same. So the "
    "parts here are the spectral landmarks, the transformation group is the band-index "
    "shift the VTL change induces, and the parts' absolute band-index coordinate "
    "values are non-invariant to the speaker.")


# Step 1 (faithful Term-tree). Built clause-by-clause from _RESIDUAL_TEXT's OWN
# structure, INDEPENDENTLY (same authoring boundary as iter-22's two trees):
#   (1) THERE EXISTS, over the instances [same word, different talkers], a transform
#       [the VTL band-index shift] whose action on EVERY part [landmark] is
#       (shifts AND scales) that part's absolute band-INDEX coordinate;
#       — here "shifts" = the band-index shift (the dominant VTL effect on the log
#         axis) and "scales" = the residual frequency-scale the shift approximates;
#         BOTH act on the part's band-INDEX coordinate, the residual's named axis.
#   (2) AND the parts' absolute band-index coordinate values are NOT invariant to
#       the speaker.
# Read as a Term-tree, in the residual frame's OWN vocabulary (landmark / band-index
# coordinate), same logical shape as the acquired rule:
#   And( Exists(instances, landmark,
#               And(shifts_band_index_coordinate(landmark),
#                   scales_band_index_coordinate(landmark))),
#        Not(invariant_to_speaker(absolute_band_index_coordinates)) ).
RESIDUAL_ANTECEDENT_TERM = _and(
    _exists(
        _holds("instances_same_word_diff_talkers"), "landmark",
        _and(
            _holds("shifts_band_index_coordinate", _var("landmark")),
            _holds("scales_band_index_coordinate", _var("landmark")),
        ),
    ),
    _not(_holds("invariant_to_speaker",
                _holds("absolute_band_index_coordinates"))),
)


def _build(with_acquired: bool = True):
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


def _register_residual(sub):
    mt = sub.add_node("Microtheory", {
        "name": "scale_residual_paradigm",
        "origin": "iter24_scale_invariant_derive"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "iter24:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "scale_residual_frame", _RESIDUAL_TEXT)
    return mt


def _shape_aware_library(sub):
    """Same as iter-22: lift the re_represent donor to a STRUCTURAL donor keyed by
    the SHAPE of its OWN antecedent Term-tree. NO-DONKEY: the donor's structural key
    is its own antecedent's shape, not a value picked to match the residual frame."""
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
    print("ITER-24 — the agent DERIVES the SCALE-invariant relation (band-INDEX axis)")
    print("=" * 78)

    sub = _build(with_acquired=True)

    # ---- Step 1: the residual postulate + its faithful Term-tree -----------
    print("\n[Step 1] Register the iter-23 RESIDUAL as a held postulate.")
    print("  residual text (the band-value relation cancels the VALUE shift but the")
    print("  VTL transform is a band-INDEX shift to which it is NOT invariant):")
    print("  ", _RESIDUAL_TEXT)
    print("\n  --- RESIDUAL antecedent Term-tree (faithful, clause-by-clause) ---")
    print(json.dumps(RESIDUAL_ANTECEDENT_TERM, indent=2))

    shape_axes = sub.shape_of_term(SHAPE_ANTECEDENT_TERM)
    res_axes = sub.shape_of_term(RESIDUAL_ANTECEDENT_TERM)
    print("\n  shape_of_term(acquired re_represent antecedent) =", shape_axes)
    print("  shape_of_term(RESIDUAL antecedent)               =", res_axes)
    print("  shapes_compatible(re_represent, residual)        =",
          sub.shapes_compatible(shape_axes, res_axes))

    # ---- Step 2: run synthesize_gaps over the residual frame --------------
    print("\n" + "=" * 78)
    print("[Step 2] synthesize_gaps over the RESIDUAL frame — what does it DERIVE?")
    print("=" * 78)

    s2 = _build(with_acquired=True)
    _register_residual(s2)
    harvester_shape.register_postulate_term(
        "scale_residual_frame", RESIDUAL_ANTECEDENT_TERM)
    lib, axes, n_lifted = _shape_aware_library(s2)
    print(f"  (re_represent donor lifted to structural: {n_lifted}; "
          f"target_shape={axes})")
    gaps = synthesize_gaps(s2, "scale_residual_frame", shapes=lib,
                           record=False, prune=False, max_order=3)
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
    print(f"\n  >>> change-side (re_represent) gaps surfaced on the RESIDUAL frame: "
          f"{len(change_side)}")
    if change_side:
        print("\n  THE DERIVED re_represent GAP (verbatim), now applied to the")
        print("  RESIDUAL frame whose parts = landmark positions, whose transform =")
        print("  the band-INDEX shift:")
        for g in change_side:
            print(f"    capability_keys = {g['capability_keys']}")
            print(f"    via_shapes      = {g['via_shapes']}")
            print(f"    source_concepts = {g.get('source_concepts')}")
            print(f"    gap             = {g['gap']}")
            print(f"    chain:")
            for step in g["chain"]:
                print(f"      - {step}")


if __name__ == "__main__":
    main()
