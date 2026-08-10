"""ASK THE AGENT its frontier — v3: WIRE THE UPGRADE then re-run the synthesizer.

Companion to scripts/agent_frontier_postLOSO593.py. That harness found (v2 doc) the
gap-synthesizer returned the STANDING frontier (cross-speaker clustering 83,
segmentation 28) because the session's five theory insights lived only in experiment
scripts — never registered as harvestable postulates. This harness wires the upgrade:
it installs the five insights as held postulates + harvestable Rules
(domains/recognition_combine.install_recognition_combine), VERIFIES the harvester now
sees them (shape count + insight terms before/after), then re-runs the SAME live
synthesize_gaps + gap_prioritiser.pick_frontier and reports whether the frontier MOVES.

Run:  python scripts/agent_frontier_v3_insights.py
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.code_authoring import _install_concept
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp
from domains.recognition_combine import install_recognition_combine, INSIGHTS

import scripts.agent_frontier_postLOSO593 as H


INSIGHT_TERMS = ["exclusion", "vector", "relaxation", "inadmissible",
                 "superposition", "commuting", "interference", "quantum",
                 "temperature", "out-of-box"]


def _build_mind():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _register_state(sub):
    mt = next(n for n in sub.nodes("Microtheory")
              if sub.node(n)["attrs"].get("name") == "speech_science")
    cid = _install_concept(sub, mt, H.POSTULATE_NAME, H.POSTULATE_DEFINITION)
    sub.set_attr(cid, "why", H.POSTULATE_WHY)
    sub.set_attr(cid, "origin", "frontier_state_postLOSO593")
    sub.set_attr(cid, "category", "self_state")
    return cid


def _scan_insight_terms(shape_lib):
    """Count shapes whose name/consequence/match_keys mention the insight terms."""
    hits = {}
    for sh in shape_lib:
        blob = (str(sh.get("name", "")) + " " + str(sh.get("consequence", ""))
                + " " + " ".join(map(str, sh.get("match_keys", [])))
                + " " + " ".join(map(str, sh.get("name_keys", [])))).lower()
        for t in INSIGHT_TERMS:
            if t in blob:
                hits[t] = hits.get(t, 0) + 1
    return hits


def main():
    print("=" * 80)
    print("ASK THE AGENT — v3: wire the upgrade (5 insights) then re-run synthesizer")
    print("=" * 80)

    # ------------------------------------------------------------------
    # BEFORE the upgrade — the harvestable shape library + insight-term scan.
    # ------------------------------------------------------------------
    sub = _build_mind()
    lib_before, mode = onp._resolve_shapes(sub, None)
    names_before = {s["name"] for s in lib_before}
    hits_before = _scan_insight_terms(lib_before)
    print(f"\n[BEFORE] harvested shapes = {len(lib_before)}  (mode='{mode}')")
    print(f"         insight-term hits in shape library: {hits_before or '{}'}")

    # ------------------------------------------------------------------
    # WIRE THE UPGRADE — install the 5 insights as held postulates + Rules.
    # ------------------------------------------------------------------
    install_recognition_combine(sub)
    cid = _register_state(sub)

    posts = {nm for _, nm, _ in onp.harvest_postulates(sub)}
    ins_names = {i["name"] for i in INSIGHTS}
    held = ins_names & posts
    print(f"\n[WIRED] installed recognition_combine Mt: 5 insight Concepts + 5 Rules")
    print(f"        insight Concepts now HELD as postulates: {len(held)}/5  {sorted(held)}")
    print(f"        post-LOSO state held? {H.POSTULATE_NAME in posts}  "
          f"(total postulates: {len(posts)})")

    lib_after, _ = onp._resolve_shapes(sub, None)
    names_after = {s["name"] for s in lib_after}
    new_shapes = names_after - names_before
    hits_after = _scan_insight_terms(lib_after)
    ins_rule_names = {f"rule_derived__{i['name']}__implication" for i in INSIGHTS}
    harvested = ins_rule_names & names_after

    print(f"\n[AFTER]  harvested shapes = {len(lib_after)}  "
          f"(+{len(lib_after) - len(lib_before)} = the 5 insight rule-shapes)")
    print(f"         insight rule-shapes harvested: {len(harvested)}/5")
    print(f"         insight-term hits in shape library: {hits_after}")

    # Do the new shapes FIRE on the post-LOSO state postulate?
    ptext = (H.POSTULATE_DEFINITION + " " + H.POSTULATE_WHY).lower()
    breadth = gp.shape_firing_breadth(sub, lib_after)
    n_post = len(onp.harvest_postulates(sub))
    cap = n_post * gp.PROMISCUITY_FRAC
    print(f"\n[FIRES?] do the insight shapes transfer onto the post-LOSO postulate? "
          f"(promiscuity cap = {cap:.1f})")
    for sh in lib_after:
        if sh["name"] in ins_rule_names:
            pats = sh.get("match_patterns", [])
            fired = bool(pats) and all(re.search(p, ptext) for p in pats)
            b = breadth.get(sh["name"], 0)
            tag = " PROMISCUOUS-gated" if b > cap else ""
            print(f"    {sh['name'].replace('rule_derived__', '').replace('__implication', ''):<35} "
                  f"fired={fired}  breadth={b}{tag}")

    # ------------------------------------------------------------------
    # RE-RUN the live synthesizer + prioritiser WITH the insights harvestable.
    # ------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[A1] order-N derivative of the post-LOSO postulate (prune=False = derived)")
    print("-" * 80)
    derived = onp.synthesize_gaps(sub, H.POSTULATE_NAME, max_order=3,
                                  shapes="harvested", prune=False, record=False)
    for g in derived:
        vs = [v.replace("rule_derived__", "").replace("__implication", "")
              for v in g["via_shapes"]]
        print(f"    order {g['order']} via {vs}: {g['capability_keys'][:4]}")

    print("\n" + "-" * 80)
    print("[A2] full gap-map + UNBIASED ranking (compression payoff, native Argmax)")
    print("-" * 80)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)
    breadth = gp.shape_firing_breadth(sub, lib_after)
    gp.build_axis_env(sub, shape_breadth=breadth)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    insight_keys = {kw for i in INSIGHTS for kw in
                    ("exclusion", "vector", "relaxation", "inadmissible",
                     "superposition")}
    for r in rows[:16]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        mark = "  <-- INSIGHT" if any(
            any(ik in str(k).lower() for ik in insight_keys)
            for k in r["capability_keys"]) else ""
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>8}  level={lvl:<22} {r['capability_keys'][:3]}{mark}")

    print("\n[A3] THE PICK (graph Argmax Term, native eval):")
    pick = gp.pick_frontier(sub, shape_breadth=breadth)
    if pick:
        print(f"    PICKED : {pick['capability_keys']}")
        print(f"    level  : {gp.axis_pipeline_level(pick['capability_keys'])[0]}")
        print(f"    payoff : {pick['postulates_unified']} "
              f"(runner-up {pick.get('runner_up_payoff')})")
        print(f"    gap    : {pick.get('gap_text', '')[:160]}")

    print("\n" + "=" * 80)
    print("VERDICT — did wiring the insights MOVE the frontier?")
    print("=" * 80)
    print("  STANDING pick (v2, no insights) : clustering [recognition] payoff 83, "
          "runner-up segmentation 28")
    if pick:
        moved = "cross-speaker" not in " ".join(pick["capability_keys"]).lower()
        print(f"  v3 pick (insights harvestable)  : {pick['capability_keys'][:3]} "
              f"[{gp.axis_pipeline_level(pick['capability_keys'])[0]}] payoff "
              f"{pick['postulates_unified']}")
        print(f"  FRONTIER MOVED? {moved}")
    print("=" * 80)


if __name__ == "__main__":
    main()
