#!/usr/bin/env python3
"""Qualia vibe probe — see the shape of concepts in qualia space.

Run: python3 scripts/qualia_vibe_probe.py [--mt NAME] [--concept NAME] [--overlay]

With no flags: loads the vocabulary seeds, iterates ALL concepts across all Mts,
computes each concept's qualia signature, and prints:
  * the dimension HISTOGRAM (how many concepts light up each axis — this IS the
    vibe: thin where the corpus hasn't been felt, rich where it has);
  * the top-10 richest concepts (most qualia coordinates — the most "known"
    things in the space);
  * any CROSS-FAMILY matches found (where lexical + dynamical co-reside).

With --concept NAME: prints that concept's full qualia coordinates + its nearest
neighbours (the concepts most structurally similar in qualia space — the
shortcut-the-logic "vibe match").

With --mt NAME: restricts to one microtheory.

With --overlay: folds the live CAN fields (how the agent feels RIGHT NOW) into
every signature. Without it: crystallised-only (the standing shape).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"


def _load_seeds(s, ag):
    """Load the qualia machinery seeds via the manifest loader."""
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)


def _materialise_domain(s, seed_name):
    """Materialise a `microtheory`+`concepts[]` domain seed (philosophy,
    mathematics, ...) directly into Concept nodes under a Microtheory, exactly
    as the real domain loader does: each concept carries name/definition/why/
    category. This reads the SAME JSON the boot path reads — a faithful corpus
    for the vibe probe without depending on the full boot orchestration.

    Returns the Mt node id, or None if the seed isn't a domain seed."""
    path = SEEDS / f"{seed_name}.json"
    if not path.exists():
        return None
    try:
        d = json.load(open(path))
    except Exception:
        return None
    concepts = d.get("concepts")
    if not concepts:
        return None
    mt_spec = d.get("microtheory")
    if not isinstance(mt_spec, dict):
        mt_spec = {}
    mt_name = mt_spec.get("name") or d.get("id") or seed_name
    mt = s.add_node("Microtheory", {"name": mt_name,
                                    "category": mt_spec.get("category", "")})
    by_name = {}
    for c in concepts:
        attrs = {k: v for k, v in c.items()
                 if isinstance(v, (str, int, float)) and k != "local_id"}
        if "name" not in attrs:
            continue
        cid = s.add_node("Concept", attrs)
        s.add_edge_unchecked(mt, "has_concept", cid)
        by_name[attrs["name"]] = cid
    # wire any is-a / built_from taxonomy edges the concepts declare inline
    for c in concepts:
        nm = c.get("name")
        if nm not in by_name:
            continue
        for et in ("built_from", "genls", "is_a", "kind_of", "subtype_of"):
            tgt = c.get(et)
            if isinstance(tgt, str) and tgt in by_name:
                s.add_edge_unchecked(by_name[nm], et, by_name[tgt])
    return mt


def _all_concepts(s):
    try:
        return list(s.nodes("Concept"))
    except Exception:
        return []


def _mt_concepts(s, mt_name):
    for mt in s.nodes("Microtheory"):
        if str(s.node(mt)["attrs"].get("name", "")) == mt_name:
            return list(s.neighbours(mt, "has_concept"))
    return []


def main():
    parser = argparse.ArgumentParser(description="Qualia vibe probe")
    parser.add_argument("--mt", help="Restrict to a microtheory by name")
    parser.add_argument("--concept", help="Show one concept's full qualia + nearest")
    parser.add_argument("--overlay", action="store_true",
                        help="Include live CAN fields (perturbed shape)")
    parser.add_argument("--top", type=int, default=10,
                        help="How many richest concepts to show")
    parser.add_argument("--ground-categories", action="store_true",
                        help="Wire each concept's author-supplied `category` "
                             "attr into a genls edge (taxonomy enrichment) "
                             "before probing — shows the lexical:formal shift")
    args = parser.parse_args()

    # Clear caches
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()

    print("booting substrate + seeds…")
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    # open productions so materialised has_concept + taxonomy edges are admitted
    _NT = ("Agent", "Concept", "Microtheory")
    _ET = ("has_concept", "built_from", "genls", "is_a", "kind_of",
           "subtype_of", "operates_in")
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "vibe:open"})
    _load_seeds(s, ag)
    _DOMAINS = ("philosophy", "mathematics", "computer_architecture",
                "communication_concepts", "embedded_iot_realtime")
    for name in _DOMAINS:
        _materialise_domain(s, name)

    # TAXONOMY ENRICHMENT (optional): wire each concept's author-supplied
    # `category` attr into a genls edge to a category-hub Concept, so the
    # edge-poor domain concepts gain a real outgoing lexical:formal coordinate
    # and same-category concepts share a traversable hub. Reads a classification
    # the seed author already asserted (graph data) — nothing invented.
    if args.ground_categories:
        from domains import grounded_representation as gr
        res = gr.ground_categories(s)
        print(f"ground_categories: +{res['edges_added']} genls edges, "
              f"{res['hubs']} category hubs, {res['concepts_wired']} concepts wired")

    concepts = _mt_concepts(s, args.mt) if args.mt else _all_concepts(s)
    # exclude the category HUB nodes ground_categories mints, so the probed set
    # stays the real domain corpus (the denominator is comparable before/after).
    concepts = [c for c in concepts
                if str(s.node(c)["attrs"].get("kind", "")) != "category_hub"]
    print(f"{len(concepts)} concepts"
          f"{' in ' + args.mt if args.mt else ' total'}")

    # ---------- compute signatures ---------------------------------------
    sigs = {}
    dim_hist = Counter()
    for c in concepts:
        name = str(s.node(c)["attrs"].get("name", ""))
        sig = asr.concept_signature(s, c, overlay=args.overlay)
        sigs[name] = sig
        for dim, _pred, _val in sig:
            dim_hist[dim] += 1

    # ---------- the dimension histogram: the VIBE of the corpus ----------
    print("\n─── dimension histogram (the vibe) ───")
    total = len(concepts)
    for dim, count in dim_hist.most_common():
        bar = "█" * int(40 * count / total)
        print(f"  {dim:35s} {count:5d}/{total} {bar}")

    # ---------- richest concepts (most qualia coordinates) ----------------
    print(f"\n─── top-{args.top} richest (most qualia coordinates) ───")
    ranked = sorted(sigs.items(), key=lambda kv: -len(kv[1]))
    for name, sig in ranked[:args.top]:
        dims = sorted({t[0] for t in sig})
        print(f"  {name:40s} [{len(sig):2d} coords] "
              f"{', '.join(dims)}")

    # ---------- single concept deep-dive ----------------------------------
    if args.concept:
        print(f"\n─── qualia coordinates of '{args.concept}' ───")
        sig = sigs.get(args.concept)
        if sig is None:
            print(f"  (concept '{args.concept}' not found)")
        else:
            for t in sorted(sig):
                print(f"  {t}")
            # nearest neighbours: concepts whose signature intersection is largest
            print(f"\n─── nearest vibes to '{args.concept}' ───")
            scores = []
            for other_name, other_sig in sigs.items():
                if other_name == args.concept:
                    continue
                shared = sig & other_sig
                disc = {t for t in shared if t[1] != "is_a" and t[2] not in ("", "·")}
                if disc:
                    dims = sorted({t[0] for t in disc})
                    scores.append((other_name, len(disc), dims))
            scores.sort(key=lambda x: -x[1])
            for other, n, dims in scores[:10]:
                print(f"  {other:40s} [{n:2d} shared] "
                      f"{', '.join(dims)}")

    # ---------- cross-family concepts (lexical + dynamical lit up) --------
    cross = [(n, sig) for n, sig in sigs.items()
             if any(d.startswith("dynamical:") for d, _, _ in sig)
             and any(d.startswith("lexical:") and d != "lexical:formal" for d, _, _ in sig)]
    if cross:
        print(f"\n─── {len(cross)} cross-family concepts "
              f"(lexical + dynamical co-reside) ───")
        for name, sig in cross[:15]:
            dims = sorted({t[0] for t in sig if not t[0].startswith("attr:")})
            print(f"  {name:40s} {', '.join(dims)}")


if __name__ == "__main__":
    main()
