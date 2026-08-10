#!/usr/bin/env python3
"""jabberwock_consumes_wikipedia — the WIKIPEDIA CONSUMPTION PIPELINE, driven on REAL articles.

Self-improvement #3 grounded ONE microtheory from ONE Wikipedia article. This drives the SAME loop over
a BATCH of real wiki_local articles, grounding per article: a LEXICON (POS-typed + defined concepts),
ASSOCIATED MACHINERY (part_of relations + POS + morphology), and a MICROTHEORY (topic + has_concept
edges) — every object EARNED from the article, ADMISSIBILITY-GATED, and SOURCE-TRACED, to an ISOLATED
seeds dir (so the global boot is unperturbed). donkey=0.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_consumes_wikipedia.py
"""
from __future__ import annotations

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import wikipedia_consumption as wc
from domains import wiki_local as wl
from domains import concept_graph as cg


def main() -> int:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds

    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()

    print("=" * 78)
    print("WIKIPEDIA CONSUMPTION PIPELINE — batch-scale gap-driven acquisition (donkey=0)")
    print("=" * 78)
    print(f"wiki_local present: {wl.present()}", flush=True)
    if not wl.present():
        print("  (local slab absent — run with the structured-enwiki dump present)")
        return 1

    seeds_dir = tempfile.mkdtemp(prefix="wc_demo_")
    batch = wc.DEFAULT_BATCH
    print(f"batch (N={len(batch)} real articles): {batch}")
    print(f"isolated acquired seeds -> {seeds_dir}\n", flush=True)

    rep = wc.consume(a, titles=batch, seeds_dir=seeds_dir)

    print("--- CONSUMES A BATCH (before -> after) ---")
    print(f"  concepts:      {rep['before']['concepts']:>6} -> {rep['after']['concepts']:>6}  "
          f"(+{rep['growth']['concepts']} grounded)")
    print(f"  microtheories: {rep['before']['microtheories']:>6} -> {rep['after']['microtheories']:>6}  "
          f"(+{rep['growth']['microtheories']} minted)")
    print(f"  lexemes admitted: {rep['admitted_total']}   rejected by gate: {rep['rejected_total']}")
    print(f"  topics grown (now edge-learnable): {rep['microtheories_grown']}\n")

    print("--- PER ARTICLE (coverage rose = edge-bearing) ---")
    for r in rep["results"]:
        if r["consumed"]:
            print(f"  {r['title']:16s} admit={r['n_admitted']:>2} rej={r['n_rejected']:>2}  "
                  f"bag {r['before']['bag']:>2}->{r['after']['bag']:<3} "
                  f"cos {r['before']['best']:.3f}->{r['after']['best']:.3f}")
        else:
            print(f"  {r['title']:16s} NOT consumed: {r['reason']}")

    # GROUNDED-LEXICON sample — POS + definition + relation, verified vs the article.
    first = next((r for r in rep["results"] if r["consumed"]), None)
    if first:
        print(f"\n--- GROUNDED LEXICON sample ('{first['title']}') — POS + def + relation, source-traced ---")
        for lex in first["admitted"][:5]:
            print(f"  {lex['name']:24s} pos={str(lex['pos']):8s} ({lex['pos_source']})  "
                  f"part_of={lex['part_of']}")
            print(f"       def: {lex['definition'][:90]}")
        # ADMISSIBILITY TEETH — the rejected extractions (honest quality).
        if first["rejected"]:
            print(f"\n--- ADMISSIBILITY TEETH ('{first['title']}') — gate REJECTED (not installed) ---")
            for rej in first["rejected"][:6]:
                print(f"  REJECTED {rej['name']:24s} (ungrounded / does not trace)")

    # BOOT UNPERTURBED — a fresh boot still sees the topics as gaps (acquired seeds isolated).
    fresh = WorldAdapter(seeds=())
    load_all_seeds(fresh)
    cg._CACHE.clear()
    from domains import gap_driven_acquisition as gda
    still_gap = [t for t in rep["microtheories_grown"] if gda.is_knowledge_gap(fresh, t)]
    print(f"\n--- BOOT UNPERTURBED ---")
    print(f"  fresh boot still sees {len(still_gap)}/{len(rep['microtheories_grown'])} grown topics as "
          f"gaps (global graph unchanged; acquired seeds isolated)")

    print("\n" + "=" * 78)
    print(f"DONE — {rep['n_articles']} articles consumed -> +{rep['growth']['concepts']} grounded "
          f"concepts, +{rep['growth']['microtheories']} microtheories, {rep['rejected_total']} gated out.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
