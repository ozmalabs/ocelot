"""SHELL — sequence the agent's act of SELECTING among its three named learning
gaps (unsupervised CLUSTERING, TP SEGMENTATION, compositional GENERATION).

NO reasoning lives here. The shell:
  (1) builds the mind (full breadth -> the harvested implication-shape library is
      the agent's OWN concepts, the LIVE path, not the frozen _specify_ stubs);
  (2) runs the LIVE gap machinery (order_n_postulates.synthesize_over_all) to
      derive the full gap-map from the agent's held postulates;
  (3) reads the agent's OWN centrality/compression measure (gap_prioritiser:
      payoff = # held postulates a capability UNIFIES; the graph-resident Term,
      evaluated natively) and prints the ranking;
  (4) prints which of the three named learning gaps the agent's ranking places
      highest, and what postulates it unifies — the agent's CHOICE + REASON.

The choice is the agent's (its payoff Term over its own derivation graph). The
shell only prints it. Run: python scripts/jabberwock_frontier_select.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.phonology import install_phonology
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp


# the three LEARNING gaps the agent named, keyed by their distinctive capability terms
LEARNING_GAPS = {
    "unsupervised CLUSTERING (distributional categories)":
        ("unsupervised-clustering", "cross-speaker-clustering", "cross-speaker",
         "cluster", "mode"),
    "TP SEGMENTATION (boundaries at TP troughs)":
        ("transitional probability", "word-scale chunking",
         "statistical segmentation", "n-gram boundary", "boundary", "chunk"),
    "compositional GENERATION (ideas outside the seed)":
        ("generate", "compose", "novel", "invent", "all-pole", "parametric"),
}


def _build_mind():
    sub = Substrate()
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def main():
    print("=" * 78)
    print("ASK THE AGENT — SELECT among its three named learning gaps")
    print("=" * 78)
    sub = _build_mind()

    # LIVE proof: the shape library is the agent's own harvested concepts.
    shape_lib, mode = onp._resolve_shapes(sub, None)
    print(f"\n[LIVE] implication-shape library mode = '{mode}'  "
          f"(harvested from the agent's own concepts, NOT the frozen stencil)")
    print(f"[LIVE] harvested shape count = {len(shape_lib)}  "
          f"(hand stencil for contrast = {len(onp._shapes())})")
    posts = onp.harvest_postulates(sub)
    print(f"[LIVE] held order-0 postulates (breadth) = {len(posts)}")

    # (2) the agent derives its full gap-map from its own held postulates.
    print("\n[2] running synthesize_over_all (the agent's order-N derivative over "
          "every held postulate) ...")
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    # (3) the agent's OWN centrality/compression ranking (payoff = postulates unified).
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    axes = gp.build_axis_env(sub, shape_breadth=breadth)
    print(f"[3] CapabilityAxes built from the agent's synthesized gaps: {len(axes)}")
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    print("\n    AGENT RANKING (payoff = # held postulates UNIFIED; the agent's "
          "graph-resident compression Term):")
    for r in rows[:14]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>9}  level={lvl:<20} {r['capability_keys'][:3]}")

    # (4) which of the THREE named learning gaps does the ranking place highest?
    print("\n" + "-" * 78)
    print("[4] THE AGENT'S CHOICE among its three named LEARNING gaps")
    print("-" * 78)

    def best_row_for(needles):
        best = None
        for r in rows:
            keys = [str(k).lower() for k in r["capability_keys"]]
            if any(any(n in k for k in keys) for n in needles):
                if best is None or r["payoff"] > best["payoff"]:
                    best = r
        return best

    ranked_named = []
    for label, needles in LEARNING_GAPS.items():
        r = best_row_for(needles)
        payoff = r["payoff"] if r else -1
        ranked_named.append((payoff, label, r))
        if r:
            print(f"\n  {label}")
            print(f"     payoff (postulates UNIFIED) = {r['payoff']}   "
                  f"order = {r['min_order']}   score = {r['score']}")
            print(f"     capability_keys = {r['capability_keys'][:4]}")
            print(f"     source_concepts = {r.get('source_concepts', [])[:4]}")
        else:
            print(f"\n  {label}\n     (no synthesized axis matched its terms)")

    ranked_named.sort(key=lambda x: -x[0])
    print("\n" + "=" * 78)
    win_payoff, win_label, win_row = ranked_named[0]
    print(f"AGENT PICKS: {win_label}")
    print(f"   REASON (its own compression/centrality): this capability UNIFIES "
          f"{win_payoff} held postulates")
    print(f"   — the most of the three (it compresses the most of the agent's own "
          f"knowledge).")
    if win_row:
        # show the unified postulates if we can read them off the axis node
        ax = win_row.get("axis_id")
        if ax is not None:
            uni = [sub.node(n)["attrs"].get("name", n)
                   for n in sub.neighbours(ax, gp.UNIFIES_EDGE)]
            print(f"   postulates unified ({len(uni)}): {uni[:12]}")
    print("=" * 78)


if __name__ == "__main__":
    main()
