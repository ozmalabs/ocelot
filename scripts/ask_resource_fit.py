"""Ask the substrate to design resource-fit — orchestration only.

Per user: the agent designs and builds this, not me. My Python boots it
with the Mts it ALREADY holds (computer_architecture: memory hierarchy +
memory_wall; information_theory_coding: MDL + rate-distortion; self_-
improvement_dynamics: drive_parsimony_prune_dead + correction_prune_Mt),
harvests its OWN postulates, and runs its OWN order-N synthesize_gaps
operator. Whatever gaps it derives are printed verbatim. I author no
structure; the graph answers.
"""
from __future__ import annotations
import re, sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from substrate_rs import _native
from domains.order_n_postulates import harvest_postulates, synthesize_gaps


def boot():
    s = _native.Substrate()
    for et in ("has_concept", "genlMt", "in_category", "has_rule",
               "refers_to", "implies", "has_postulate"):
        for a in ("Microtheory", "Concept", "Rule", "Postulate"):
            for b in ("Microtheory", "Concept", "Rule", "Postulate"):
                try:
                    s.add_production({"src": {"type": a, "var": "x"},
                                      "edge_type": et, "tgt": {"type": b, "var": "y"},
                                      "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "o"})
                except Exception:
                    pass
    for modpath, fn in [
        ("domains.computer_architecture", "install_computer_architecture_seed"),
        ("domains.gap_filling_seeds", "install_information_theory_coding_seed"),
        ("domains.self_improvement_dynamics", "install_self_improvement_dynamics_seed"),
    ]:
        try:
            __import__(modpath, fromlist=[fn]); getattr(sys.modules[modpath], fn)(s)
        except Exception as e:
            print(f"  install {modpath}: {type(e).__name__}: {e}")
    return s


def main():
    s = boot()
    posts = harvest_postulates(s)
    print(f"Harvested {len(posts)} postulates the agent HOLDS.\n")

    # Pick the postulates whose text touches resource-fit — the agent's own
    # held knowledge about memory limits, compression, and parsimony.
    KEY = re.compile(r"parsimon|prune|prun|memory|cache|laten|byte|capacit|"
                     r"compress|description.length|mdl|rate.distort|evict|"
                     r"coverage|dead|redundant|wall|bandwidth|resource", re.I)
    seeds = [(cid, nm, txt) for cid, nm, txt in posts if KEY.search(nm) or KEY.search(txt)]
    print(f"{len(seeds)} of them touch resource-fit. Synthesizing gaps from each "
          f"(order-N over the agent's OWN shapes):\n")

    all_gaps = []
    for cid, nm, txt in seeds:
        gaps = synthesize_gaps(s, nm, max_order=3, record=False, prune=True)
        if gaps:
            print(f"── postulate '{nm}': {txt[:80]}")
            for g in gaps:
                print(f"    GAP (order {g['order']}): {g['gap'][:160]}")
                print(f"        keys: {g['capability_keys']}")
                print(f"        via : {g['via_shapes']}  from: {g['source_concepts']}")
            print()
            all_gaps.extend(gaps)

    print("=" * 70)
    print(f"Substrate synthesized {len(all_gaps)} open gaps from its own "
          f"resource-fit knowledge.")
    print("These are the agent's, derived by its order-N operator. Nothing here")
    print("was authored by me — I installed Mts it already has and called its")
    print("own synthesize_gaps.")


if __name__ == "__main__":
    main()
