"""iter-26 — the agent DERIVES the MULTI-CHANNEL STACK from its OWN shapes + the
iter-25 RESIDUAL. NO-DONKEY: this script registers iter-25's HONEST residual as a held
postulate and runs the agent's OWN synthesize_gaps over it with the agent's OWN
harvested shape-library. Whatever the agent's shapes surface IS the derivation,
reported VERBATIM. The script does NOT name the fix ("stack", "manner channel",
"voicing channel", "tracking", "continuity", "redundancy", "combine") in the residual
text — it states the residual STRUCTURALLY and lets the agent's implication-shapes
fire.

THE SITUATION (iter-25, commit 61bd405f). The agent autonomously DERIVED + COMPOSED the
SCALE-invariant formant-spacing relation over TRUE (waveform-LPC) formants. The object
finally carries real, shuffle-beating, speaker-robust signal (gate within-NN 0.153 vs
its own shuffle 0.011; cross-NN 0.043 vs surface 0.014; FSDD waveform-LPC 0.528 ~
baseline 0.544). But it does NOT clear surface (within-NN 0.153 < surface 0.204 < CNN
0.32 < SSL 0.49), and cross-NN stays small. iter-25 named TWO honest sub-residuals,
restated here as the order-0 postulate:

  (a) the representation rides on a SINGLE relational component (the formant spacings)
      computed ALONE — it throws away the WITHIN-speaker cues the raw band surface
      exploits (the overall spectral-envelope SHAPE; whether each frame is voiced /
      periodic vs unvoiced / aperiodic; the low / mid / high band energy balance).
      A single component carries all the burden, so where it is weak nothing backs it.
  (b) the few formant positions, estimated independently per frame, JITTER frame to
      frame (~2.4-4.4 candidates/frame, extra poles from tilt / noise / nasalisation),
      even though the true vocal-tract resonances move SMOOTHLY and continuously over a
      word.

Run:  python scripts/iter26_stacked_derive.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import breadth_audit
from domains.code_authoring import _install_concept
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps

# Re-use iter-25's full build (installs the agent's all-pole science + phonology +
# speech_science + engineering + concept-expansions, so its harvested library carries
# the parameterize, redundancy, and voicing-class shapes).
from scripts.iter25_lpc_formant_derive import _build


# ---------------------------------------------------------------------------
# Step 1 — register iter-25's RESIDUAL as a held postulate.
#
# Honest text: it states (a) the single-component-ness of the representation and the
# WITHIN-speaker cues it discards (spectral-envelope shape; voiced/unvoiced periodicity;
# band-energy balance), and (b) the per-frame JITTER of the formant estimate against the
# SMOOTH continuous true-resonance trajectories. It does NOT name the answer (no "stack",
# "manner", "voicing channel", "tracking", "continuity smoothing", "redundancy",
# "combine", "fuse", "median", "Kalman"). It states the residual + the kind of cue,
# exactly as iter-24/25's residuals stated parts + axis without naming the method.
# ---------------------------------------------------------------------------
_RESIDUAL_TEXT = (
    "The unit's representation is a SINGLE relational component: the spacings between "
    "the true formant positions, computed on its own. That one component is "
    "VTL-invariant by construction and carries real word identity above chance, but it "
    "rides on its own and throws away the WITHIN-speaker information the raw spectral "
    "surface keeps. The discarded information is the overall spectral-envelope SHAPE of "
    "each frame, whether the frame is voiced (periodic glottal source) or unvoiced "
    "(aperiodic noise), the sonorant-versus-sibilant balance of low, mid and high band "
    "energy, and the manner of the sound. These are exactly the frames being "
    "classified as voiced, unvoiced or silence, with very different statistics per "
    "class. A representation built from one component alone is fragile: where that one "
    "component is weak, nothing else backs it up. The reliability of a system built "
    "from a single component is the reliability of that component; building it from "
    "several complementary redundant components, each reliable in a different region, "
    "would make the whole more reliable than any one. Separately, the few formant "
    "positions are estimated independently in each frame, so the estimate JITTERS from "
    "frame to frame: extra spurious poles appear and disappear from spectral tilt, "
    "noise and nasalisation, two to four candidates per frame instead of the steady two "
    "or three. Yet the true vocal-tract resonances move SMOOTHLY and continuously "
    "across a word; each formant is a smooth function of time whose neighbouring-frame "
    "values are close. The frame-by-frame estimate is a noisy sample of that smooth "
    "underlying trajectory.")


def _register(sub):
    mt = sub.add_node("Microtheory", {
        "name": "stacked_representation_paradigm",
        "origin": "iter26_stacked_derive"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "iter26:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "single_component_frame", _RESIDUAL_TEXT)
    return mt


def _show(g):
    print(f"    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"       source_concepts={g.get('source_concepts')}")
    print(f"       gap: {g['gap']}")


def main():
    print("=" * 78)
    print("ITER-26 — the agent DERIVES the MULTI-CHANNEL STACK + tracking from its OWN")
    print("shapes, over the iter-25 RESIDUAL frame")
    print("=" * 78)

    print("\n[Step 1] Register iter-25's RESIDUAL as a held postulate:")
    print("  ", _RESIDUAL_TEXT)

    sub = _build()
    _register(sub)

    lib = harvest_shapes_combined(sub)
    print(f"\n  harvested library: {len(lib)} shapes (the agent's OWN).")

    print("\n" + "=" * 78)
    print("[Step 2] synthesize_gaps over the RESIDUAL frame — what does it DERIVE?")
    print("=" * 78)
    gaps = synthesize_gaps(sub, "single_component_frame", shapes=lib,
                           record=False, prune=False, max_order=3)
    print(f"  n gaps surfaced: {len(gaps)}\n")

    combine_gaps, manner_gaps, track_gaps = [], [], []
    for g in gaps:
        roles = breadth_audit.classify_shape_role(breadth_audit._gap_to_shapelike(g))
        tag = ",".join(roles) or "unclassified"
        print(f"    [{tag}]")
        _show(g)
        blob = (" ".join(g.get("via_shapes", [])) + " "
                + " ".join(g.get("capability_keys", [])) + " "
                + g.get("gap", "")).lower()
        if any(k in blob for k in ("redundan", "reliab", "complementary",
                                   "combine", "fuse", "integrat", "ensemble")):
            combine_gaps.append(g)
        if any(k in blob for k in ("voic", "manner", "class", "sonor", "sibil",
                                   "specialised", "specialized")):
            manner_gaps.append(g)
        if any(k in blob for k in ("smooth", "continu", "trajector", "track",
                                   "neighbour", "context", "predict-remove",
                                   "taylor", "local approx")):
            track_gaps.append(g)
        print()

    print("=" * 78)
    print("DERIVATION SUMMARY — the agent's OWN shapes, fired on the residual:")
    print("=" * 78)
    print(f"  (a) STACK a complementary/redundant component  -> {len(combine_gaps)} gap(s)")
    for g in combine_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (b) a WITHIN-speaker manner/voicing channel    -> {len(manner_gaps)} gap(s)")
    for g in manner_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (c) SHARPEN formants via continuity/tracking   -> {len(track_gaps)} gap(s)")
    for g in track_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")


if __name__ == "__main__":
    main()
