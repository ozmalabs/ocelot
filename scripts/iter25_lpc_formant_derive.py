"""iter-25 — the agent DERIVES the SMOOTHED-ENVELOPE (LPC / all-pole) move from its
OWN parameterize shape + the iter-24 RESIDUAL.

THE SITUATION (iter-24, commit 4564ab8e). The agent autonomously DERIVED + COMPOSED
the SCALE-invariant relation (band-index landmark SPACINGS, VTL-invariant BY
CONSTRUCTION = 0.0). It did NOT lift, and a THIRD co-limit surfaced UNDERNEATH the
axis: the LANDMARK QUALITY. The spacing relation is built on RAW-spectrum ArgMax
peaks — a mean of 5.4 local maxima per frame (range 2-11), most of them spurious
envelope ripples, not the 2-3 TRUE formants. The spacings among spurious peaks are
noise, so a relation that is mathematically VTL-invariant carries little word
identity (gate within-NN 0.112 ~ shuffle 0.098; cross-NN 0.007 = chance; FSDD LOSO
dropped to 0.253). (iter-24 doc, VERDICT + residual, verbatim.)

THE DERIVATION THIS SCRIPT DRIVES (NO-DONKEY). The agent already HOLDS, in its OWN
breadth, the PARAMETERIZE / all-pole implication-shape (the breadth-audit's
`parameterize` role: "compress the SAME values to a few coefficients / a parametric
model"; evidence = all-pole / autoregressive / linear-predict / poles / coefficients).
That shape is harvested from the agent's OWN concept `IIR_filter` /
`linear_prediction_models_speech_autocorrelation` (a recursive / all-pole filter is
captured by a FEW poles, recovered by LINEAR PREDICTION; the pole angles ARE the
resonances). The agent also HOLDS the iter-24 RESIDUAL: the spacing relation is right
but its parts — the raw-spectrum peaks — are spurious, NOT the true formants.

The agent's OWN move is to APPLY ITS PARAMETERIZE / all-pole shape TO THE RESIDUAL
FRAME, whose object is the spectral ENVELOPE the formants live in: a few poles of an
all-pole model capture that envelope, and those few poles ARE the 2-3 true formants —
a SMOOTH envelope whose peaks are the formants, not the raw spectrum's ripples. This
script does NOT assert the answer: it registers the residual as an honest postulate
(it states the residual + identifies the object as the spectral envelope whose true
peaks are the vocal-tract RESONANCES; it does NOT say "LPC" or "all-pole"), INSTALLS
the agent's all-pole science (audio_coding_theory — the concepts the breadth-audit
counted), then runs synthesize_gaps with the agent's OWN harvested library. Whatever
parameterize / all-pole gap synthesize_gaps surfaces ONTO THIS FRAME is the agent's
derivation, reported VERBATIM. The composition (Step 2) then runs the SAME iter-24
spacing relation over the LPC-smoothed envelope's peaks.

Run:  python scripts/iter25_lpc_formant_derive.py
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
from domains.audio_coding_theory import install_audio_coding_theory_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.invariant_representation import install_invariant_representation_seed
from domains.code_authoring import _install_concept
from domains import breadth_audit
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps


# ---------------------------------------------------------------------------
# Step 1 — register iter-24's RESIDUAL as a postulate the agent HOLDS.
#
# The text is the honest iter-24 residual: the band-INDEX spacing relation IS
# invariant to the VTL band-index shift by construction, but it is built on the
# RAW gammatone spectrum's local maxima, which are 5-11 spurious envelope ripples
# per frame, NOT the 2-3 true formants. It identifies the OBJECT the relation needs
# — the smooth spectral ENVELOPE whose few true peaks are the vocal-tract RESONANCES
# — but DOES NOT name the answer (no "LPC", no "all-pole", no "Levinson", no
# "linear prediction", no "cepstral"). It states the residual + the kind of object,
# exactly as iter-24's residual stated the parts + the transform axis.
# ---------------------------------------------------------------------------
_RESIDUAL_TEXT = (
    "The unit's scale-invariant relational representation takes the SPACINGS between "
    "the POSITIONS of the spectral landmarks (peaks) along the band-index axis, which "
    "cancels the vocal-tract-length band-index shift by construction. But these "
    "landmarks are the local maxima of the RAW gammatone spectrum, and the raw "
    "spectrum has many small ripples: there are 5 to 11 local maxima per frame, most "
    "of them spurious — fine ripples of the source harmonics and noise, NOT the few "
    "true formants. The spacings among spurious peaks are noise, so the relation, "
    "though invariant by construction, carries little word identity. The relation "
    "needs the TRUE few formants. A formant is a RESONANCE of the vocal tract: the "
    "vocal tract is a resonant linear FILTER that imposes a SMOOTH spectral ENVELOPE "
    "on the glottal source, and the few peaks of that smooth envelope ARE the "
    "resonances — the true 2 to 3 formants. So the object the relation should be "
    "built on is the smooth spectral ENVELOPE, whose few peaks are the vocal-tract "
    "RESONANCES, rather than the raw spectrum with its many spurious ripples; the "
    "filter's resonances are what carry the word identity.")


def _build():
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
    # The agent's held all-pole / linear-prediction science — the concepts the
    # breadth-audit's `parameterize` role counts (IIR_filter,
    # linear_prediction_models_speech_autocorrelation). iter-24's build did NOT
    # install these, so its library held no parameterize shape and only the
    # re_represent shape could fire. Installing them lets the agent harvest its OWN
    # parameterize shape and transfer it onto the iter-24 residual.
    install_audio_coding_theory_seed(sub)
    install_all_concept_expansions(sub)
    install_invariant_representation_seed(sub)
    return sub


def _register_residual(sub):
    mt = sub.add_node("Microtheory", {
        "name": "landmark_quality_paradigm",
        "origin": "iter25_lpc_formant_derive"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "iter25:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "landmark_quality_frame", _RESIDUAL_TEXT)
    return mt


def _show_gap(g, prefix=""):
    print(f"{prefix}    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"{prefix}       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"{prefix}       source_concepts={g.get('source_concepts')}")
    print(f"{prefix}       gap: {g['gap']}")


def main():
    print("=" * 78)
    print("ITER-25 — the agent DERIVES the SMOOTHED-ENVELOPE (all-pole/LPC) move")
    print("=" * 78)

    print("\n[Step 1] Register iter-24's RESIDUAL as a held postulate.")
    print("  residual text (the spacing relation is right but its landmarks are raw-")
    print("  spectrum ripples, not the true formants; the object it needs is the")
    print("  smooth spectral ENVELOPE whose few peaks are the vocal-tract resonances):")
    print("  ", _RESIDUAL_TEXT)

    sub = _build()
    _register_residual(sub)

    # The agent's OWN harvested library — including the parameterize / all-pole shape
    # now that its all-pole science is installed.
    lib = harvest_shapes_combined(sub)
    by_role = {}
    for d in lib:
        for role in breadth_audit.classify_shape_role(
                breadth_audit._gap_to_shapelike(
                    {"gap": d.get("consequence", ""),
                     "capability_keys": d.get("name_keys", [])})):
            by_role.setdefault(role, 0)
            by_role[role] += 1
    allpole = [d for d in lib
               if "all-pole" in [k.lower() for k in d.get("name_keys", [])]]
    print(f"\n  harvested library: {len(lib)} shapes; "
          f"parameterize/all-pole shapes present: {len(allpole)}")
    for d in allpole:
        print(f"    - {d.get('name')}  (from concept '{d.get('source_concept')}', "
              f"domain {d.get('domain')})")

    print("\n" + "=" * 78)
    print("[Step 2] synthesize_gaps over the RESIDUAL frame — what does it DERIVE?")
    print("=" * 78)

    gaps = synthesize_gaps(sub, "landmark_quality_frame", shapes=lib,
                           record=False, prune=False, max_order=3)
    print(f"  n gaps surfaced: {len(gaps)}")
    parameterize_gaps = []
    for g in gaps:
        roles = breadth_audit.classify_shape_role(
            breadth_audit._gap_to_shapelike(g))
        tag = ",".join(roles) or "unclassified"
        print(f"    [{tag:18}]")
        _show_gap(g)
        # Identify the parameterize / all-pole derivation by its via_shape /
        # capability keys (the agent's OWN shape name), not by hand.
        via = " ".join(g.get("via_shapes", [])).lower()
        keys = " ".join(g.get("capability_keys", [])).lower()
        if ("allpole" in via or "all-pole" in keys or "lpc" in keys
                or "levinson" in keys or "autoregress" in keys
                or "parametric" in keys):
            parameterize_gaps.append(g)

    print(f"\n  >>> parameterize / all-pole gaps surfaced on the RESIDUAL frame: "
          f"{len(parameterize_gaps)}")
    if parameterize_gaps:
        print("\n  THE DERIVED parameterize / all-pole GAP (verbatim), now applied to")
        print("  the RESIDUAL frame whose object = the spectral envelope, whose true")
        print("  peaks = the vocal-tract resonances:")
        for g in parameterize_gaps:
            print(f"    capability_keys = {g['capability_keys']}")
            print(f"    via_shapes      = {g['via_shapes']}")
            print(f"    source_concepts = {g.get('source_concepts')}")
            print(f"    gap             = {g['gap']}")
            print(f"    chain:")
            for step in g["chain"]:
                print(f"      - {step}")
    else:
        print("\n  (No parameterize/all-pole gap surfaced — report what DID surface,")
        print("   do not substitute a hand-written answer.)")


if __name__ == "__main__":
    main()
