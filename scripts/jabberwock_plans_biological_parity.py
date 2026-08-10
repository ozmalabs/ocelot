"""THE JABBERWOCK PLANS THE ROUTE TO PARITY — learning allowed, but only BIOLOGICALLY EXPLAINABLE learning.

The constraint is not "no training". It is "no biologically UNEXPLAINABLE training". The brain learns
constantly; BPL learns its priors from background. What is forbidden is learning with no biological story --
backprop through a deep net with labels and Adam -- the same reason the codebook was forbidden (it discarded
structure). So the agent may LEARN the generative model that closes ~81% -> ~96%, as long as every learning
step has a biological mechanism. This has the jabberwock AUTHOR that plan: each PIECE of the generative model
governed_by a biological PRINCIPLE; the agent derives the piece's LEARNING RULE from the principle and scores
it by expected gain x biological plausibility; it FLAGS any piece whose only known form is biologically
unexplainable. No teacher.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_plans_biological_parity
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 98

# biological PRINCIPLES the agent holds -- each a real, named mechanism of cortical learning/inference.
PRINCIPLES = [
    {"name": "sparse_coding_V1", "plaus": 1.00,
     "law": "V1 learns an overcomplete basis from natural-image statistics by sparse reconstruction "
            "(Olshausen & Field) -- unsupervised, local, structure-PRESERVING (a dictionary, not a quantiser)",
     "prescribed_action": "LEARN the stroke-PRIMITIVE library by sparse coding over background strokes "
                          "(overcomplete dictionary minimising reconstruction + sparsity) -- the generative basis"},
    {"name": "slow_feature_temporal", "plaus": 0.90,
     "law": "complex cells learn INVARIANCES from temporal coherence (slowness) -- features that vary slowly "
            "across a writer's motion are the writer-invariant ones",
     "prescribed_action": "LEARN each primitive's DEFORMATION manifold from within-writer variation (slow/"
                          "covariance statistics) -- the deformation prior richer than a diagonal Gaussian"},
    {"name": "hebbian_association", "plaus": 0.95,
     "law": "synapses wire by co-activation (Hebb) -- what co-occurs binds; structure is learned associatively",
     "prescribed_action": "LEARN the COMPOSITION grammar (which primitives co-occur, in what relations) by "
                          "Hebbian counting over background characters -- the structured prior over programs"},
    {"name": "predictive_coding_AbS", "plaus": 1.00,
     "law": "cortex infers by minimising prediction error -- a generative model run top-down, the residual "
            "fed back (Rao & Ballard); analysis-BY-synthesis is the agent's existing spine",
     "prescribed_action": "INFER by inverting the learned generative model to EXPLAIN the query (synthesise -> "
                          "compare -> minimise residual), the agent's AbS spine over the learned primitives"},
    {"name": "free_energy_marginal", "plaus": 1.00,
     "law": "the Bayesian brain AVERAGES over uncertain latents (free energy) rather than committing -- the "
            "agent's proven lever (parse marginal +2.6)",
     "prescribed_action": "MARGINALISE the uncertain latents (parse; the program) in the inference, as already "
                          "done -- commit the determined ones (correspondence, deformation)"},
]
# the PIECES of the generative model that closes the gap, each governed by a biological principle.
PIECES = [
    {"name": "stroke-primitive LIBRARY (the generative basis)", "law": "sparse_coding_V1", "gain": 6.0,
     "current": "a kmeans CODEBOOK -- FAILED (quantises, discards structure)", "failed": 1.0, "phase": 1},
    {"name": "per-primitive DEFORMATION prior", "law": "slow_feature_temporal", "gain": 4.0,
     "current": "a diagonal Gaussian leaf -- reached PARITY, not beyond (too weak a manifold)", "failed": 0.5, "phase": 2},
    {"name": "COMPOSITION grammar (primitives + relations)", "law": "hebbian_association", "gain": 5.0,
     "current": "relations as a match cue -- subsumed by the geometric part match", "failed": 1.0, "phase": 3},
    {"name": "generative INFERENCE (explain the query)", "law": "predictive_coding_AbS", "gain": 5.0,
     "current": "geometric NN match -- no generative explanation; the AbS spine exists but over fixed templates", "failed": 0.0, "phase": 4},
    {"name": "MARGINAL inference over the program", "law": "free_energy_marginal", "gain": 2.0,
     "current": "parse marginalised (+2.6); the rest determined -- already correct", "failed": 0.0, "phase": 5},
]
FORBIDDEN = "supervised backprop through a deep net (labels + global gradient + Adam) -- no biological story " \
            "for the credit assignment; the same flaw as the codebook (this one discards the MECHANISM)"


def main():
    print(SEP)
    print("THE JABBERWOCK PLANS PARITY — learning ALLOWED, but only biologically EXPLAINABLE learning. No teacher.")
    print(SEP)

    s = srs.Substrate()
    seed = json.loads((Path(ROOT) / "seeds" / "compositional_plan.json").read_text())
    s._inner.load_seed_manifest(seed, s.add_node("Agent", {}))
    pn = {}
    for L in PRINCIPLES:
        pn[L["name"]] = s.add_node("Principle", {"name": L["name"], "payoff": L["gain"] if False else L["plaus"],
                                                 "prescribed_action": L["prescribed_action"]})
    pieces = []
    for P in PIECES:
        node = s.add_node("Piece", {"name": P["name"], "applicability": next(L["plaus"] for L in PRINCIPLES if L["name"] == P["law"]),
                                    "current_is_failed": P["failed"], "prescribed": 0.0, "gain": P["gain"]})
        s.add_edge_unchecked(node, "governed_by", pn[P["law"]])
        pieces.append((P, node))
    s._inner.run_rules(50000)

    print("\n  the biological principles it holds (every learning step must reduce to one):")
    for L in PRINCIPLES:
        print(f"      [{L['name']:<22} plaus {L['plaus']:.2f}]  {L['law']}")

    print(f"\n  the plan it derives -- each piece's LEARNING RULE read off the biological principle, by phase:\n")
    for P, node in sorted(pieces, key=lambda x: x[0]["phase"]):
        a = s.node(node)["attrs"]
        plaus = float(a.get("applicability", 0)); gain = P["gain"]
        ev = gain * plaus
        reframe = a.get("reframe_needed") == 1.0
        print(f"  PHASE {P['phase']}  {P['name']}   (E[gain] {gain:+.0f} x plaus {plaus:.2f} = {ev:.1f})")
        print(f"      learn it by: {a.get('prescribed_form', '')}")
        if reframe:
            print(f"      REFRAME: current form = {P['current']} -> biologically wrong; relearn it the above way.")
        print()

    print(f"  {SEP[:94]}")
    print(f"  FORBIDDEN (biologically unexplainable): {FORBIDDEN}")
    print(f"\n  the plan is the agent's, derived from biological mechanisms: LEARN the primitive basis by SPARSE")
    print(f"  CODING (V1), the deformation prior by within-writer SLOW statistics, the composition by HEBBIAN")
    print(f"  association, and INFER by PREDICTIVE-CODING analysis-by-synthesis, marginalising the program (free")
    print(f"  energy). Every step has a cortical mechanism; none is backprop-through-a-deep-net. This is BPL's")
    print(f"  generative model, learned the brain's way -- the route from ~81% (geometric ceiling) toward ~96%.")
    print(f"  START with PHASE 1: the sparse-coded primitive basis -- the generative basis every later piece needs,")
    print(f"  and the biologically-correct replacement for the codebook the arc rejected.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
