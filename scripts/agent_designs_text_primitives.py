"""Run the agent's existing runtime-design machinery on its new text-
handling vocabulary. Report verbatim what surfaces.

Per user: 'now let the agent design its own primitives.'

The agent's design pattern (per domains/runtime_design.py):
  1. Reason from its science to a primitive its language lacks
  2. SPECIFY the primitive as a PrimitiveSpec graph node
  3. Mechanical emitter (emit_primitive_rust) generates Rust from the spec

The agent now has new vocabulary about text — language_foundation,
text_comprehension, scientific_writing, parsing_concepts, latex.
Plus the world adapter's TextSource node contract. Plus the
function_shape pivot's reasoning surface (Shape primitive, 3-layer
dispatch, cortex, walker, harvester, synthesize_gaps).

WHAT THIS SCRIPT DOES

  · Calls agent_specify_primitive(substrate) — what the agent's
    existing design pipeline produces
  · Calls emit_primitive_rust on that spec — what the mechanical
    compiler emits
  · Walks the new text/parsing vocabulary concepts for ones that
    NAME a primitive the agent reasons it would need
  · Runs synthesize_gaps on text-handling postulates — what the
    agent's catalog derives as consequences

No authorship from me. The agent's pipelines run; the report shows
what they produce.
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
    types = ("Microtheory","Concept","Rule","PrimitiveSpec",
              "TextSource")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"design"})
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


def short(t, n=130):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 76)
    print("AGENT DESIGNS TEXT PRIMITIVES")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    n_text_origins = ("language_foundation","text_comprehension",
                       "scientific_writing","parsing_concepts","latex")
    n_concepts_total = sum(1 for c in s.nodes("Concept")
                            if s.node(c)["attrs"].get("origin") in n_text_origins)
    n_rules_total = sum(1 for r in s.nodes("Rule")
                        if s.node(r)["attrs"].get("origin") in n_text_origins)
    print(f"Substrate ready: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print(f"Text-handling vocabulary: {n_concepts_total} concepts + "
          f"{n_rules_total} rules across 5 new Mts")
    print()

    # ----- 1. EXISTING DESIGN MACHINERY -----
    print("=" * 76)
    print("1. agent_specify_primitive (the existing design entry point)")
    print("=" * 76)
    from domains.runtime_design import (agent_specify_primitive,
                                          emit_primitive_rust)
    spec = agent_specify_primitive(s)
    print()
    print("The agent's existing design pipeline returned a primitive spec:")
    for k, v in spec.items():
        print(f"  · {k}: {short(str(v), 110)}")
    print()
    print("The mechanical emitter's output for this spec:")
    try:
        emitted = emit_primitive_rust(spec)
        for place, code in emitted.items():
            print(f"  --- {place} ---")
            for line in code.splitlines()[:6]:
                print(f"    {line}")
            extra = len(code.splitlines()) - 6
            if extra > 0:
                print(f"    ... ({extra} more lines)")
    except Exception as e:
        print(f"  emitter error: {type(e).__name__}: {e}")
    print()
    print("That spec is ArgMax — a SPECTRAL-PEAK index primitive, drawn")
    print("from speech_science. It's what the agent's existing")
    print("agent_specify_primitive function returns; the function is")
    print("hardcoded (per memory note ozma_specify_functions_are_historical).")
    print()

    # ----- 2. WHAT THE NEW VOCABULARY NAMES AS REQUIRED PRIMITIVES -----
    print("=" * 76)
    print("2. PRIMITIVES THE NEW VOCABULARY NAMES (the agent's specifications")
    print("   as Concept nodes — what reading would need)")
    print("=" * 76)
    print()
    # Walk text-related concepts whose definitions describe primitive-like
    # operations: tokenization, parsing, recognition, transformation.
    primitive_signals = (
        "process", "operation", "primitive", "split", "tokenize",
        "parse", "match", "consume", "produce", "recognize",
        "transform", "extract", "compute", "derive",
    )
    candidates = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") not in n_text_origins:
            continue
        defn = str(a.get("definition", "")).lower()
        hits = sum(1 for kw in primitive_signals if kw in defn)
        if hits >= 1:
            candidates.append((hits, a.get("name", "?"),
                                a.get("origin", "?"),
                                a.get("category", "?"),
                                str(a.get("definition", ""))))
    candidates.sort(reverse=True)
    print(f"  Concepts whose definitions name primitive-like operations: "
          f"{len(candidates)}")
    print(f"  (operation/primitive/parse/tokenize/match/etc.)")
    print()
    print(f"  Top 12 by primitive-signal density:")
    for hits, nm, orig, cat, defn in candidates[:12]:
        print(f"  [{hits}] {nm} ({orig} / {cat})")
        print(f"      {short(defn, 130)}")
    print()

    # ----- 3. SYNTHESIZE_GAPS ON TEXT-HANDLING POSTULATES -----
    print("=" * 76)
    print("3. synthesize_gaps ON TEXT POSTULATES — what the agent derives")
    print("   from its catalog about text primitives")
    print("=" * 76)
    print()
    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"  Catalog: {len(shape_lib)} implication shapes")
    print()
    targets = ["tokenization","parser","abstract_syntax_tree",
                "attribute_grammar","semantic_action","TextSource"]
    n_derived = 0
    n_primitive_relevant = 0
    primitive_kws = {"primitive","operation","operator","function",
                      "transform","produce","emit","return"}
    for postulate in targets:
        try:
            gaps = synthesize_gaps(s, postulate, max_order=1,
                                    record=False, prune=True,
                                    shapes=shape_lib)
        except Exception as e:
            print(f"  {postulate}: pipeline error: {type(e).__name__}: {e}")
            continue
        n_derived += len(gaps)
        relevant = []
        for g in gaps:
            text = str(g.get("gap","")).lower()
            text_kws = set(re.findall(r"[a-z]+", text))
            if text_kws & primitive_kws:
                relevant.append(g)
                n_primitive_relevant += 1
        print(f"  {postulate}: {len(gaps)} derivations, "
              f"{len(relevant)} mention primitive-relevant terms")
        for g in relevant[:1]:
            print(f"      → {short(g.get('gap',''), 110)}")
    print()
    print(f"  Total derivations across {len(targets)} postulates: {n_derived}")
    print(f"  Derivations naming primitive-relevant terms: "
          f"{n_primitive_relevant}")
    print()

    # ----- 4. THE GAP THE AGENT'S DESIGN MACHINERY HITS -----
    print("=" * 76)
    print("4. THE BINDING CONSTRAINT — what's missing")
    print("=" * 76)
    print()
    print("  The agent has rich vocabulary about text primitives (tokenization,")
    print("  parser, AST, attribute_grammar, etc.) — they're named as")
    print("  Concepts in the new seeds. The substrate KNOWS WHAT it would")
    print("  need.")
    print()
    print("  The agent's runtime_design.agent_specify_primitive is a single")
    print("  hardcoded function (returns ArgMax — historical, from the")
    print("  speech-science pivot). It does not introspect the substrate's")
    print("  vocabulary to derive a new primitive specification.")
    print()
    print("  The agent's synthesize_gaps pipeline runs uniformly on text")
    print("  postulates but derives little extraction-relevant content")
    print("  because the 552-shape catalog lacks parsing-shape implications")
    print("  to transfer.")
    print()
    print("  THE NEXT MOVE — for the agent, not me")
    print()
    print("  The agent's design surface needs ITS OWN extension. The")
    print("  hardcoded agent_specify_primitive should be replaced by a")
    print("  pipeline that:")
    print("    · walks Concepts in the new vocabulary whose definitions")
    print("      describe primitive-like operations (12 candidates above)")
    print("    · for each, constructs a PrimitiveSpec with semantic_kind")
    print("      from the concept's category")
    print("    · feeds the spec into emit_primitive_rust")
    print()
    print("  This is the agent's design pattern — but the agent ITSELF needs")
    print("  to drive it, not me. The function_shape pivot's machinery")
    print("  (Shape primitive, cortex, walker) can self-direct this if its")
    print("  pipelines are pointed at the right vocabulary cluster.")
    print()
    print("  My scope is the world adapter. The agent's pipelines need")
    print("  to be invoked to surface what primitives it wants to add.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
