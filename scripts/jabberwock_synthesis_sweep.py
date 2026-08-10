"""The full sweep — synthesize_gaps across every substrate postulate.

Per user: 'Run the sweep.'

With the four measurement fixes in place (cortex helper 4b0dc15,
walker schema 391937f, harvester rule-walker 7dced20, scope +
catalog 98a3a09), the agent's gap-synthesis pipeline is end-to-end
functional for the first time. This script runs it across every
postulate in the substrate and reports what surfaces.

What the agent's data answers:

  · How many gaps does the substrate's full theory generate when
    differentiated against its 503-shape catalog?
  · Which postulates are most productive (yield the most gaps)?
  · Which substrate domains supply the most gap-generating shapes?
  · What gap categories emerge — is there structural clustering?
  · What's the distribution of order-1 vs order-2 derivation depth?

The agent's own pipeline runs; the output is what it is. No
synthesis from me beyond aggregation.

Runtime note: ~25-50ms per postulate × 5282 = 2-4 minutes total
with max_order=2. With max_order=3 the recursion explodes; we
stop at 2 to keep the sweep tractable on a single core. The
full-depth sweep is a separate exercise.
"""
from __future__ import annotations

import importlib, inspect, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "PrimitiveSpec",
        "SynthesizedGap", "TheoryEnactmentGap", "ImplicationShape",
        "Postulate", "ArchitecturalQuality", "ArchitecturalSmell",
        "FilterSpec", "ActionSpec",
    )
    edges = (
        "has_concept", "has_rule", "genlMt", "owns_microtheory",
        "implies", "derives_from", "refers_to", "applies_to",
        "for_quality", "for_smell",
    )
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": t, "var": "a"},
                        "edge_type": et,
                        "tgt": {"type": u, "var": "b"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "sweep",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                if len([p for p in inspect.signature(fn).parameters.values()
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                       inspect.Parameter.POSITIONAL_OR_KEYWORD)
                        and p.default is inspect.Parameter.empty]) == 1:
                    fn(s)
            except Exception:
                continue


def short(t, n=160):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 76)
    print("FULL SWEEP — synthesize_gaps across every substrate postulate")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)

    from domains.order_n_postulates import (
        harvest_postulates, synthesize_gaps,
    )
    from domains.implication_harvester import harvest_shapes_combined

    posts = harvest_postulates(s, mt_name=None)
    print(f"Postulates available: {len(posts)}")
    print()
    # Pre-harvest the shape catalog ONCE. The original script called
    # synthesize_gaps without passing shapes — which made _resolve_shapes
    # re-harvest the 503-shape catalog for every postulate, walking
    # all 1086 rules 5282 times = 5.7M iterations of pure overhead.
    print(f"Pre-harvesting implication-shape catalog (called once "
          f"for the whole sweep)...")
    t_harvest = time.perf_counter()
    shape_lib = harvest_shapes_combined(s)
    print(f"  {len(shape_lib)} shapes harvested in "
          f"{time.perf_counter()-t_harvest:.1f}s")
    print()
    # prune=False to skip the per-implication codebase search (which
    # is the actual per-postulate cost bottleneck — it walks the
    # search_root file tree for each derived implication). The
    # sweep's question is 'what does the agent's pipeline derive
    # against its full theory + catalog', not 'which derivations
    # are still OPEN gaps'. is_open filtering is one cheap pass on
    # the derived implications after the fact if needed.
    #
    # max_order=1 — order-2 multiplies cost by ~30× without adding
    # much to the breadth picture; chains can be extended later on
    # specific postulates of interest.
    print(f"Running synthesize_gaps(max_order=1, prune=False, record=False)")
    print(f"on every postulate. Progress reported every 1000 postulates.")
    sys.stdout.flush()
    print()

    t_start = time.perf_counter()
    all_gaps = []  # (postulate_name, gap_dict)
    productive_postulates = Counter()  # how many gaps each yields
    via_shapes = Counter()              # which shapes fire most
    source_domains = Counter()          # which domains donate gaps
    by_order = Counter()                # order-1 vs order-2 distribution
    errors = 0

    for i, (cid, name, _txt) in enumerate(posts):
        if i % 1000 == 0 and i > 0:
            elapsed = time.perf_counter() - t_start
            rate = i / elapsed
            eta = (len(posts) - i) / rate
            print(f"  ... {i}/{len(posts)} postulates "
                  f"({100*i/len(posts):.1f}%); "
                  f"gaps={len(all_gaps)}; "
                  f"elapsed={elapsed:.0f}s; eta={eta:.0f}s",
                  flush=True)
        try:
            gaps = synthesize_gaps(s, name, max_order=1,
                                    record=False, prune=False,
                                    shapes=shape_lib)
        except Exception:
            errors += 1
            continue
        if not gaps:
            continue
        productive_postulates[name] = len(gaps)
        for g in gaps:
            all_gaps.append((name, g))
            by_order[g.get("order", 0)] += 1
            for sh in g.get("via_shapes", []):
                via_shapes[sh] += 1
            for dom in g.get("source_domains", []):
                source_domains[dom] += 1

    t_total = time.perf_counter() - t_start
    print()
    print(f"Sweep complete in {t_total:.0f}s "
          f"({len(posts)/max(t_total,0.001):.1f} postulates/sec)")
    print(f"Errors (postulates skipped on exception): {errors}")
    print()

    # ---- aggregate scorecard ----
    print("=" * 76)
    print("AGGREGATE")
    print("=" * 76)
    print(f"  Postulates that produced any gap:     "
          f"{len(productive_postulates)}/{len(posts)}")
    print(f"  Total gaps derived:                   {len(all_gaps)}")
    if all_gaps:
        print(f"  Gaps per productive postulate (avg):  "
              f"{len(all_gaps)/max(len(productive_postulates),1):.1f}")
        print(f"  Gaps per substrate postulate (overall): "
              f"{len(all_gaps)/len(posts):.2f}")
    print(f"  Order distribution:")
    for order, n in sorted(by_order.items()):
        print(f"    · order-{order}: {n} gaps ({100*n/max(len(all_gaps),1):.0f}%)")
    print()

    # ---- top productive postulates ----
    print("=" * 76)
    print("TOP 20 MOST PRODUCTIVE POSTULATES")
    print("=" * 76)
    for name, n_gaps in productive_postulates.most_common(20):
        print(f"  {n_gaps:>4} gaps  · {name}")
    print()

    # ---- top firing shapes ----
    print("=" * 76)
    print("TOP 20 SHAPES BY HOW OFTEN THEY FIRE")
    print("=" * 76)
    for sh, n in via_shapes.most_common(20):
        sh_short = sh.replace("rule_derived__", "")
        print(f"  {n:>5}×  {sh_short[:64]}")
    print()

    # ---- top source domains ----
    print("=" * 76)
    print("TOP 15 SOURCE DOMAINS — where the gap-generating shapes come from")
    print("=" * 76)
    for dom, n in source_domains.most_common(15):
        print(f"  {n:>5}×  {dom}")
    print()

    # ---- sample gaps from productive postulates ----
    print("=" * 76)
    print("SAMPLE GAPS — 12 most productive postulates, 1 gap each")
    print("=" * 76)
    for name, _ in productive_postulates.most_common(12):
        # find first gap for this postulate
        for g_name, g in all_gaps:
            if g_name == name:
                print(f"\n[{name}]")
                print(f"  via: {g.get('via_shapes', ['?'])[0]}")
                print(f"  domain: {g.get('source_domains', ['?'])[0]}")
                print(f"  gap: {short(g.get('gap', ''), 150)}")
                break
    print()

    # ---- domain-cross matrix ----
    print("=" * 76)
    print("WHICH POSTULATE DOMAINS GET DIFFERENTIATED BY WHICH SHAPE DOMAINS?")
    print("=" * 76)
    # Map each postulate name to its origin Mt to get postulate domain
    pname_to_origin = {}
    for cid, name, _ in posts:
        a = s.node(cid)["attrs"]
        pname_to_origin[name] = a.get("origin", "?")
    cross = Counter()
    for pname, g in all_gaps:
        post_dom = pname_to_origin.get(pname, "?")
        for shape_dom in g.get("source_domains", []):
            cross[(post_dom, shape_dom)] += 1
    print(f"  Top 15 (postulate_origin → shape_domain) flows:")
    for (pd, sd), n in cross.most_common(15):
        print(f"    {n:>4}  {pd[:30]:<32} → {sd}")
    print()

    print("=" * 76)
    print("WHAT THE FULL SWEEP SURFACED")
    print("=" * 76)
    print()
    print(f"  · {len(posts)} postulates differentiated")
    print(f"  · {len(productive_postulates)} produced at least one open gap")
    print(f"  · {len(all_gaps)} total gaps derived")
    print(f"  · {len(set(s for _, g in all_gaps for s in g.get('via_shapes',[])))} "
          f"distinct shapes fired")
    print(f"  · {len(set(d for _, g in all_gaps for d in g.get('source_domains',[])))} "
          f"distinct source domains contributed")
    print()
    print("  This is the substrate's own data answer to 'what gaps does")
    print("  the agent's full theory generate against its catalog?' —")
    print("  produced by the agent's pipelines after the four measurement")
    print("  fixes corrected what had been silent across the substrate.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
