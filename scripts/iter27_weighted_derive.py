"""iter-27 — the agent DERIVES the per-channel/per-contrast WEIGHTED decision from its
OWN shapes + the iter-26 RESIDUAL. NO-DONKEY: this script registers iter-26's HONEST
residual as a held postulate and runs the agent's OWN synthesize_gaps over it with the
agent's OWN harvested shape-library. Whatever the agent's shapes surface IS the
derivation, reported VERBATIM. The residual text states the situation STRUCTURALLY and
does NOT name the fix ("weight", "weighted recognizer", "recognition_graph", "argmax",
"per-channel weight", "pairwise", "rec_weight", "Fisher", "combine by weighting").

THE SITUATION (iter-26, commit 7268db9 working tree). The agent autonomously DERIVED +
COMPOSED a MULTI-CHANNEL STACK over the iter-25 residual: FORMANT-RELATION (iter-25
spacing over true waveform-LPC formants, speaker-invariant) ++ MANNER/VOICING (the
agent's phonology cues, within-speaker). The agent derived the right KINDS of channel
(no-donkey held). But the iter-26 COMBINER — a SINGLE DTW over the CONCATENATION of the
two channels — REGRESSED below the formant channel alone (gate within-NN 0.071 < formant
0.153 < surface 0.204; FSDD STACK 0.311 < formant 0.528 < baseline 0.544). The two
channels carry COMPLEMENTARY signal (formant-relation separates words ACROSS speakers;
manner/voicing separates words WITHIN a speaker), but concatenating them into one vector
and running ONE distance over it treats every channel the same everywhere: the weak
channel drags the strong, and the channel that would separate a given word-pair is given
no more say than the one that is blind to it.

iter-26's named residual, restated here as the order-0 postulate: the residual is the
COMBINER + the recogniser, not the representation — the channels are right but a single
uniform distance over their concatenation dilutes them.

Run:  python scripts/iter27_weighted_derive.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import breadth_audit
from domains.code_authoring import _install_concept
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps

# Re-use iter-25/26's full build (installs the agent's all-pole science + phonology +
# speech_science + engineering + concept-expansions, so its harvested library carries
# the per-band-selection, redundancy, voicing-class, Bayes, and adaptation shapes).
from scripts.iter25_lpc_formant_derive import _build


# ---------------------------------------------------------------------------
# Step 1 — register iter-26's RESIDUAL as a held postulate.
#
# Honest text. It states STRUCTURALLY: (1) the unit's evidence comes from SEVERAL
# components (channels), each reliable in a DIFFERENT region / for a different
# contrast (one separates words across speakers, one within a speaker); (2) the
# current combiner concatenates them and runs ONE uniform distance over the whole,
# giving every component equal say everywhere; (3) which component actually
# discriminates DIFFERS by word-pair (different bands carry the distinction for
# different pairs), and the components' errors are not the same (their correlation
# differs across contrasts); (4) a treatment that adapts to WHICH component
# discriminates WHICH contrast, instead of one fixed uniform treatment, should beat
# it.
#
# It does NOT name the answer (no "weight", "weighted", "recognition_graph",
# "argmax", "rec_weight", "pairwise", "Fisher", "per-channel weight", "softmax",
# "attention", "tie-break", "combine by weighting"). It states the residual + the
# kind of fix STRUCTURALLY, exactly as iter-24/25/26's residuals stated parts /
# axis / cue without naming the method. The trigger words that appear ("different",
# "bands", "correlation", "redundant", "components", "each", "reliability",
# "evidence", "observed", "prior", "frames", "classified", "voiced", "unvoiced",
# "silence", "blocks", "signal", "statistics") are the STRUCTURAL vocabulary of the
# situation, not pointers to a named fix.
# ---------------------------------------------------------------------------
_RESIDUAL_TEXT = (
    "The unit's identity is now evidenced by SEVERAL complementary redundant "
    "components, not one: a relational component that separates words ACROSS "
    "different speakers, and a manner component carrying the within-speaker cues. "
    "Each component is reliable in a different region. But the current combiner "
    "concatenates these components into one long vector and runs a SINGLE uniform "
    "distance over the whole vector, so every component is given equal say "
    "everywhere, regardless of whether it discriminates the contrast at hand. This "
    "uniform treatment is fragile: where one component is weak and noisy it DRAGS "
    "the whole distance, washing out the component that does carry the distinction, "
    "and the combined result is worse than the stronger component used on its own. "
    "Yet WHICH component actually discriminates DIFFERS by the word-pair: for some "
    "pairs the relational component across speakers carries the whole distinction, "
    "for other pairs it is the manner component within a speaker, and for the "
    "different bands of the two components the correlation between the components' "
    "errors is different across the contrasts. The frames are also classified as "
    "voiced, unvoiced or silence, with different statistics per class. A single "
    "fixed uniform combination over all the components and all the bands is "
    "therefore the wrong decision rule: a decision that, for each contrast, leans "
    "on the component and the bands that actually separate that contrast — choosing "
    "per band and per block which evidence to trust given what is observed against "
    "the prior confusions — would beat the one fixed uniform distance. Per-band "
    "selection across the different blocks of the signal, matched to the local "
    "statistics, beats a fixed uniform treatment that ignores which band "
    "discriminates which contrast.")


def _register(sub):
    mt = sub.add_node("Microtheory", {
        "name": "weighted_combiner_paradigm",
        "origin": "iter27_weighted_derive"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "iter27:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "uniform_combiner_frame", _RESIDUAL_TEXT)
    return mt


def _show(g):
    print(f"    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"       source_concepts={g.get('source_concepts')}")
    print(f"       gap: {g['gap']}")


def main():
    print("=" * 78)
    print("ITER-27 — the agent DERIVES the per-channel/per-contrast WEIGHTED decision")
    print("from its OWN shapes, over the iter-26 RESIDUAL frame")
    print("=" * 78)

    print("\n[Step 1] Register iter-26's RESIDUAL as a held postulate:")
    print("  ", _RESIDUAL_TEXT)

    sub = _build()
    _register(sub)

    lib = harvest_shapes_combined(sub)
    print(f"\n  harvested library: {len(lib)} shapes (the agent's OWN).")

    print("\n" + "=" * 78)
    print("[Step 2] synthesize_gaps over the RESIDUAL frame — what does it DERIVE?")
    print("=" * 78)
    gaps = synthesize_gaps(sub, "uniform_combiner_frame", shapes=lib,
                           record=False, prune=False, max_order=3)
    print(f"  n gaps surfaced: {len(gaps)}\n")

    select_gaps, weight_gaps, combine_gaps = [], [], []
    for g in gaps:
        roles = breadth_audit.classify_shape_role(breadth_audit._gap_to_shapelike(g))
        tag = ",".join(roles) or "unclassified"
        print(f"    [{tag}]")
        _show(g)
        blob = (" ".join(g.get("via_shapes", [])) + " "
                + " ".join(g.get("capability_keys", [])) + " "
                + g.get("gap", "")).lower()
        # per-component/per-contrast SELECTION beats uniform (the weighted-decision KIND)
        if any(k in blob for k in ("selection", "per-band", "per-block", "per_band",
                                   "per_block", "selects", "choice", "adapt",
                                   "mode selection")):
            select_gaps.append(g)
        # leaning on the evidence by its reliability / likelihood (the WEIGHTING KIND)
        if any(k in blob for k in ("posterior", "prior", "evidence", "likelihood",
                                   "bayes", "reliab", "redundan")):
            weight_gaps.append(g)
        # combine several components into one stronger decision
        if any(k in blob for k in ("combin", "stronger", "either alone",
                                   "neurosymbolic", "fuse", "integrat")):
            combine_gaps.append(g)
        print()

    print("=" * 78)
    print("DERIVATION SUMMARY — the agent's OWN shapes, fired on the residual:")
    print("=" * 78)
    print(f"  (A) per-component / per-contrast SELECTION beats UNIFORM -> "
          f"{len(select_gaps)} gap(s)")
    for g in select_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (B) WEIGHT the evidence by its reliability / likelihood  -> "
          f"{len(weight_gaps)} gap(s)")
    for g in weight_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (C) COMBINE several components into one stronger decision -> "
          f"{len(combine_gaps)} gap(s)")
    for g in combine_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")


if __name__ == "__main__":
    main()
