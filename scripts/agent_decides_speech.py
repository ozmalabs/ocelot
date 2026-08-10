"""agent_decides_speech — STEP 1 bank the session's confirmed findings as held
order-0 postulates; STEP 2 run the AGENT'S OWN decision machinery over its now-
updated state and report what IT chose, with the selector's actual values.

NO decision lives in this shell. It:
  (1) builds the mind (full breadth -> the harvested implication-shape library is
      the agent's OWN concepts), then BANKS the session findings as Concepts
      (postulates) under the relational_invariance_findings Mt;
  (2) runs the LIVE order-N derivative (order_n_postulates.synthesize_over_all)
      over EVERY held postulate, so the agent derives the next-capability gaps;
  (3) reads the agent's OWN compression selector (gap_prioritiser.rank_gaps:
      payoff = # held postulates a capability UNIFIES, evaluated natively as a
      graph Term) and prints the full ranking with values;
  (4) enacts the agent's PICK natively (gap_prioritiser.pick_frontier — an
      Argmax graph Rule) and reports the #1 with its score + runner-up margin;
  (5) shows which axes the NEWLY-BANKED findings surfaced (BEFORE vs AFTER),
      so it is auditable that banking the findings changed what the agent's
      selector saw — and HONEST about derived-vs-scaffolded.

Run: python scripts/agent_decides_speech.py
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
from domains.relational_invariance_findings import (
    install_relational_invariance_findings)
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp


def _build_mind():
    sub = Substrate()
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _rank(sub, label):
    """Run the agent's order-N derivative + native compression ranker, return rows."""
    shape_lib, _mode = onp._resolve_shapes(sub, None)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    gp.build_axis_env(sub, shape_breadth=breadth)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    return rows, breadth


def _axis_sig(row):
    return frozenset(str(k).lower() for k in row["capability_keys"])


def main():
    print("=" * 78)
    print("AGENT DECIDES SPEECH — bank the findings, then the agent's selector picks")
    print("=" * 78)

    # ---- BEFORE: the agent's ranking WITHOUT the session findings banked. ----
    sub0 = _build_mind()
    posts0 = onp.harvest_postulates(sub0)
    rows0, _ = _rank(sub0, "before")
    sig_before = {_axis_sig(r) for r in rows0}
    print(f"\n[BEFORE banking] held postulates = {len(posts0)}   "
          f"capability-axes synthesized = {len(rows0)}")

    # ---- STEP 1: BANK the findings as held order-0 postulates. ----
    sub = _build_mind()
    banked = install_relational_invariance_findings(sub)
    n_banked = len([k for k in banked if not k.startswith("_")])
    print("\n" + "-" * 78)
    print(f"STEP 1 — BANKED the session findings: {n_banked} order-0 postulates "
          f"under the 'relational_invariance_findings' Mt")
    for k in banked:
        if k.startswith("_"):
            continue
        cat = sub.node(banked[k])["attrs"].get("category", "")
        print(f"    + {k:<48} [{cat}]")

    # ---- STEP 2: the agent's OWN decision machinery over the updated state. ----
    posts = onp.harvest_postulates(sub)
    rows, breadth = _rank(sub, "after")
    sig_after = {_axis_sig(r) for r in rows}
    print("\n" + "-" * 78)
    print(f"STEP 2 — the agent derives + ranks. held postulates = {len(posts)} "
          f"(+{len(posts) - len(posts0)})   capability-axes = {len(rows)}")

    print("\n  AGENT RANKING (payoff = # held postulates UNIFIED, a graph Term "
          "evaluated natively; tie-break shallower order; score = payoff*K - order):")
    new_sigs = sig_after - sig_before
    for r in rows[:24]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        is_new = "  <== NEW (surfaced by the banked findings)" \
            if _axis_sig(r) in new_sigs else ""
        print(f"    payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>9}  level={lvl:<20} "
              f"{r['capability_keys'][:3]}{is_new}")

    # ---- the agent ENACTS its pick natively (Argmax graph Rule). ----
    print("\n" + "-" * 78)
    print("THE AGENT'S PICK — enacted natively (gap_prioritiser.pick_frontier, an "
          "Argmax graph Rule over CapabilityAxis of payoff*K - order)")
    print("-" * 78)
    win = gp.pick_frontier(sub, shape_breadth=breadth)
    if win is None:
        print("  (no axes — nothing synthesized)")
        return
    lvl, _ = gp.axis_pipeline_level(win["capability_keys"])
    print(f"  PICK: {win['capability_keys'][:4]}")
    print(f"     pipeline level     = {lvl}")
    print(f"     payoff (UNIFIES)   = {win['payoff']} held postulates")
    print(f"     min derivation ord = {win['min_order']}")
    print(f"     score              = {win['score']}")
    print(f"     runner-up payoff   = {win['runner_up_payoff']}")
    print(f"     criterion          = {win['criterion']}")
    ax = win.get("axis_id")
    if ax is not None:
        uni = [sub.node(n)["attrs"].get("name", n)
               for n in sub.neighbours(ax, gp.UNIFIES_EDGE)]
        print(f"     postulates unified ({len(uni)}): {uni[:14]}")

    # ---- which of the directive's candidate directions did the agent surface, and
    #      how does its selector rank them among each other? (auditable, no pick.) --
    print("\n" + "-" * 78)
    print("CANDIDATE DIRECTIONS — how the agent's selector ranked each (its values)")
    print("-" * 78)
    CANDIDATES = {
        "SCALE the coherent decoder (continuous / large-vocab)":
            ("continuous", "large-vocab", "scale"),
        "SUB-LEXICAL COMPOSITION (units composed into words)":
            ("compositional generation", "production-space search",
             "compose-under-selection", "compose", "production"),
        "GENERATIVE / COLLAPSE recovery (invert production)":
            ("analysis-by-synthesis", "articulatory forward model",
             "internal synthesiser", "forward model"),
        "LIBRARY + ROUTER (decode-configs routed by circumstance)":
            ("library", "router", "route", "config"),
        "QUANTIZE to discrete coherent categories":
            ("categorical quantiser", "learned decision boundary",
             "continuous-to-discrete category map"),
        "TOP-DOWN restoration / lexical-prediction completion":
            ("top-down restoration", "lexical-prediction fill-in",
             "context-predictive completion"),
        "RATIO / scale-cancellation (carrier normalisation)":
            ("speaker normalization", "formant ratio",
             "vocal-tract-length normalization"),
    }

    def best_row_for(needles):
        best = None
        for r in rows:
            keys = [str(k).lower() for k in r["capability_keys"]]
            if any(any(n in k for k in keys) for n in needles):
                if best is None or r["payoff"] > best["payoff"]:
                    best = r
        return best

    ranked = []
    for label, needles in CANDIDATES.items():
        r = best_row_for(needles)
        ranked.append((r["payoff"] if r else -1, label, r))
    ranked.sort(key=lambda x: -x[0])
    for payoff, label, r in ranked:
        if r:
            print(f"  payoff={r['payoff']:>3} score={r['score']:>9}  {label}")
            print(f"           keys={r['capability_keys'][:3]}  "
                  f"order={r['min_order']}")
        else:
            print(f"  payoff= -- (no synthesized axis matched)  {label}")

    print("\n" + "=" * 78)
    print("AGENT'S #1 (its compression selector): "
          f"{win['capability_keys'][:3]} @ level={lvl}, "
          f"payoff={win['payoff']}, score={win['score']}")
    print("=" * 78)


if __name__ == "__main__":
    main()
