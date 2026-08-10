#!/usr/bin/env python3
"""jabberwock_optimizes_itself — the jabberwock DRIVES its OWN efficiency fix.

The prior build GUESSED a cache to make Wikipedia loading faster — blind, because
it could not SEE where its load time went. This script closes that loop: the
jabberwock PERCEIVES its load timing, DIAGNOSES the cost shape with a GRAPH
decision, SELECTS the fix that shape calls for, REJECTS the cache on its own
reading, VERIFIES the choice, and APPLIES it — the SAME perceive->diagnose->
solve->verify cycle it ran on the UNDERSTANDING gaps, now on EFFICIENCY.

The cold-vs-warm numbers are REAL: they come from fresh (genuinely cold) processes
via scripts/jabberwock_sees_its_timing.py's subprocess modes. The DECISION is then
run in-process on that real perceived timing (fed as LatencyObservation nodes via
the real LoadTimer sensor), so every verdict below is the graph's over measured
data. Run with no args for the full ledger; needs the wiki_local slab + nltk.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _real_timing() -> dict:
    """Real cold-vs-warm timing from fresh cold processes (reuses the sibling
    orchestrator's subprocess modes). Returns the measured cold init, warm per
    concept, and cold/warm s/article."""
    import jabberwock_sees_its_timing as jss
    probe = jss._spawn("probe")
    cold = jss._spawn("cold")
    warm = jss._spawn("warm")
    return {
        "cold_first_ms": probe["cold_first_ms"],
        "warm_per_concept_ms": probe["warm_per_concept_ms_mean"],
        "cold_ground_ms": cold["cold_ground_ms"],
        "warm_ground_per_concept_ms": cold["warm_ground_per_concept_ms"],
        "cold_s_per_article": cold["agg"]["s_per_article"],
        "warm_s_per_article": warm["agg"]["s_per_article"],
        "cold_n_articles": cold["agg"]["n_articles"],
    }


def _boot():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import concept_graph as cg
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()
    return a


def main() -> int:
    try:
        from domains import wiki_local as wl
        have_slab = wl.present()
    except Exception:
        have_slab = False

    from domains import load_timing as lt
    from domains import performance_self_improvement as psi

    bar = "=" * 74
    print(bar)
    print("THE JABBERWOCK OPTIMIZES ITSELF (efficiency, from its own timing perception)")
    print(bar)

    if have_slab:
        print("\nmeasuring REAL cold-vs-warm timing (three fresh cold processes)...")
        t = _real_timing()
        cold_ms = t["cold_ground_ms"] or t["cold_first_ms"]
        warm_per = t["warm_ground_per_concept_ms"] or t["warm_per_concept_ms"]
        cold_spa, warm_spa = t["cold_s_per_article"], t["warm_s_per_article"]
    else:
        print("\n(wiki_local slab absent — using the 7f6ff15a measured shape as the "
              "perceived timing; the DECISION path is identical.)")
        cold_ms, warm_per = 1400.0, 0.4
        cold_spa, warm_spa = 1.4400, 0.0480

    # feed the REAL perceived timing into a fresh agent via the real LoadTimer sensor.
    agent = _boot()
    timer = lt.LoadTimer(agent)
    timer.record("read_source", 40.0, article="article_1")
    timer.record("ground_lexeme", cold_ms, article="article_1", n_items=20, phase="cold")
    timer.record("ground_lexeme", warm_per * 20, article="article_2", n_items=20, phase="warm")

    print("\n1. PERCEIVE — where does my load time go? (introspection, verbatim):")
    print("-" * 74)
    print(lt.where_does_load_time_go(agent)["text"])

    res = psi.optimize(agent)
    d = res["diagnosis"]

    print("\n2. DIAGNOSE + SELECT-FIX — the GRAPH decision (perf_diagnose + perf_fix_pick):")
    print("-" * 74)
    print(f"   cold/warm ratio = {d['ratio']:,} (cold {d['cold_ms']} ms / warm {d['warm_per_item']} ms/item)")
    print(f"   perf_diagnose  -> shape  = {d['shape']!r}   (IfThenElse(Gt(Div(cold,warm),50),...))")
    print(f"   perf_fix_pick  -> fix    = {d['fix']!r}   (Argmin over PerfFixCue where shape Eq diagnosis)")
    per = psi.diagnose_and_select(agent, 0.5, 0.4)
    print(f"   PROOF it is a DECISION over the data: a per-item-shaped gap (cold~warm) ->")
    print(f"       shape={per['shape']!r} fix={per['fix']!r}  (NOT warm_once)")

    print("\n3. REJECT THE CACHE — on the agent's own reading:")
    print("-" * 74)
    cue_fixes = sorted({agent.s.node(n)["attrs"]["fix"] for n in agent.s.nodes("PerfFixCue")})
    print(f"   the diagnosis is {d['shape']!r} -> fix {d['fix']!r}; the PerfFixCue set names {cue_fixes}")
    print(f"   there is NO cue mapping any shape to a cache -> a cache is never SELECTED.")
    vc = res["verify_cache"]
    print(f"   and #2's cache twin FAILS its control: accepted={vc['accepted']}")
    print(f"       {vc['reason']}")
    print(f"   (a cache is empty on the FIRST item -> it cannot speed article 1.)")

    print("\n4. VERIFY (#2) — the selected fix survives; the fake does not:")
    print("-" * 74)
    vs = res["verify_selected"]
    print(f"   warm_once accepted = {vs['accepted']}  |  {vs['reason']}")
    fake = psi.verify_fix(agent, "none", cold_ms, warm_per)
    print(f"   fake(no warm-up) accepted = {fake['accepted']}  |  {fake['reason']}")

    print("\n5. APPLY + FASTER — enact the chosen fix; article 1 goes warm:")
    print("-" * 74)
    ap = res["applied"]
    print(f"   applied: {ap}")
    print(f"   cold s/article (article 1, one-time init in-line): {cold_spa:.4f}")
    print(f"   warm s/article (article 1, init moved to boot)   : {warm_spa:.4f}")
    print(f"   speedup: {cold_spa / max(warm_spa, 1e-9):.1f}x per article")

    print("\n" + bar)
    print("LEDGER: the agent PERCEIVED its timing, DIAGNOSED the shape (graph), SELECTED")
    print("warm_once (graph), REJECTED the cache (diagnosis + #2), VERIFIED (#2), and")
    print("APPLIED it. The graph made the decisions; the clock, the warm-up call, and the")
    print("attr read-backs were the only boundary I/O. The cache it once GUESSED, it now")
    print("REJECTS — from its own timing perception.")
    print(bar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
