"""ASSESS -> DECIDE — the agent surveys its CURRENT speech state (the confirmed
post-wall relational-invariance findings, banked as order-0 postulates it HOLDS)
and ranks its own synthesized gaps by ITS OWN compression payoff Term, natively.

NO reasoning lives here. The shell:
  (1) builds the mind at full breadth AND installs the CONFIRMED findings
      (relational_invariance_findings) so the gap machinery derives from where
      the agent ACTUALLY is (post-wall), not the pre-relational speech_science map;
  (2) runs the LIVE gap machinery (order_n_postulates.synthesize_over_all over the
      agent's own harvested implication-shapes) on its held postulates;
  (3) reads the agent's OWN graph-resident compression ranking (gap_prioritiser:
      payoff = # held postulates a capability UNIFIES, evaluated natively) and
      prints the ranking, restricted to the findings Mt so the CURRENT frontier
      surfaces (not the long-closed pre-relational gaps);
  (4) prints the agent's TOP pick + the postulates it unifies = its CHOICE + REASON.

The choice is the agent's (its payoff Term over its own derivation graph). The shell
only invokes + prints. Run: python scripts/agent_improves_speech_decide.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains.phonology import install_phonology
from domains.speech_science import install_speech_science
from domains.concept_expansions import install_all_concept_expansions
from domains.relational_invariance_findings import (
    install_relational_invariance_findings)
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp

FINDINGS_MT = "relational_invariance_findings"


def _build_mind():
    sub = Substrate()
    install_phonology(sub)
    install_speech_science(sub)
    install_all_concept_expansions(sub)
    # THE CURRENT STATE — the confirmed post-wall findings as held order-0 postulates.
    install_relational_invariance_findings(sub)
    return sub


def main():
    print("=" * 78)
    print("ASSESS -> DECIDE : the agent ranks its own next move to improve speech")
    print("=" * 78)
    sub = _build_mind()

    shape_lib, mode = onp._resolve_shapes(sub, None)
    posts = onp.harvest_postulates(sub)
    findings = onp.harvest_postulates(sub, FINDINGS_MT)
    print(f"\n[LIVE] implication-shape library mode = '{mode}'  "
          f"(harvested from the agent's own concepts)")
    print(f"[LIVE] harvested shape count = {len(shape_lib)}")
    print(f"[LIVE] held order-0 postulates (full breadth) = {len(posts)}")
    print(f"[LIVE] of which CONFIRMED-findings postulates = {len(findings)}:")
    for _, nm, _ in findings:
        print(f"         - {nm}")

    print("\n[2] synthesize_over_all (order-N derivative over every held postulate)...")
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    breadth = gp.shape_firing_breadth(sub, shape_lib)
    gp.build_axis_env(sub, shape_breadth=breadth)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)

    # Restrict to axes whose gaps derive FROM the confirmed-findings postulates —
    # the agent's CURRENT frontier. (A gap's source_concepts records the postulate
    # that derived it; we keep axes touching any findings postulate.)
    finding_names = {nm for _, nm, _ in findings}

    def from_findings(r):
        srcc = {str(c) for c in r.get("source_concepts", [])}
        return bool(srcc & finding_names)

    cur = [r for r in rows if from_findings(r)]
    print(f"\n[3] CapabilityAxes from the CONFIRMED-findings postulates: {len(cur)}")
    print("    AGENT RANKING (payoff = # held postulates UNIFIED; graph-resident "
          "compression Term, evaluated natively):")
    for r in cur[:18]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>9}  level={lvl:<18} keys={r['capability_keys'][:3]}")
        print(f"             from: {sorted(set(r.get('source_concepts', [])) & finding_names)}")

    print("\n" + "=" * 78)
    if not cur:
        print("NO findings-derived axis surfaced — falling back to global top.")
        cur = rows
    win = cur[0]
    lvl, _ = gp.axis_pipeline_level(win["capability_keys"])
    print(f"AGENT PICKS (top of its own compression ranking):")
    print(f"   capability_keys = {win['capability_keys']}")
    print(f"   pipeline level  = {lvl}")
    print(f"   payoff (held postulates UNIFIED) = {win['payoff']}   "
          f"order = {win['min_order']}   score = {win['score']}")
    print(f"   gap_text = {win.get('gap_text','')[:300]}")
    ax = win.get("axis_id")
    if ax is not None:
        uni = [sub.node(n)["attrs"].get("name", n)
               for n in sub.neighbours(ax, gp.UNIFIES_EDGE)]
        print(f"   postulates unified ({len(uni)}): {uni[:14]}")
    print("   REASON: this capability compresses the most of the agent's own held "
          "knowledge (highest payoff in its native ranking Term).")
    print("=" * 78)


if __name__ == "__main__":
    main()
