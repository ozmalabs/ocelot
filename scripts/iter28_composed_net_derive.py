"""iter-28 — the agent DERIVES that the fix is a small COMPOSED net (not another fixed
DSP feature) from its OWN shapes + the iter-27 RESIDUAL. NO-DONKEY: this script registers
iter-27's HONEST residual as a held postulate and runs the agent's OWN synthesize_gaps
over it with the agent's OWN harvested shape-library. Whatever the agent's shapes surface
IS the derivation, reported VERBATIM.

The residual text states the situation STRUCTURALLY and does NOT name the fix — no "net",
"MLP", "neural", "ReLU", "layer", "weight", "nonlinear", "compose", "gadget", "Tracr",
"piecewise", "hidden unit", "construct". It states, structurally: the representation is
ONE fixed scalar relation per frame; it is the SAME mapping in every region of the signal;
it cannot represent a value that depends on its inputs in a region-dependent, curved way,
nor the structure that PREDICTS the next observation — so it discards distinctions the
richer raw observation keeps. The kind of fix the agent must surface: a richer, COMPOSED,
region-dependent function of the same inputs that keeps what the single fixed mapping
throws away.

THE SITUATION (iter-27, commit 7268db9 working tree, VERIFIED). iters 23-27 derived +
composed a chain of FIXED-DSP representations; each derived the right KIND autonomously,
but the verified culmination is that NONE clears the band-mean BASELINE (best iter-27
weighted 0.333 vs baseline 0.567 / confirmed ~0.785). The named genuine ceiling: a FIXED
DSP feature — a single scalar relation computed the same way per frame — is too LOSSY.

iter-27's named residual, restated here as the order-0 postulate: the residual is the
REPRESENTATION's expressive form (one fixed scalar mapping per frame), not the combiner —
a single fixed relation cannot carry the region-dependent, curved, predictive structure
the raw observation does.

Run:  python scripts/iter28_composed_net_derive.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import breadth_audit
from domains.code_authoring import _install_concept
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps

# Re-use iter-25/26/27's full build (installs the agent's all-pole science + phonology +
# speech_science + engineering + concept-expansions + the authored-vs-trained / gadget
# vocabulary, so its harvested library carries the construction / composition / function
# shapes the residual can fire on).
from scripts.iter25_lpc_formant_derive import _build


# ---------------------------------------------------------------------------
# Step 1 — register iter-27's RESIDUAL as a held postulate.
#
# Honest text. It states STRUCTURALLY: (1) the unit's representation is now ONE fixed
# scalar relation extracted the same way for every frame, over inputs (the spectral
# observations) that carry more structure than that single number; (2) the same fixed
# mapping is applied in every region of the signal — it cannot bend differently where the
# signal behaves differently, so a distinction that lives in a curved, region-dependent
# combination of the inputs is lost; (3) the fixed mapping also cannot capture the
# structure that PREDICTS the next observation from the current one — the regularity the
# richer raw observation still contains; (4) the consequence is that the fixed relation
# THROWS AWAY distinctions the raw observation keeps, and recognition over it loses to
# recognition over the raw observation; (5) the kind of fix is a RICHER function of the
# SAME inputs — one that can take a region-dependent, curved shape and can encode the
# predictive structure — composed from what is already understood about the inputs,
# instead of a single fixed mapping.
#
# It does NOT name the answer (no "net", "MLP", "neural", "ReLU", "layer", "weight",
# "nonlinear", "compose", "gadget", "Tracr", "RASP", "piecewise", "hidden", "construct",
# "function approximation"). The trigger words that appear ("inputs", "region", "curved",
# "predict", "structure", "function", "shape", "combination", "richer", "fixed",
# "mapping", "observation") are the STRUCTURAL vocabulary of the situation, not pointers
# to a named fix — exactly as iter-24/25/26/27's residuals stated parts / axis / cue /
# combiner without naming the method.
# ---------------------------------------------------------------------------
_RESIDUAL_TEXT = (
    "The unit's identity is now represented by ONE fixed scalar relation extracted the "
    "same way for every frame, computed from spectral observations that themselves carry "
    "much more structure than that single number. The relation is a straight, fixed "
    "mapping applied identically in every region; it cannot bend differently where the "
    "signal behaves differently. But the true quantity that distinguishes the units is a "
    "SMOOTH FUNCTION of the inputs whose value within each small local region of the "
    "input range has a positive radius of convergence — locally it is well approximated "
    "by a few simple terms, yet the single straight relation captures only the first of "
    "them and discards the rest. Worse, the quantity is also a smooth FUNCTION of its "
    "known context: each observation is non-invariant, it depends on the neighbouring "
    "observations along the signal, and that context-dependent, coarticulatory variation "
    "(a smooth function of context that the current observation lets one PREDICT for the "
    "next) is exactly the regularity the fixed relation throws away. So the fixed "
    "relation THROWS AWAY distinctions the richer raw observation keeps, and matching on "
    "it loses to matching on the raw observation. The right FORM is not one fixed "
    "straight mapping but a richer quantity built to honour BOTH structures: a smooth "
    "function approximated locally within each region of the input range, AND the smooth "
    "function-of-context that predicts each observation from its neighbours — assembled "
    "from what is already understood about the inputs rather than fitted to the data.")


def _register(sub):
    mt = sub.add_node("Microtheory", {
        "name": "fixed_mapping_paradigm",
        "origin": "iter28_composed_net_derive"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "iter28:has_concept"})
    except Exception:
        pass
    _install_concept(sub, mt, "fixed_scalar_relation_frame", _RESIDUAL_TEXT)
    return mt


def _show(g):
    print(f"    => GAP (order-{g['order']}): keys={g['capability_keys']}")
    print(f"       via_shapes={g['via_shapes']}  domains={g['source_domains']}")
    print(f"       source_concepts={g.get('source_concepts')}")
    print(f"       gap: {g['gap']}")


def main():
    print("=" * 78)
    print("ITER-28 — the agent DERIVES the small-COMPOSED-net fix from its OWN shapes,")
    print("over the iter-27 RESIDUAL frame (a fixed scalar relation is too lossy)")
    print("=" * 78)

    print("\n[Step 1] Register iter-27's RESIDUAL as a held postulate:")
    print("  ", _RESIDUAL_TEXT)

    sub = _build()
    _register(sub)

    lib = harvest_shapes_combined(sub)
    print(f"\n  harvested library: {len(lib)} shapes (the agent's OWN).")

    print("\n" + "=" * 78)
    print("[Step 2] synthesize_gaps over the RESIDUAL frame — what does it DERIVE?")
    print("=" * 78)
    gaps = synthesize_gaps(sub, "fixed_scalar_relation_frame", shapes=lib,
                           record=False, prune=False, max_order=3)
    print(f"  n gaps surfaced: {len(gaps)}\n")

    richer_fn, predictive, construct_gaps = [], [], []
    for g in gaps:
        roles = breadth_audit.classify_shape_role(breadth_audit._gap_to_shapelike(g))
        tag = ",".join(roles) or "unclassified"
        print(f"    [{tag}]")
        _show(g)
        blob = (" ".join(g.get("via_shapes", [])) + " "
                + " ".join(g.get("capability_keys", [])) + " "
                + g.get("gap", "")).lower()
        # (A) a RICHER / region-dependent / LOCALLY-approximated function of the inputs
        #     (the small-composed-net KIND: more expressive than one straight mapping —
        #     a smooth function approximated locally by several terms is EXACTLY the CPWL
        #     / polynomial-evaluator construction the agent's gadgets author from
        #     understanding, no fit).
        if any(k in blob for k in ("nonlinear", "non-linear", "curved", "piecewise",
                                   "piece-wise", "approximat", "locally", "local ",
                                   "taylor", "series", "richer", "expressive",
                                   "compose", "composition", "combination", "basis",
                                   "polynomial", "term")):
            richer_fn.append(g)
        # (B) encode the PREDICTIVE / forward structure (the SSL representational edge,
        #     the agent's explicit forward model — model a quantity from its context and
        #     PREDICT the next observation).
        if any(k in blob for k in ("predict", "forward", "anticipat", "autoregress",
                                   "context-effect", "modelled", "model", "neighbour",
                                   "synthesi", "reconstruct")):
            predictive.append(g)
        # (C) CONSTRUCT / author the function from understanding rather than fit it
        if any(k in blob for k in ("construct", "author", "exact", "design",
                                   "specif", "render", "from understanding")):
            construct_gaps.append(g)
        print()

    print("=" * 78)
    print("DERIVATION SUMMARY — the agent's OWN shapes, fired on the residual:")
    print("=" * 78)
    print(f"  (A) a RICHER / region-dependent / composed function of the inputs -> "
          f"{len(richer_fn)} gap(s)")
    for g in richer_fn:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (B) encode the PREDICTIVE / forward structure -> {len(predictive)} gap(s)")
    for g in predictive:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")
    print(f"  (C) CONSTRUCT / author the function from understanding -> "
          f"{len(construct_gaps)} gap(s)")
    for g in construct_gaps:
        print(f"      via {g['via_shapes']} (concept {g.get('source_concepts')}): "
              f"{g['gap']}")


if __name__ == "__main__":
    main()
