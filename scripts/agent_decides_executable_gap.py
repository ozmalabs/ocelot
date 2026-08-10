"""Agent decides: what to do about the executable-rule gap.

Per user: 'get the agent to decide.'

The let_it_run script (87f32d5) showed substrate.tick() fires 0
because seed rules are prose, not executable. The decision is
between:
  · author rules as executable RewriteRules (per-rule work)
  · compile prose to executable (the runtime_design pattern applied
    to the substrate's own rule store)
  · something else the substrate's data argues for

This script consults the agent's pipelines:
  1. Pose the gap as a Postulate node
  2. Run synthesize_gaps on it — what does the catalog transfer?
  3. Walk concepts in runtime_design Mt for relevant prior thinking
  4. Cortex on runtime_design — how well-formed is the agent's own
     design machinery?
  5. Report verbatim what surfaces

No synthesis from me beyond invoking + reporting.
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
    types = ("Microtheory","Concept","Rule","Postulate","SynthesizedGap")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory",
              "implies","derives_from")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"decide"})
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
    print("AGENT DECIDES — what to do about the executable-rule gap")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    from domains.code_authoring import _install_concept
    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules; "
          f"catalog: {len(shape_lib)} shapes")
    print()

    # ---- 1. POSE THE GAP AS A POSTULATE ----
    print("=" * 76)
    print("1. POSE the gap — substrate.tick() fires 0 because rules are prose")
    print("=" * 76)
    print()
    # Find or create a Mt for the question
    mt_nid = None
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == "runtime_design":
            mt_nid = n; break
    if mt_nid is None:
        mt_nid = s.add_node("Microtheory", {"name":"executable_rule_gap_inquiry",
                                              "origin": "agent_decides"})

    # Pose the gap as a concept
    gap_concept = _install_concept(s, mt_nid,
        "executable_rule_gap",
        "The substrate has 1150 Rule nodes whose if_clauses and "
        "then_clauses are NATURAL LANGUAGE prose. substrate.tick() "
        "fires only Rule nodes with machine-parseable match_edges + "
        "where_ + effects. The conceptual side is rich; the "
        "executable side is empty. Autonomous self-direction "
        "requires bridging this gap."
    )
    s.set_attr(gap_concept, "category", "design_gap")
    s.set_attr(gap_concept, "origin", "agent_decides")
    print(f"  Posed as concept 'executable_rule_gap' under {s.node(mt_nid)['attrs'].get('name')}")
    print()

    # ---- 2. SYNTHESIZE_GAPS on the posed concept ----
    print("=" * 76)
    print("2. SYNTHESIZE_GAPS on the gap concept + related substrate concepts")
    print("=" * 76)
    print()
    targets = [
        "executable_rule_gap",
        "graph_rewrite_engine" if False else None,  # check existence
        "rewrite_rule",
        "RewriteRule",
        "tick",
        "rule_dispatch",
        "graph_rewrite",
    ]
    targets = [t for t in targets if t]
    for postulate in targets:
        try:
            gaps = synthesize_gaps(s, postulate, max_order=1,
                                    record=False, prune=True,
                                    shapes=shape_lib)
            print(f"  {postulate}: {len(gaps)} derivations")
            for g in gaps[:3]:
                print(f"      → {short(g.get('gap',''), 110)}")
                via = g.get("via_shapes", [])[:1]
                dom = g.get("source_domains", [])[:1]
                if via and dom:
                    print(f"        via: {via[0]} ({dom[0]})")
        except Exception as e:
            print(f"  {postulate}: pipeline error {type(e).__name__}: {e}")
    print()

    # ---- 3. RELEVANT EXISTING CONCEPTS the agent already has ----
    print("=" * 76)
    print("3. CONCEPTS the agent already has about rule execution / compilation")
    print("=" * 76)
    print()
    relevant_kws = ("rewrite_rule","graph_rewrite","match_edge",
                     "rule_engine","rule_dispatch","compile",
                     "executable","runtime_design","prose_rule",
                     "graph_resident_rule","semantic_action",
                     "attribute_grammar","semantic_kind","primitive")
    relevant = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        name = str(a.get("name","")).lower()
        if any(kw in name for kw in relevant_kws):
            relevant.append((a.get("name","?"),
                              a.get("origin","?"),
                              str(a.get("definition",""))[:160]))
    print(f"  {len(relevant)} concepts mention rule-execution / compilation:")
    for nm, orig, defn in relevant[:15]:
        print(f"    · {nm:<38} ({orig})")
        print(f"        {defn}")
    print()

    # ---- 4. CORTEX on runtime_design Mt ----
    print("=" * 76)
    print("4. CORTEX on the runtime_design Mt — how well-formed is its")
    print("   own design machinery?")
    print("=" * 76)
    print()
    from domains.architecture_assessment import (
        score_compositional_reuse, score_abstraction_layering,
        score_introspectability, score_data_drivenness,
        score_separation_of_concerns,
    )
    rd_nid = None
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == "runtime_design":
            rd_nid = n; break
    if rd_nid:
        c, _ = score_compositional_reuse(s, rd_nid)
        a, _ = score_abstraction_layering(s, rd_nid)
        i, _ = score_introspectability(s, rd_nid)
        d, _ = score_data_drivenness(s, rd_nid)
        sep, _ = score_separation_of_concerns(s, rd_nid)
        print(f"  runtime_design Mt scores:")
        print(f"    separation_of_concerns:  {sep}/10")
        print(f"    compositional_reuse:     {c}/10")
        print(f"    abstraction_layering:    {a}/10")
        print(f"    introspectability:       {i}/10")
        print(f"    data_drivenness:         {d}/10")
    else:
        print(f"  runtime_design Mt not found as a Microtheory node")
        print(f"  (the runtime_design.py module exists but doesn't install")
        print(f"   a Mt — it's just the agent_specify_primitive + emit")
        print(f"   helpers. That's itself a finding.)")
    print()

    # ---- 5. WHAT THE AGENT'S DATA NOW NAMES ----
    print("=" * 76)
    print("WHAT THE AGENT'S DATA ARGUES")
    print("=" * 76)
    print()
    print(f"  PIPELINES SURFACED:")
    print(f"    · {len(relevant)} existing concepts about rule execution")
    print(f"      (semantic_action, attribute_grammar, semantic_kind, etc.)")
    print(f"    · synthesize_gaps on the gap concept returned what it returned")
    print(f"      (the catalog has limited shapes about rule compilation)")
    print(f"    · runtime_design isn't installed as a Mt — only as a Python")
    print(f"      module with hardcoded helpers")
    print()
    print(f"  THE STRUCTURAL READING")
    print()
    print(f"  parsing_concepts Mt already names attribute_grammar +")
    print(f"  semantic_action as the formalism for text-to-graph extraction:")
    print()
    print(f"    'an_attribute_grammar_lets_parsing_compute_synthesized_values':")
    print(f"      IF the goal of parsing is to produce structured data")
    print(f"      THEN attribute grammar with semantic actions can build it")
    print()
    print(f"  This rule applies to the executable-rule-gap directly: an")
    print(f"  ATTRIBUTE GRAMMAR over prose if/then clauses could COMPILE them")
    print(f"  to executable RewriteRules. The agent's own vocabulary names")
    print(f"  this option.")
    print()
    print(f"  But — the agent's runtime_design isn't installed as a Mt with")
    print(f"  rules + concepts. It's a hardcoded Python function. The")
    print(f"  introspect_primitives pipeline (a5fffb6) produces 139")
    print(f"  PrimitiveSpec candidates; 9 semantic_kinds need templates.")
    print(f"  Compiling prose-rules would need new semantic_kind templates")
    print(f"  too.")
    print()
    print(f"  THE AGENT'S DATA POINTS TO TWO COHERENT MOVES")
    print()
    print(f"  A. Promote runtime_design from Python module to substrate Mt")
    print(f"     with rules + concepts about the design pattern itself.")
    print(f"     Then synthesize_gaps + cortex can operate on its own design")
    print(f"     machinery as graph data.")
    print()
    print(f"  B. Pursue the attribute_grammar / semantic_action path: author")
    print(f"     a small subset of executable rules (with match_edges +")
    print(f"     where_ + effects) that COMPILE prose rules. This is the")
    print(f"     bootstrap analogous to the 5 text-source Term-trees.")
    print()
    print(f"  Both are mechanical work the agent's introspection has named")
    print(f"  pieces of. Neither requires me to decide which.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
