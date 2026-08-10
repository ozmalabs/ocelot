"""Jabberwock cross-references all its Mts using n-order analysis.

Per user: 'have the agent update and cross-reference everything by
using n order analysis'.

Method:
  1. Walk all Mts × all Mts (skip self-pairs)
  2. For each pair, find_analogies at order n=3 (abstract principles)
  3. Keep top-K analogies per pair to bound graph growth
  4. Emit Analogy graph nodes + implements/analogous_to edges

The analogical_thinking faculty already exists. This script
invokes it systematically across the substrate's vocabulary.
The output is Jabberwock's own data — every Mt now has explicit
implements/analogous_to edges to every other Mt where structural
correspondences exist at order-3 abstraction.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "Analogy",
             "CrossReference")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "implements", "analogous_to", "cross_references")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tt, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "xref",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(",
                              src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (
                           inspect.Parameter.POSITIONAL_ONLY,
                           inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def main():
    s = fresh_substrate()
    install_all(s)

    from domains.analogical_thinking import find_analogies

    # All Mts, indexed by name
    mts = {}
    for mt in s.nodes("Microtheory"):
        nm = str(s.node(mt)["attrs"].get("name", "")).lower()
        if nm:
            mts[nm] = mt
    mt_names = sorted(mts.keys())
    print(f"{len(mt_names)} Mts to cross-reference.")
    print()

    # Pair-wise: find top analogies at n=3.
    # To bound runtime + graph growth: per source Mt, find analogies
    # against all targets; keep top-3 per (source, target) pair.
    TOP_PER_PAIR = 1
    MIN_SCORE = 12      # raise to cut noise; only strong analogies
    MAX_PAIRS_PROCESSED = 30  # tighter — first 30 Mts as sources

    n_emitted = 0
    n_pairs_processed = 0
    edge_count = 0
    summary_top_by_pair = []

    print("Walking Mt × Mt pairs at order n=3 (abstract principle)...")
    print()

    for i, src_name in enumerate(mt_names):
        if n_pairs_processed >= MAX_PAIRS_PROCESSED:
            break
        # Get analogies for this Mt against EVERY OTHER Mt at once
        target_names = [n for n in mt_names if n != src_name]
        try:
            analogies = find_analogies(
                s, src_name, target_names,
                order_n=3, min_score=MIN_SCORE)
        except Exception:
            continue
        n_pairs_processed += 1
        if not analogies:
            continue

        # Group by target Mt + keep top-K per
        by_target: dict[str, list] = {}
        for a in analogies:
            by_target.setdefault(a["target_mt"], []).append(a)
        for tgt, alist in by_target.items():
            alist.sort(key=lambda x: -x["score"])
            for a in alist[:TOP_PER_PAIR]:
                # Emit Analogy node
                try:
                    an = s.add_node("Analogy", {
                        "source_mt": a["source_mt"],
                        "target_mt": a["target_mt"],
                        "source_concept": a["source_concept"],
                        "target_concept": a["target_concept"],
                        "score": int(a["score"]),
                        "order_n": 3,
                        "rationale": a["rationale"][:300],
                    })
                    s.add_edge(a["source_node"], "analogous_to",
                               a["target_node"], {})
                    if a["score"] >= 12:
                        s.add_edge(a["source_node"], "implements",
                                   a["target_node"], {})
                    n_emitted += 1
                    edge_count += 1
                except Exception:
                    pass

        # Record top pair for this source
        if analogies:
            top = max(analogies, key=lambda x: x["score"])
            summary_top_by_pair.append((src_name, top))

        if i < 10 or i % 10 == 0:
            print(f"  [{i+1}/{len(mt_names)}] {src_name:<32}  "
                  f"emitted {sum(min(TOP_PER_PAIR, len(v)) for v in by_target.values())} analogies "
                  f"to {len(by_target)} target Mts")

    print()
    print("=" * 72)
    print("CROSS-REFERENCE SUMMARY")
    print("=" * 72)
    print(f"  Mts cross-referenced as source: {n_pairs_processed}")
    print(f"  Analogy nodes emitted: {n_emitted}")
    print(f"  analogous_to / implements edges: {edge_count}")
    print()

    print("=" * 72)
    print("SAMPLE — strongest cross-Mt analogy per source Mt")
    print("=" * 72)
    print()
    summary_top_by_pair.sort(key=lambda x: -x[1]["score"])
    for src_name, top in summary_top_by_pair[:25]:
        print(f"  {src_name:<32} → {top['target_mt'][:25]:<25} "
              f"score={top['score']}")
        print(f"     {top['source_concept'][:25]:<25} ↔ "
              f"{top['target_concept'][:30]:<30}")
        # Truncate rationale
        rat = top['rationale'][:120]
        print(f"     {rat}")
        print()


if __name__ == "__main__":
    main()
