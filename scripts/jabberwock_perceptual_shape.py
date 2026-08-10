"""jabberwock_perceptual_shape — have the AGENT derive what its PERCEPTUAL
REPRESENTATION needs, by the SAME mechanism scripts/reframe_is_order_n.py used.

Iter-17 (reframe_is_order_n) proved: register a FRAME as a higher-order postulate
in order_n_postulates' OWN representation, run the EXISTING shape-aware
synthesize_gaps over it, and the agent's own operator derives the reframe — nothing
seeded. Iter-19 does the SAME for the PERCEPTUAL-REPRESENTATION frame.

The perceptual front-end (gammatone -> invariant -> CMVN, per-frame surface
features matched against stored exemplars) is co-limiting continuous recognition:
with GOLD word-boundaries it ceilings at same-word within-NN ~0.20 (shallow-CNN
0.32, SSL 0.49). We register that frame HONESTLY — describing only what the current
representation IS and the symptom it produces — with NO answer seeded (the words
"shape" / "relational" / "structure" / "whole-unit" / "transform-invariant" do
NOT appear in the postulate text). Whatever the agent's own operator surfaces is
the agent's, not ours.

This script does NOT do the derivation. It WIRES the perceptual frame into the
operator's real representation and RUNS the existing operator. The chain printed
is verbatim from synthesize_gaps — the agent's machinery.

Run:  python scripts/jabberwock_perceptual_shape.py
"""
from __future__ import annotations

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
from domains.code_authoring import _install_concept
from domains.order_n_postulates import synthesize_gaps, harvest_postulates


def _build():
    """The same agent the order_n_postulates / reframe demos build: its speech
    impl + the speech SCIENCE it holds + its cross-domain BREADTH (the source of
    harvested implication-shapes)."""
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
    return sub


def _register_frame_postulates(sub):
    """Register the PERCEPTUAL-REPRESENTATION frame as a higher-order postulate,
    in the operator's OWN representation (a Concept under a Microtheory, with the
    property text the operator differentiates). NO new mechanism — these are
    ordinary postulates harvest_postulates() picks up.

    The postulate text is the HONEST description of what the current perceptual
    representation IS and the symptom it produces. It deliberately seeds NO answer:
    the words 'shape', 'relational', 'structure', 'whole-unit', 'transform-
    invariant' do not appear. Whether the operator's own shapes fire on that honest
    text — and WHAT they surface — is exactly the thing under test.

    Returns the Mt id."""
    mt = sub.add_node("Microtheory", {
        "name": "perceptual_representation_paradigm",
        "description": "the agent's current frame for how it REPRESENTS a "
                       "perceptual unit, registered as a higher-order postulate",
        "origin": "jabberwock_perceptual_shape"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "jabberwock_perceptual_shape:has_concept"})
    except Exception:
        pass

    # (1) THE FRAME — honest description of the current perceptual representation
    #     and the symptom. NO answer seeded.
    _install_concept(
        sub, mt, "surface_feature_representation_frame",
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

    return mt


def _show(gap):
    for line in gap["chain"]:
        print(f"    {line}")
    print(f"    => GAP (order-{gap['order']}): keys={gap['capability_keys']}")
    print(f"       via_shapes={gap['via_shapes']}  domains={gap['source_domains']}")
    print(f"       source_concepts={gap.get('source_concepts')}")


def _run_over(sub, postulate, shapes_label, prune):
    """Run the EXISTING operator over the frame-postulate. Report VERBATIM every
    gap it surfaces — no filtering, no answer-naming. The operator decides."""
    print(f"\n--- synthesize_gaps('{postulate}', shapes={shapes_label!r}, "
          f"prune={prune}) ---")
    gaps = synthesize_gaps(sub, postulate, shapes=shapes_label, record=False,
                           prune=prune, max_order=3)
    if not gaps:
        print("    (operator surfaced NO gap)")
        return []
    for g in gaps:
        print("\n  GAP")
        _show(g)
    return gaps


def main():
    sub = _build()
    _register_frame_postulates(sub)

    print("=" * 78)
    print("PERCEPTUAL-REPRESENTATION FRAME REGISTERED AS A POSTULATE")
    print("=" * 78)
    names = {nm for _, nm, _ in harvest_postulates(sub)}
    p = "surface_feature_representation_frame"
    present = p in names
    print(f"  {'OK ' if present else 'MISS'} harvest_postulates() picks up "
          f"'{p}': {present}")

    print("\n" + "=" * 78)
    print("RUN THE EXISTING order_n_postulates OPERATOR OVER THE FRAME-POSTULATE")
    print("=" * 78)
    print("No new operator. Just synthesize_gaps over the perceptual frame, with")
    print("the agent's OWN harvested shapes (and the hand stencil for comparison).")
    print("Nothing in the postulate names the answer; whatever surfaces is the")
    print("agent's.")

    for prune in (False, True):
        print("\n" + "#" * 78)
        print(f"# prune={prune}  ({'DERIVATION only' if not prune else 'OPEN gaps only'})")
        print("#" * 78)
        for label in ("harvested", "stencil"):
            _run_over(sub, p, label, prune)


if __name__ == "__main__":
    main()
