"""reframe_is_order_n — is the agent's REFRAME a NEW meta-ability, or just its
EXISTING order_n_postulates operator run at a HIGHER ORDER (over the FRAME itself)?

The user's thesis: the agent already SYNTHESIZES its own gaps WITHIN a frame
(domains/order_n_postulates.py: take a held postulate, transfer an implication-
SHAPE, surface the un-realized implication = the next gap). A FRAME is just a
higher-order postulate. So the REFRAME = the SAME operator climbing to the
frame-level once the lower-order (feature / segmentation / invariance) gaps are
exhausted. NO new operator, NO exhaustion-detector, NO frame-analogy-engine.

THE TEST (known answer = analysis-by-synthesis):
  Register the FRAME as a postulate in the operator's OWN representation
  (a Concept under a Microtheory, exactly like every other postulate the
  operator harvests), alongside the postulate that the agent HAS a forward
  model (speak/speak_as maps word -> sound). Then RUN THE EXISTING
  synthesize_gaps operator over it. Does its order-N derivative surface the
  inverse/generative reframe — recognition = INVERT the forward model
  (analysis-by-synthesis) — ON ITS OWN, without the answer being supplied?

CRITICAL: this script does NOT do the derivation. It WIRES the frame-postulate
into the operator's real representation and RUNS the existing operator. The
derivation chain printed is verbatim from synthesize_gaps — the agent's machinery.

The postulate property-text is the HONEST description of what each postulate is
(no regex-gaming): the bottom-up paradigm RECOVERS THE WORD (the cause) FROM the
acoustic CUES (the effects); the agent HAS a forward model. Whether the
operator's own shapes fire on that honest text is exactly the thing under test.

Run:  python scripts/reframe_is_order_n.py
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
    """The same agent the order_n_postulates demo builds: its speech impl + the
    speech SCIENCE it holds + its cross-domain BREADTH (the source of harvested
    implication-shapes)."""
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
    """Register the FRAME as a higher-order postulate, in the operator's OWN
    representation (a Concept under a Microtheory, with definition+why = the
    property text the operator differentiates). NO new mechanism — these are
    ordinary postulates the existing harvest_postulates() will pick up.

    Two postulates, described HONESTLY (not regex-gamed):

      (1) the FRAME (the bottom-up recognition paradigm). What it IS: recognition
          RECOVERS THE WORD (the cause) FROM the acoustic CUES (the effects) by
          forward-matching observed features to stored exemplars. That honest
          description is, structurally, "recovering causes from effects" /
          "recover ... from ... cue" — an inverse-problem statement. We do NOT add
          the word 'inverse' or 'analysis-by-synthesis'; those are the operator's
          to derive.

      (2) the agent HAS a FORWARD model: speak / speak_as maps word -> sound
          (production). This is the resource the inverse needs.

    Returns the Mt id."""
    mt = sub.add_node("Microtheory", {
        "name": "recognition_paradigm",
        "description": "the agent's current frame for speech recognition, "
                       "registered as higher-order postulates",
        "origin": "reframe_is_order_n"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "reframe_is_order_n:has_concept"})
    except Exception:
        pass

    # (1) THE FRAME — honest description of the bottom-up recognition paradigm.
    _install_concept(
        sub, mt, "bottom_up_recognition_frame",
        "Speech recognition must RECOVER THE WORD (the underlying cause) FROM the "
        "acoustic CUES it produced (the observed effects): perception forward-"
        "matches the observed features against stored exemplars and votes for the "
        "best match. The word is the hidden cause; the acoustics are the effects "
        "the listener must recover from the cue.")

    # (2) THE FORWARD MODEL the agent already owns.
    _install_concept(
        sub, mt, "agent_has_forward_model",
        "The agent owns a FORWARD model of speech PRODUCTION: speak / speak_as "
        "maps a word (and a chosen voice) to its sound — articulation produces "
        "acoustics. The agent can run this generative production model to "
        "reproduce a target utterance and imitate what it would have said.")
    return mt


def _show(gap):
    for line in gap["chain"]:
        print(f"    {line}")
    print(f"    => GAP (order-{gap['order']}): keys={gap['capability_keys']}")
    print(f"       via_shapes={gap['via_shapes']}  domains={gap['source_domains']}")
    print(f"       source_concepts={gap.get('source_concepts')}")


def _run_over(sub, postulate, shapes_label):
    """Run the EXISTING operator over one frame-postulate, prune OFF (we want the
    DERIVATION — does the order-N derivative reach AxS — independent of whether the
    capability is later marked implemented; AxS / analysis-by-synthesis is in fact
    a live un-realized gap, but prune-off isolates the derivation question)."""
    print(f"\n--- synthesize_gaps('{postulate}', shapes={shapes_label!r}, "
          f"prune=False) ---")
    gaps = synthesize_gaps(sub, postulate, shapes=shapes_label, record=False,
                           prune=False, max_order=3)
    if not gaps:
        print("    (operator surfaced NO gap)")
        return []
    axs = []
    for g in gaps:
        keys = [k.lower() for k in g["capability_keys"]]
        is_axs = any("analysis-by-synthesis" in k or "forward model" in k or
                     "synthesiser" in k for k in keys)
        tag = "  <== ANALYSIS-BY-SYNTHESIS (the reframe)" if is_axs else ""
        print(f"\n  GAP{tag}")
        _show(g)
        if is_axs:
            axs.append(g)
    return axs


def main():
    sub = _build()
    _register_frame_postulates(sub)

    print("=" * 78)
    print("FRAME REGISTERED AS POSTULATES (operator's own representation)")
    print("=" * 78)
    names = {nm for _, nm, _ in harvest_postulates(sub)}
    for p in ("bottom_up_recognition_frame", "agent_has_forward_model"):
        present = p in names
        print(f"  {'OK ' if present else 'MISS'} harvest_postulates() picks up "
              f"'{p}': {present}")

    print("\n" + "=" * 78)
    print("RUN THE EXISTING order_n_postulates OPERATOR OVER THE FRAME-POSTULATE")
    print("=" * 78)
    print("No new operator. No exhaustion-detector. No frame-analogy-engine.")
    print("Just synthesize_gaps over the frame, with the agent's OWN harvested")
    print("shapes (and the hand stencil shown for comparison).")

    derived_axs = {}
    for postulate in ("bottom_up_recognition_frame", "agent_has_forward_model"):
        print("\n" + "=" * 78)
        print(f"POSTULATE: {postulate}")
        print("=" * 78)
        for label in ("harvested", "stencil"):
            axs = _run_over(sub, postulate, label)
            if axs:
                derived_axs[(postulate, label)] = axs

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    if derived_axs:
        print("  The EXISTING operator, run over the frame registered as a")
        print("  higher-order postulate, DERIVED the inverse/generative reframe")
        print("  (analysis-by-synthesis) on its own. Where:")
        for (p, label), gs in derived_axs.items():
            print(f"    - postulate '{p}', shapes={label}: "
                  f"{[g['order'] for g in gs]} (order)")
        print("\n  ==> The reframe was NOT a missing capability. It is the SAME")
        print("      order_n_postulates operator pointed one level up — at the")
        print("      FRAME-postulate. The user's thesis is supported by a live run.")
    else:
        print("  The operator did NOT surface analysis-by-synthesis over the frame.")
        print("  Report exactly what it did surface (above). Thesis NOT supported")
        print("  by this wiring — see honest report.")


if __name__ == "__main__":
    main()
