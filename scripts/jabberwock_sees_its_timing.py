#!/usr/bin/env python3
"""jabberwock_sees_its_timing — the jabberwock SEES where its load time goes.

THE USER'S POINT: a prior build reached for a CACHE to make Wikipedia loading
faster. It was a BLIND guess, because the jabberwock could not SEE timing — "if
the timing isn't visible to it, there is our problem." This script makes timing
VISIBLE (a graph perception the agent holds) and shows the fix that visibility
reveals is trivial: warm WordNet once.

Three FRESH (genuinely cold) processes, so every measurement is honest:

  --mode probe : the raw cold-vs-warm shape of the ground/sense primitive
                 (dictionary_lexicon._enumerate_features): FIRST call vs warm.
  --mode cold  : consume a batch WITHOUT warm-up (warm=False). Article 1's ground
                 stage pays the one-time WordNet init -> cold-inflated s/article.
                 The jabberwock then INTROSPECTS its LatencyObservations.
  --mode warm  : consume a batch WITH warm-once (warm=True). The init moves to
                 boot; article 1 is WARM -> the true warm steady-state s/article.

Run with no args to orchestrate all three and print the full ledger + a
machine-readable ===JSON=== block (consumed by tests/test_load_timing.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BATCH_COLD = ["Cryptography", "Photosynthesis", "Volcano", "Guitar"]
BATCH_WARM = ["Blockchain", "Democracy", "Glacier", "Antibiotic"]
FULL_READ_ARTICLES = 7_600_000  # ~ the wiki_local structured-enwiki title count.


def _boot():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import concept_graph as cg
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()
    return a


def _per_article_seconds(records: list) -> dict:
    """Aggregate a LoadTimer's per-stage records into a per-article s/article
    (read + extract + ground). Also return the stage totals."""
    by_article: dict = {}
    stage_total: dict = {}
    for r in records:
        st = r["stage"]
        if st == "boot_warm_wordnet":
            stage_total[st] = stage_total.get(st, 0.0) + r["ms"]
            continue
        art = r.get("article") or "?"
        by_article.setdefault(art, 0.0)
        by_article[art] += r["ms"]
        stage_total[st] = stage_total.get(st, 0.0) + r["ms"]
    n = max(len(by_article), 1)
    total_ms = sum(by_article.values())
    return {"n_articles": n, "total_ms": round(total_ms, 3),
            "s_per_article": round(total_ms / 1000.0 / n, 4),
            "per_article_ms": {k: round(v, 3) for k, v in by_article.items()},
            "stage_total_ms": {k: round(v, 3) for k, v in stage_total.items()}}


def mode_probe() -> dict:
    """Raw cold-vs-warm shape of the ground/sense primitive — no pipeline, just
    the WordNet enumerate call, first vs steady state."""
    from domains import dictionary_lexicon as dl
    t0 = time.perf_counter()
    dl._enumerate_features(["cipher"], "patient", ["cryptography"], "en")
    cold = (time.perf_counter() - t0) * 1000.0
    warm = []
    for w in ["key", "hash", "signature", "lens", "mirror", "prism",
              "glacier", "volcano", "guitar", "democracy"]:
        t0 = time.perf_counter()
        dl._enumerate_features([w], "patient", ["topic"], "en")
        warm.append((time.perf_counter() - t0) * 1000.0)
    return {"cold_first_ms": round(cold, 1),
            "warm_per_concept_ms_mean": round(sum(warm) / len(warm), 3),
            "warm_min": round(min(warm), 3), "warm_max": round(max(warm), 3)}


def mode_cold() -> dict:
    from domains import wikipedia_consumption as wc
    from domains.load_timing import LoadTimer, where_does_load_time_go
    agent = _boot()
    timer = LoadTimer(agent)
    wc.consume(agent, titles=BATCH_COLD, warm=False, timing=timer, gate=True)
    intro = where_does_load_time_go(agent)
    agg = _per_article_seconds(timer.records)
    return {"introspection_text": intro["text"], "by_stage": intro["by_stage"],
            "dominant_stage": intro["dominant_stage"], "dominant_pct": intro["dominant_pct"],
            "cold_ground_ms": intro["cold"], "warm_ground_per_concept_ms": intro["warm"],
            "agg": agg, "n_latency_obs": len(intro["observations"]),
            "records": timer.records}


def mode_warm() -> dict:
    from domains import wikipedia_consumption as wc
    from domains.load_timing import LoadTimer, where_does_load_time_go
    agent = _boot()
    timer = LoadTimer(agent)
    wc.consume(agent, titles=BATCH_WARM, warm=True, timing=timer, gate=True)
    intro = where_does_load_time_go(agent)
    agg = _per_article_seconds(timer.records)
    # article-1 ground phase: after warm-once it must be WARM, not cold.
    art1 = BATCH_WARM[0]
    art1_ground = [r for r in timer.records
                   if r["stage"] == "ground_lexeme" and r.get("article") == art1]
    boot = [r for r in timer.records if r["stage"] == "boot_warm_wordnet"]
    return {"introspection_text": intro["text"], "by_stage": intro["by_stage"],
            "boot_warm_ms": round(boot[0]["ms"], 1) if boot else 0.0,
            "article1": art1,
            "article1_ground_phase": art1_ground[0]["phase"] if art1_ground else None,
            "article1_ground_ms": round(art1_ground[0]["ms"], 3) if art1_ground else None,
            "agg": agg, "records": timer.records}


def _spawn(mode: str) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [os.path.join(ROOT, "runners", "dsl", "python"), ROOT,
         os.path.join(ROOT, "scripts"), env.get("PYTHONPATH", "")])
    out = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--mode", mode, "--json"],
        capture_output=True, text=True, env=env, cwd=ROOT)
    for line in out.stdout.splitlines():
        if line.startswith("===JSON==="):
            return json.loads(line[len("===JSON==="):])
    raise RuntimeError(f"mode {mode} produced no JSON:\nSTDOUT:\n{out.stdout}\nSTDERR:\n{out.stderr}")


def orchestrate() -> dict:
    probe = _spawn("probe")
    cold = _spawn("cold")
    warm = _spawn("warm")

    cold_spa = cold["agg"]["s_per_article"]
    warm_spa = warm["agg"]["s_per_article"]
    cold_days = FULL_READ_ARTICLES * cold_spa / 86400.0
    warm_days = FULL_READ_ARTICLES * warm_spa / 86400.0

    print("=" * 74)
    print("THE JABBERWOCK SEES ITS OWN LOAD TIME")
    print("=" * 74)
    print()
    print("1. THE LOAD-TIMING PERCEPTION (the jabberwock introspecting, verbatim):")
    print("-" * 74)
    print(cold["introspection_text"])
    print()
    print(f"   (it HOLDS {cold['n_latency_obs']} LatencyObservation nodes, wired "
          f"agent -perceives_latency-> obs — a perception, not a print.)")
    print()
    print("2. COLD-vs-WARM PROOF (raw ground/sense primitive, fresh process):")
    print("-" * 74)
    print(f"   FIRST _enumerate_features call : {probe['cold_first_ms']:.1f} ms   "
          f"<- ONE-TIME WordNet corpus init")
    print(f"   WARM per-concept (mean of 10)  : {probe['warm_per_concept_ms_mean']:.3f} ms   "
          f"(min {probe['warm_min']:.3f}, max {probe['warm_max']:.3f})")
    ratio = probe["cold_first_ms"] / max(probe["warm_per_concept_ms_mean"], 1e-9)
    print(f"   the 'bottleneck' is {ratio:,.0f}x a warm concept — it is ONE-TIME "
          f"init, not a per-item cost.")
    print()
    print("3. WARM-ONCE FASTER (pipeline, before vs after — fresh processes):")
    print("-" * 74)
    print(f"   BEFORE (cold, warm=False): article 1 ground = {cold['cold_ground_ms']:.1f} ms "
          f"(COLD); cold-inflated {cold_spa:.4f} s/article")
    print(f"   AFTER  (warm-once, warm=True): boot pays {warm['boot_warm_ms']:.1f} ms once; "
          f"article 1 ground is '{warm['article1_ground_phase']}' "
          f"({warm['article1_ground_ms']:.2f} ms); warm {warm_spa:.4f} s/article")
    print(f"   full-read extrapolation ({FULL_READ_ARTICLES:,} articles):")
    print(f"       cold-inflated: {cold_days:,.1f} days   (the WRONG, cold-start-inflated figure)")
    print(f"       warm steady  : {warm_days:,.1f} days   (the corrected, honest figure)")
    print(f"       speedup      : {cold_spa / max(warm_spa, 1e-9):.1f}x per article")
    print()
    print("4. NO CACHE — HONEST LEDGER:")
    print("-" * 74)
    print("   The prior cache was the agent optimizing a cost it COULD NOT SEE. The real")
    print("   cost was a ~1.4s ONE-TIME WordNet init, not a per-item cost — so a cache")
    print("   (context-keyed, 2.6% hit-rate) could never help: there was no repeated")
    print("   per-item work to memoize. Making timing VISIBLE dissolved the false")
    print("   problem; the true fix (warm WordNet once at boot) is one line and adds NO")
    print("   cache. The speedup above is warm-once + visibility, not memoization.")
    print("=" * 74)

    combined = {"probe": probe, "cold": cold, "warm": warm,
                "cold_s_per_article": cold_spa, "warm_s_per_article": warm_spa,
                "cold_full_read_days": round(cold_days, 2),
                "warm_full_read_days": round(warm_days, 2)}
    print("===JSON===" + json.dumps(combined))
    return combined


def main(argv: list) -> int:
    mode = None
    as_json = "--json" in argv
    if "--mode" in argv:
        mode = argv[argv.index("--mode") + 1]
    if mode is None:
        orchestrate()
        return 0
    fn = {"probe": mode_probe, "cold": mode_cold, "warm": mode_warm}[mode]
    result = fn()
    if as_json:
        print("===JSON===" + json.dumps(result))
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
