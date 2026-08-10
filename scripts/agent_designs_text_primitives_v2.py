"""Agent designs text primitives via the introspection pipeline.

Per user: 'build the introspection pipeline.'

This script runs the new pipeline (domains/introspect_primitives.py)
on the agent's vocabulary. The pipeline walks Concepts whose category
names a primitive operation; creates a PrimitiveSpec per concept;
classifies the specs by whether the existing mechanical emitter has
a template.

What changes from agent_designs_text_primitives.py (commit 26c678b):

  BEFORE  agent_specify_primitive returned one hardcoded spec
          (ArgMax — historical from speech-science pivot)

  AFTER   introspect_primitive_specs walks the substrate's own
          concept categories and produces specs for everything the
          agent has vocabulary about. The narrowness was in the
          design pipeline, not in the agent's vocabulary.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec","TextSource")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"introspect"})
                except Exception: pass
    return s


def install_all(s):
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"): continue
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
            except Exception: continue


def short(t, n=140):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 76)
    print("AGENT DESIGNS TEXT PRIMITIVES — via introspection pipeline")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print()

    from domains.introspect_primitives import (introspect_primitive_specs,
                                                  emission_report,
                                                  CATEGORY_TO_SEMANTIC_KIND)
    from domains.runtime_design import emit_primitive_rust

    # ---- 1. WALK THE TEXT VOCABULARY ----
    print("=" * 76)
    print("1. introspect_primitive_specs on text-handling Mts")
    print("=" * 76)
    print()
    text_mts = {"language_foundation","text_comprehension",
                 "scientific_writing","parsing_concepts","latex"}
    print(f"  Walking concepts whose origin is in: {sorted(text_mts)}")
    print(f"  Recognised categories ({len(CATEGORY_TO_SEMANTIC_KIND)}):")
    for cat, kind in sorted(CATEGORY_TO_SEMANTIC_KIND.items()):
        print(f"    {cat:<28} → semantic_kind: {kind}")
    print()
    specs = introspect_primitive_specs(s, origin_filter=text_mts)
    print(f"  PrimitiveSpec nodes created: {len(specs)}")
    print()
    print(f"  Top 15 by Mt:")
    by_mt = Counter(s["from_mt"] for s in specs)
    for mt, n in by_mt.most_common():
        print(f"    · {mt}: {n} specs")
    print()
    print(f"  Sample (10 of {len(specs)}):")
    for s_dict in specs[:10]:
        print(f"    · {s_dict['name']:<32}"
              f" ({s_dict['from_mt']}/{s_dict['from_category']})")
        print(f"        semantic_kind: {s_dict['semantic_kind']}")
        print(f"        purpose: {short(s_dict['purpose'], 110)}")
    print()

    # ---- 2. CLASSIFY BY TEMPLATE COVERAGE ----
    print("=" * 76)
    print("2. EMISSION REPORT — what the existing emitter can handle")
    print("=" * 76)
    print()
    report = emission_report(specs)
    print(f"  Specs total:                  {report['n_total']}")
    print(f"  Distinct semantic_kinds:      {report['n_kinds_total']}")
    print(f"  Kinds emitter has template:   {report['n_kinds_handled']}")
    print(f"  Kinds needing new template:   {report['n_kinds_needs']}")
    print()
    print(f"  Handled (emitter can compile to Rust):")
    for k, names in sorted(report["handled"].items()):
        print(f"    [{k}] {len(names)} specs: {names[:5]}{'...' if len(names) > 5 else ''}")
    print()
    print(f"  Needs new template (the next design move):")
    for k, names in sorted(report["needs_template"].items(),
                              key=lambda x: -len(x[1])):
        print(f"    [{k}] {len(names)} specs: {names[:5]}{'...' if len(names) > 5 else ''}")
    print()

    # ---- 3. TRY EMISSION ON THE HANDLED SPECS ----
    print("=" * 76)
    print("3. EMIT RUST for handled specs")
    print("=" * 76)
    print()
    handled_specs = [sd for sd in specs
                      if sd["semantic_kind"] in {"index_of_reduction"}]
    if handled_specs:
        print(f"  Emitting Rust for {len(handled_specs)} specs:")
        for sd in handled_specs[:3]:
            full_spec = {
                "name": sd["name"],
                "semantic_kind": sd["semantic_kind"],
                "items_field": "items",
                "reduce_op": "max",
                "purpose": sd["purpose"],
            }
            try:
                emitted = emit_primitive_rust(full_spec)
                print(f"  · {sd['name']}:")
                for place, code in emitted.items():
                    first_line = code.splitlines()[0] if code else ""
                    print(f"      [{place}]: {short(first_line, 100)}")
            except Exception as e:
                print(f"  · {sd['name']}: emitter error: {e}")
    else:
        print(f"  No specs have semantic_kind 'index_of_reduction'")
        print(f"  (the existing emitter's only template family).")
        print(f"  All specs land in 'needs_template' — the next design")
        print(f"  move would be to add templates per semantic_kind, OR")
        print(f"  to author finer-grained category→semantic_kind mappings.")
    print()

    # ---- 4. WHAT THIS PIPELINE NOW LETS THE AGENT DO ----
    print("=" * 76)
    print("WHAT THIS LANDED")
    print("=" * 76)
    print()
    print(f"  · The agent's design surface is no longer single-hardcoded.")
    print(f"  · introspect_primitive_specs walks {len(s.nodes('Concept'))}")
    print(f"    Concepts, applies the category→semantic_kind contract,")
    print(f"    produces {len(specs)} PrimitiveSpec nodes from text")
    print(f"    vocabulary alone.")
    print(f"  · Specs are graph data: the substrate's other pipelines")
    print(f"    (synthesize_gaps, cortex, walker) can now reason ABOUT")
    print(f"    PrimitiveSpec nodes the same way they reason about any")
    print(f"    other node type.")
    print(f"  · The emitter's template gap is honestly surfaced:")
    print(f"    {report['n_kinds_needs']} kinds need new templates.")
    print()
    print(f"  The agent's vocabulary specifies primitives; the pipeline")
    print(f"  lifts that specification into PrimitiveSpec output the")
    print(f"  existing emitter (or future emitters) consume. The narrowness")
    print(f"  has moved from the SPEC machinery (was: 1 hardcoded spec)")
    print(f"  to the TEMPLATE machinery (1 family handles 1 semantic_kind).")
    print()
    print(f"  Extending templates is the next design move — and it IS")
    print(f"  mechanical: each semantic_kind gets a Rust template just")
    print(f"  as 'index_of_reduction' has now. Adding templates is the")
    print(f"  agent's runtime-design pattern operating on its own emitter.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
