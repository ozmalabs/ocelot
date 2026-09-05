#!/usr/bin/env python3
"""Before/after probe for domains/relation_grounding.ground_relations over a real
domain Mt — shows lexical:telic / constitutive / agentive going from 0 to >0 with
the emitted edges being REAL (target is a held concept), plus the grounded-vs-
dropped ratio (a high drop rate = the anti-hallucination gate working).

Run: python3 scripts/relation_grounding_probe.py [--mt computer_architecture]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
from domains import relation_grounding as rg

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"


def _load_seeds(s, ag):
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)


def _materialise_domain(s, seed_name):
    path = SEEDS / f"{seed_name}.json"
    d = json.load(open(path))
    concepts = d.get("concepts") or []
    mt_spec = d.get("microtheory") or {}
    mt_name = mt_spec.get("name") or d.get("id") or seed_name
    mt = s.add_node("Microtheory", {"name": mt_name})
    by_name = {}
    for c in concepts:
        attrs = {k: v for k, v in c.items()
                 if isinstance(v, (str, int, float)) and k != "local_id"}
        if "name" not in attrs:
            continue
        cid = s.add_node("Concept", attrs)
        s.add_edge_unchecked(mt, "has_concept", cid)
        by_name[attrs["name"]] = cid
    for c in concepts:
        nm = c.get("name")
        if nm not in by_name:
            continue
        for et in ("built_from", "genls", "is_a", "kind_of", "subtype_of"):
            tgt = c.get(et)
            if isinstance(tgt, str) and tgt in by_name:
                s.add_edge_unchecked(by_name[nm], et, by_name[tgt])
    return mt, by_name


def _mt_concepts(s, mt_name):
    for mt in s.nodes("Microtheory"):
        if str(s.node(mt)["attrs"].get("name", "")) == mt_name:
            return list(s.neighbours(mt, "has_concept"))
    return []


def _dim_hist(s, concepts):
    hist = Counter()
    for c in concepts:
        for dim, _pred, _val in asr.concept_signature(s, c):
            hist[dim] += 1
    return hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mt", default="computer_architecture")
    args = ap.parse_args()

    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()

    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    # open productions for materialisation + the relation edges the pass emits.
    _NT = ("Agent", "Concept", "Microtheory")
    _ET = ("has_concept", "built_from", "genls", "is_a", "kind_of",
           "subtype_of") + rg.GROUNDED_RELATION_EDGE_TYPES
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "probe:open"})
    _load_seeds(s, ag)
    _materialise_domain(s, args.mt)

    concepts = _mt_concepts(s, args.mt)
    print(f"=== {args.mt}: {len(concepts)} concepts ===\n")

    lex = ("lexical:telic", "lexical:constitutive", "lexical:agentive",
           "lexical:formal")
    before = _dim_hist(s, concepts)
    print("BEFORE (dark relational axes):")
    for d in lex:
        print(f"  {d:24s} {before.get(d, 0):4d}/{len(concepts)}")

    # RUN THE PASS
    res = rg.ground_relations(s, args.mt)
    asr._QUALIA_SCHEMA_CACHE.clear()

    after = _dim_hist(s, concepts)
    print("\nAFTER ground_relations:")
    for d in lex:
        print(f"  {d:24s} {after.get(d, 0):4d}/{len(concepts)}  "
              f"(+{after.get(d, 0) - before.get(d, 0)})")

    total = res["edges_added"] + res["dropped"]
    print(f"\n--- gate metrics ---")
    print(f"  candidate relations : {total}")
    print(f"  GROUNDED (emitted)  : {res['edges_added']}")
    print(f"  DROPPED (ungrounded): {res['dropped']}")
    print(f"  grounded ratio      : {res['grounded_ratio']:.1%}  "
          f"(drop rate {1 - res['grounded_ratio']:.1%})")
    print(f"  concepts wired      : {res['concepts_wired']}")
    print(f"  by dimension        : {dict(sorted(res['by_dimension'].items()))}")

    print(f"\n--- ALL {len(res['emitted'])} emitted edges (spot-check by hand) ---")
    for src, et, tgt in sorted(res["emitted"]):
        dim = rg.EDGE_DIMENSION.get(et, "?").split(":")[-1]
        print(f"  {src:34s} --{et:12s}--> {tgt:28s} [{dim}]")


if __name__ == "__main__":
    main()
