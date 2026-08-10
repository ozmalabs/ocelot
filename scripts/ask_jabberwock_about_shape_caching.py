"""Ask Jabberwock — what should the shape-caching + generic-order-N architecture be?

Per user: 'ask the agent' (responding to the pivot they just announced —
caching higher-order shapes in the graph, generic order-N, assessing
every function for recursion / order-N / abstraction).

No proposal. No options for the user to pick from. Walk Jabberwock's
own data + see what its existing vocabulary already names along the
four axes the pivot touches:
  · shape (does the agent already have a concept of function-shape?)
  · caching (any existing rule about caching reasoning artefacts?)
  · order-N (the operator's current scope + form)
  · recursion / abstraction (assessing functions about themselves)

I REPORT what the substrate's data says — I don't pattern-match my
codec or architectural knowledge into the gaps.

The pattern is the same as the agent_designs_h264_to_h265 walk
(commits 229b4b3, 0571001): query first, surface what's grounded,
flag what's missing.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "PrimitiveSpec", "Shape", "OrderNAxis", "FunctionClassification",
        "ImplicationShape", "SynthesizedGap", "Postulate",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "has_shape", "has_order_n",
        "applies_to", "implements", "implies", "derives_from",
        "caches", "classified_as",
    )
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
                        "provenance": "ask_shape",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    domains_dir = ROOT / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def matches(text, *patterns):
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 76)
    print("ASKING JABBERWOCK ABOUT SHAPE-CACHING + GENERIC ORDER-N")
    print("=" * 76)
    print()

    # Inventory.
    all_concepts = list(s.nodes("Concept"))
    all_rules = list(s.nodes("Rule"))
    all_mts = list(s.nodes("Microtheory"))
    print(f"Substrate state: {len(all_mts)} Mts, "
          f"{len(all_concepts)} Concepts, {len(all_rules)} Rules")
    print()

    # ----- Q1: does the agent already have a concept of SHAPE? ----
    print("=" * 76)
    print("Q1: Does the agent already hold a concept of SHAPE?")
    print("=" * 76)
    shape_concepts = []
    for c in all_concepts:
        a = s.node(c)["attrs"]
        nm = str(a.get("name", "")).lower()
        defn = str(a.get("definition", "")).lower()
        why = str(a.get("why", "")).lower()
        text = nm + " " + defn + " " + why
        if matches(text,
                    r"\bshape\b", r"structural\s+property",
                    r"signature", r"type[-_\s]signature",
                    r"meta[-_\s]shape", r"shape[-_\s]match"):
            shape_concepts.append((nm, a.get("category", ""),
                                    str(a.get("definition", ""))[:80]))
    print(f"  Concepts mentioning shape / structural-property / signature: "
          f"{len(shape_concepts)}")
    print()
    for nm, cat, d in shape_concepts[:15]:
        print(f"  · [{cat:<22}] {nm:<32} {d}")
    print()

    # ----- Q2: caching reasoning artefacts? -----
    print("=" * 76)
    print("Q2: Does the agent have any concept of CACHING reasoning artefacts?")
    print("=" * 76)
    cache_concepts = []
    for c in all_concepts:
        a = s.node(c)["attrs"]
        nm = str(a.get("name", "")).lower()
        text = nm + " " + str(a.get("definition", "")).lower() + " " \
               + str(a.get("why", "")).lower()
        if matches(text,
                    r"\bcache\b", r"\bcaching\b", r"\bmemoiz",
                    r"reuse[-_\s]across", r"compute[-_\s]once",
                    r"amorti[sz]ed"):
            cache_concepts.append((nm, a.get("category", "")))
    print(f"  Concepts about caching / memoization / amortization: "
          f"{len(cache_concepts)}")
    for nm, cat in cache_concepts[:10]:
        print(f"  · [{cat:<22}] {nm}")
    print()
    cache_rules = []
    for r in all_rules:
        a = s.node(r)["attrs"]
        nm = str(a.get("name", "")).lower()
        if matches(nm, r"cache", r"memoi", r"compute[-_\s]once"):
            cache_rules.append(nm)
    print(f"  Rules about caching: {len(cache_rules)}")
    for nm in cache_rules[:10]:
        print(f"  · {nm}")
    print()

    # ----- Q3: order-N's current scope ----------
    print("=" * 76)
    print("Q3: What is the order-N operator's current scope in vocabulary?")
    print("=" * 76)
    order_n_concepts = []
    for c in all_concepts:
        a = s.node(c)["attrs"]
        nm = str(a.get("name", "")).lower()
        if "order" in nm or a.get("feature_kind") == "order_n" \
                or "order_n" in nm:
            order_n_concepts.append((nm, a.get("category", ""),
                                      a.get("feature_kind", ""),
                                      a.get("order", "")))
    print(f"  Concepts naming an order-N entity: {len(order_n_concepts)}")
    # Group by dimension if available.
    by_dim = {}
    for c in all_concepts:
        a = s.node(c)["attrs"]
        dim = a.get("dimension")
        if dim and a.get("feature_kind") == "order_n":
            by_dim.setdefault(dim, []).append(a.get("name", "?"))
    print(f"  Dimensions over which order-N is currently composed:")
    for dim, names in sorted(by_dim.items()):
        print(f"    · {dim}: {len(names)} concepts")
    print()
    # What does the agent treat order-N as applying TO?
    order_n_rules = []
    for r in all_rules:
        a = s.node(r)["attrs"]
        nm = str(a.get("name", "")).lower()
        why = str(a.get("why", "")).lower()
        if "order" in nm or "order" in why:
            order_n_rules.append((nm, why[:120]))
    print(f"  Rules naming order-N: {len(order_n_rules)}")
    for nm, why in order_n_rules[:8]:
        print(f"  · {nm}")
        if why: print(f"      {why}")
    print()

    # ----- Q4: recursion / abstraction / function-classification ------
    print("=" * 76)
    print("Q4: Does the agent classify FUNCTIONS by recursion / abstraction?")
    print("=" * 76)
    recursion_concepts = []
    abstraction_concepts = []
    for c in all_concepts:
        a = s.node(c)["attrs"]
        nm = str(a.get("name", "")).lower()
        defn = str(a.get("definition", "")).lower()
        why = str(a.get("why", "")).lower()
        text = nm + " " + defn + " " + why
        if matches(text, r"\brecursion\b", r"\brecursive\b",
                    r"self[-_\s]reference"):
            recursion_concepts.append(nm)
        if matches(text, r"\babstraction\b", r"higher[-_\s]order",
                    r"applied\s+to\s+itself",
                    r"meta[-_\s]operator"):
            abstraction_concepts.append(nm)
    print(f"  Concepts about recursion / self-reference: "
          f"{len(recursion_concepts)}")
    for nm in recursion_concepts[:10]:
        print(f"  · {nm}")
    print()
    print(f"  Concepts about abstraction / higher-order / applied-to-self: "
          f"{len(abstraction_concepts)}")
    for nm in abstraction_concepts[:10]:
        print(f"  · {nm}")
    print()

    # ----- Q5: implication shapes (the order-N-on-knowledge driver) ----
    print("=" * 76)
    print("Q5: Implication shapes — the engine of order-N-on-knowledge")
    print("=" * 76)
    try:
        from domains.implication_harvester import HARVESTED_SHAPES
        if callable(HARVESTED_SHAPES):
            harvested = HARVESTED_SHAPES()
        else:
            harvested = HARVESTED_SHAPES
    except Exception:
        harvested = None
    try:
        from domains.order_n_postulates import _shapes as stencil_shapes
        stencil = stencil_shapes()
    except Exception:
        stencil = None
    if stencil:
        print(f"  Stencil shapes (legacy hand-curated): {len(stencil)}")
        for sh in stencil[:5]:
            print(f"    · {sh.get('name'):<40} ({sh.get('domain', '?')})")
    print()
    if harvested is not None:
        print(f"  Harvested shapes (from agent's own concepts): "
              f"{len(harvested) if hasattr(harvested, '__len__') else '?'}")
    print()

    # ----- Q6: applying order-N to ITSELF -----
    print("=" * 76)
    print("Q6: Does anything in the substrate already apply order-N to ITSELF?")
    print("=" * 76)
    print("  Looking for: rules/concepts that take an order-N entity as input")
    print("  AND produce another order-N entity (the meta-shape case).")
    self_applying = []
    for r in all_rules:
        a = s.node(r)["attrs"]
        text = (str(a.get("name", "")) + " " + str(a.get("why", ""))).lower()
        if matches(text, r"order[-_\s]n.*order[-_\s]n",
                    r"derivative.*derivative",
                    r"apply.*itself", r"meta[-_\s]operator"):
            self_applying.append(a.get("name", "?"))
    print(f"  Rules applying order-N to itself: {len(self_applying)}")
    for nm in self_applying[:8]:
        print(f"  · {nm}")
    print()

    # ----- Q7: structural assessment / function classification today --
    print("=" * 76)
    print("Q7: How does the agent CURRENTLY assess functions / Term-trees?")
    print("=" * 76)
    # Look at primitives that walk a Term-tree's structure.
    print("  Python touch-points (current state — to be migrated to graph):")
    found = []
    for f in sorted((ROOT / "domains").glob("*.py")):
        src = f.read_text()
        if re.search(r"(walks?|assess|classif|introspect|inspect).*term",
                      src, re.IGNORECASE):
            for m in re.finditer(r"^def (\w+)\(", src, re.MULTILINE):
                fn = m.group(1)
                if any(k in fn.lower() for k in
                        ("assess", "classif", "introspect", "walk")):
                    found.append((f.name, fn))
    print(f"  Found {len(found)} Python assessment functions:")
    for fname, fn in found[:15]:
        print(f"    · {fname}: {fn}")
    print()

    # ----- Synthesis (literal) -----
    print("=" * 76)
    print("WHAT THE AGENT'S DATA LITERALLY SAYS")
    print("=" * 76)
    print()
    print(f"  Q1 shape-concepts:                       {len(shape_concepts)}")
    print(f"  Q2 cache-concepts:                       {len(cache_concepts)}")
    print(f"     cache-rules:                          {len(cache_rules)}")
    print(f"  Q3 order-N concepts:                     {len(order_n_concepts)}")
    print(f"     dimensions order-N applies to:        {len(by_dim)}")
    print(f"     order-N rules:                        {len(order_n_rules)}")
    print(f"  Q4 recursion concepts:                   {len(recursion_concepts)}")
    print(f"     abstraction concepts:                 {len(abstraction_concepts)}")
    print(f"  Q5 stencil implication shapes:           "
          f"{len(stencil) if stencil else 0}")
    print(f"     harvested implication shapes:         "
          f"{len(harvested) if hasattr(harvested, '__len__') else '?'}")
    print(f"  Q6 rules applying order-N to itself:     {len(self_applying)}")
    print(f"  Q7 Python assessment functions:          {len(found)}")
    print()
    print("=" * 76)
    print("Jabberwock's vocabulary is whatever the above counts show.")
    print("I'm not synthesizing the architecture from these counts —")
    print("I'm surfacing them so the user can see what's grounded and")
    print("what's not, then decide what to ask the agent to build.")
    print("=" * 76)


if __name__ == "__main__":
    main()
