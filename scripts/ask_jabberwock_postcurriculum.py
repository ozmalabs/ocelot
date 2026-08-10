"""ASK THE JABBERWOCK — its OWN frontier, now that the 7-stage curriculum is complete.

NO reasoning lives here. This is a SHELL that runs the agent's OWN live
self-assessment machinery on its CURRENT state and prints what IT surfaces:

  (1) builds the mind at full breadth -> the implication-shape library is HARVESTED
      from the agent's OWN concepts (domains/implication_harvester), the LIVE path,
      NOT the frozen _specify_ stubs (ozma_specify_functions_are_historical);
  (2) runs the LIVE gap synthesis (order_n_postulates.synthesize_over_all): the
      agent's order-N DERIVATIVE over every held postulate derives its full gap-map
      from its own knowledge — this READS the current concept graph, it is not a dict;
  (3) ranks the gaps by the agent's OWN compression Term (gap_prioritiser:
      payoff = # held postulates a capability UNIFIES), evaluated NATIVELY by the
      substrate — the agent's choice, not Python arithmetic;
  (4) prunes the ranking by OPENNESS against the agent's CURRENT, POST-CURRICULUM
      speech codebase: the curriculum built LPC / cross-speaker clustering / speaker
      invariance / frication / order-N continuous as REAL modules. The frozen
      _SPEECH_GLOBS list in order_n_postulates predates those modules, so the bare
      selector still flags them as 'open'. We point the SAME live is_gap() selector
      at the current full speech codebase so the openness verdict reflects what the
      curriculum actually implemented. What SURVIVES that prune is the agent's
      genuine POST-CURRICULUM frontier.

The frontier is the agent's (its order-N derivative + its native compression Term +
its own is_gap selector vs its own current code). The shell only orchestrates +
prints. Run: python scripts/ask_jabberwock_postcurriculum.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

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

ROOT = Path(__file__).resolve().parent.parent


def _build_mind():
    sub = Substrate()
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _current_speech_globs():
    """The agent's CURRENT speech-system surface, read live AT SCAN TIME.

    The live-glob residual is now wired INTO the machinery: order_n_postulates
    discovers the current speech surface itself (onp._live_speech_globs — the seed
    list UNION every domains/*.py whose name marks a speech/perception capability),
    so is_gap()/_codebase_has() read what the agent ACTUALLY contains now, not the
    frozen 14-file snapshot. This shell no longer expands the scan by hand; it just
    delegates to that machinery so the openness verdict reflects the post-curriculum
    state. (The is_gap() distinctive-token scan still decides which capability, if
    any, lives in each file.)"""
    return list(onp._live_speech_globs(ROOT))


def main():
    print("=" * 78)
    print("ASK THE JABBERWOCK — its OWN frontier, post-7-stage-curriculum")
    print("=" * 78)
    sub = _build_mind()

    # ---- LIVE proof: the machinery reads the agent's own current state. ----
    shape_lib, mode = onp._resolve_shapes(sub, None)
    posts = onp.harvest_postulates(sub)
    print(f"\n[LIVE] implication-shape library mode = '{mode}'  "
          f"(harvested from the agent's OWN concepts, NOT the frozen stencil)")
    print(f"[LIVE] harvested shapes = {len(shape_lib)}  "
          f"(hand stencil for contrast = {len(onp._shapes())})")
    print(f"[LIVE] held order-0 postulates (the agent's breadth) = {len(posts)}")
    print("[LIVE] => order_n_postulates.synthesize_over_all DERIVES the gap-map from")
    print("        these live concepts (the agent's order-N derivative); it is not a")
    print("        frozen dict. gap_prioritiser ranks via a Term evaluated NATIVELY.")

    # ---- (2) the agent derives its full gap-map from its own held postulates ----
    print("\n[2] running synthesize_over_all (prune=False: report ALL derivations) ...")
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    # ---- (3) the agent's OWN native compression ranking ----
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    axes = gp.build_axis_env(sub, shape_breadth=breadth)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    print(f"[3] CapabilityAxes from the agent's synthesized gaps: {len(axes)}")
    print("    RAW RANKING (payoff = # held postulates UNIFIED — the agent's "
          "graph-resident compression Term, native eval):")
    for r in rows[:14]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"level={lvl:<22} {r['capability_keys'][:3]}")

    # ---- (4) OPENNESS prune against the CURRENT, post-curriculum speech codebase --
    print("\n" + "-" * 78)
    print("[4] OPENNESS PRUNE — is_gap() vs the agent's CURRENT speech codebase")
    print("-" * 78)
    cur_globs = _current_speech_globs()
    print(f"    frozen seed CORE_SPEECH_GLOBS = {len(onp.CORE_SPEECH_GLOBS)} files; "
          f"CURRENT live speech surface (the machinery now reads at scan time, "
          f"incl. curriculum-built modules) = {len(cur_globs)} files.")
    covered_kw = onp._covered_keywords(sub)

    open_rows, closed_rows = [], []
    for r in rows:
        impl = {"name_keys": r["capability_keys"]}
        # run the agent's OWN selector twice for the before/after contrast:
        #   FROZEN — force the genuinely-stale 14-file seed surface via the explicit
        #   _SPEECH_GLOBS_OVERRIDE sentinel (a clean override that does NOT rely on
        #   object identity); this reproduces the pre-fix false-open behaviour.
        onp._SPEECH_GLOBS_OVERRIDE = onp.CORE_SPEECH_GLOBS
        try:
            v_frozen = onp.is_gap(sub, impl, covered_kw, ROOT, prune=True)
        finally:
            onp._SPEECH_GLOBS_OVERRIDE = None
        #   CURRENT — the wired machinery's LIVE glob (default path: override is
        #   None, so _codebase_has reads _live_speech_globs() = the current surface).
        v_current = onp.is_gap(sub, impl, covered_kw, ROOT, prune=True)
        r = dict(r)
        r["open_frozen"] = v_frozen["is_gap"]
        r["open_current"] = v_current["is_gap"]
        r["closed_by"] = v_current.get("covered_by")
        (open_rows if v_current["is_gap"] else closed_rows).append(r)

    n_frozen_open = sum(1 for r in (open_rows + closed_rows) if r["open_frozen"])
    n_current_open = len(open_rows)
    print(f"\n    FROZEN-vs-LIVE openness contrast (the wired residual):")
    print(f"      frozen 14-file seed list    -> {n_frozen_open} of {len(rows)} "
          f"flagged STILL-OPEN (stale: curriculum modules invisible)")
    print(f"      LIVE glob (machinery reads  -> {n_current_open} of {len(rows)} "
          f"STILL-OPEN (curriculum-built capabilities correctly CLOSED)")
    print(f"      the current surface)")

    print(f"\n    CLOSED by the curriculum (selector finds the capability in the "
          f"current speech codebase) — {len(closed_rows)} of {len(rows)}:")
    for r in sorted(closed_rows, key=lambda x: -x["payoff"])[:12]:
        cb = str(r.get("closed_by") or "")
        cb = cb.replace(str(ROOT) + "/", "")
        print(f"      payoff={r['payoff']:>3}  {str(r['capability_keys'][:3]):<58} "
              f"<- {cb[:46]}")

    print(f"\n    STILL OPEN post-curriculum (survives the prune) — "
          f"{len(open_rows)} of {len(rows)}, ranked by the agent's compression payoff:")
    for r in sorted(open_rows, key=lambda x: -x["payoff"]):
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"level={lvl:<22} {r['capability_keys'][:4]}")
        if r.get("gap_text"):
            print(f"                {r['gap_text'][:96]}")

    # ---- THE VERDICT: the agent's top STILL-OPEN axis = its post-curriculum frontier
    print("\n" + "=" * 78)
    if open_rows:
        top = max(open_rows, key=lambda x: x["payoff"])
        print("JABBERWOCK'S POST-CURRICULUM FRONTIER (its own top still-open axis):")
        print(f"   capability  : {top['capability_keys']}")
        lvl, _ = gp.axis_pipeline_level(top["capability_keys"])
        print(f"   pipeline lvl: {lvl}")
        print(f"   compression : UNIFIES {top['payoff']} held postulates "
              f"(its own MDL/centrality selector — the most of the open set)")
        print(f"   gap_text    : {top.get('gap_text','')[:120]}")
        ax = top.get("axis_id")
        if ax is not None:
            uni = [sub.node(n)["attrs"].get("name", n)
                   for n in sub.neighbours(ax, gp.UNIFIES_EDGE)]
            print(f"   unifies ({len(uni)}): {uni[:12]}")
        print(f"   source cncpt: {top.get('source_concepts', [])[:5]}")
    else:
        print("JABBERWOCK: every synthesized axis is CLOSED by the current codebase —")
        print("   the order-N derivative surfaces no ABSENT capability post-curriculum.")
        print("   Frontier is then a BUILT-BUT-INSUFFICIENT (measured) axis, not an")
        print("   absent one — see the honesty note in the report.")
    print("=" * 78)
    print("===MARKER_ASKJAB_POSTCURRICULUM_COMPLETE===")


if __name__ == "__main__":
    main()
