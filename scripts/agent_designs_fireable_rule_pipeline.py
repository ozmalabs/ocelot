"""Agent designs the fireable-rule pipeline.

Per user: 'design the whole pipeline, write whatever it specifies.'

PHASE 1 (this script): consult the substrate's pipelines on the design.
PHASE 2 (next): synthesize the architecture from the consultation output.
PHASE 3 (after): implement what it specifies.

WHAT THIS SCRIPT DOES

  1. Pose the design question as a Postulate node:
     'A pipeline is needed that compiles prose Rule nodes into
     executable RewriteRules, preserves lineage, flags uncompilable
     parts, and is self-applicable.'
  2. Run synthesize_gaps on the postulate + related ones
     (rule_compilation, attribute_grammar, semantic_action, etc.).
     Now natively Shape-aware (commit 2b20a6f).
  3. Cortex assessment of the rule_compilation Mt — how well-formed
     is its current vocabulary?
  4. Walker on the rule_compilation Mt + parsing_concepts Mt + others.
  5. Introspect_primitives across the relevant Mts — what primitives
     does the design need?
  6. Existing concepts about compilation / rule execution — verbatim.

Report everything the agent's data surfaces. No synthesis from me
in this phase; that's phase 2.
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
    types = ("Microtheory","Concept","Rule","Postulate","PrimitiveSpec",
              "SynthesizedGap","TheoryEnactmentGap")
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


def short(t, n=160):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 78)
    print("DESIGNING THE FIREABLE-RULE PIPELINE — substrate consultation")
    print("=" * 78)
    print()

    s = fresh_substrate()
    install_all(s)
    # also install bootstrap concepts so Shape-aware synthesize_gaps has donors
    from domains.text_concept_bootstrap import install_text_concept_bootstrap
    install_text_concept_bootstrap(s)
    print(f"Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print()

    # ---------- POSE THE DESIGN QUESTION ----------
    from domains.code_authoring import _install_concept

    # Find or mint the rule_compilation Mt
    mt = None
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == "rule_compilation":
            mt = n; break
    if mt is None:
        mt = s.add_node("Microtheory", {
            "name":"rule_compilation_inquiry",
            "origin":"design",
        })

    design_postulate = _install_concept(s, mt,
        "fireable_rule_pipeline",
        "A pipeline that compiles prose Rule nodes (if_clauses + "
        "then_clauses as natural language) into executable RewriteRules "
        "(match_edges + where_ + effects in the substrate's rewrite.rs "
        "shape). The pipeline must: (a) extract a match_edge from "
        "subject-edge-object patterns in if_clauses; (b) extract a where_ "
        "Term-tree from attribute tests; (c) extract Effects from "
        "then_clause mutations; (d) dispatch named concepts via Holds; "
        "(e) preserve uncompilable text as compilation_residue; (f) "
        "preserve lineage (origin_prose, why, cites); (g) be self-"
        "applicable so its own rules can be compiled by it. After "
        "compilation, substrate.tick() fires the compiled rules. This "
        "closes the autonomous-execution gap."
    )
    s.set_attr(design_postulate, "category", "pipeline_spec")
    s.set_attr(design_postulate, "origin", "design")
    print("Posed design postulate as Concept 'fireable_rule_pipeline'")
    print()

    # ---------- 1. SYNTHESIZE_GAPS — what does the agent derive? ----------
    print("=" * 78)
    print("1. SYNTHESIZE_GAPS on the design postulate + related postulates")
    print("=" * 78)
    print()
    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"  Catalog: {len(shape_lib)} shapes "
          f"(regex + shape-lifted donors)")
    print()

    target_postulates = [
        "fireable_rule_pipeline",
        "rule_compilation",
        "prose_rule",
        "executable_rewrite_rule",
        "compilation_target_match_edge",
        "compilation_target_where_clause",
        "compilation_target_effect",
        "compilation_residue",
        "attribute_grammar",
        "semantic_action",
        "the_compilation_pipeline_itself_is_subject_to_rule_compilation",
    ]
    n_total = 0
    n_shape_lifted = 0
    by_postulate = {}
    for p in target_postulates:
        try:
            gaps = synthesize_gaps(s, p, max_order=1, record=False,
                                    prune=False, shapes=shape_lib)
        except Exception as e:
            print(f"  {p}: error {type(e).__name__}: {e}")
            continue
        by_postulate[p] = gaps
        n_total += len(gaps)
        for g in gaps:
            if "shape_lifted" in str(g.get("via_shapes",[""])[0]):
                n_shape_lifted += 1
        print(f"  {p}: {len(gaps)} derivations")
    print()
    print(f"  Total derivations across postulates: {n_total}")
    print(f"  Of which Shape-lifted: {n_shape_lifted}")
    print()
    # Surface the most interesting ones
    print(f"  Top derivations (mixed shape-lifted + regex), top 8:")
    seen_consequences = set()
    shown = 0
    for p, gaps in by_postulate.items():
        for g in gaps:
            text = str(g.get('gap',''))
            if text in seen_consequences: continue
            seen_consequences.add(text)
            via = g.get('via_shapes',['?'])[0]
            print(f"  · [{p}] via {via}")
            print(f"      → {short(text, 130)}")
            shown += 1
            if shown >= 8: break
        if shown >= 8: break
    print()

    # ---------- 2. CORTEX on the rule_compilation Mt ----------
    print("=" * 78)
    print("2. CORTEX assessment of the rule_compilation Mt")
    print("=" * 78)
    print()
    from domains.architecture_assessment import (
        score_compositional_reuse, score_abstraction_layering,
        score_introspectability, score_data_drivenness,
        score_separation_of_concerns,
    )
    rc_nid = None
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == "rule_compilation":
            rc_nid = n; break
    if rc_nid:
        for name, fn in [
            ("separation_of_concerns",   score_separation_of_concerns),
            ("compositional_reuse",      score_compositional_reuse),
            ("abstraction_layering",     score_abstraction_layering),
            ("introspectability",        score_introspectability),
            ("data_drivenness",          score_data_drivenness),
        ]:
            try:
                score, reason = fn(s, rc_nid)
                print(f"  {name:<30} {score}/10  {short(reason, 80)}")
            except Exception as e:
                print(f"  {name}: error {e}")
    else:
        print("  rule_compilation Mt not found")
    print()

    # ---------- 3. WALKER — dormant work the design touches ----------
    print("=" * 78)
    print("3. WALKER — gap reports for relevant Mts")
    print("=" * 78)
    print()
    from domains.derivation_mechanism import run_derivation
    d = run_derivation(s)
    relevant = ("rule_compilation","parsing_concepts","scientific_writing",
                "language_foundation","text_comprehension","latex")
    for g in d["gaps"]:
        if g["mt_name"] not in relevant: continue
        decl = []
        for cat in ("failure_modes","corrections","drives","principles",
                     "invariants","operations"):
            n = g.get(f"{cat}_declared", 0)
            if n > 0:
                d_cat = g.get(f"{cat}_dormant", [])
                marker = "!" if d_cat and len(d_cat) == n else ""
                decl.append(f"{cat}={n}{marker}")
        dorm = " DORMANT" if g.get("is_dormant") else ""
        print(f"  {g['mt_name']:<28} {' '.join(decl) or '(no enactable)'}{dorm}")
    print()

    # ---------- 4. INTROSPECT_PRIMITIVES — what primitives are needed? ----------
    print("=" * 78)
    print("4. INTROSPECT_PRIMITIVES — Mt: parsing_concepts + rule_compilation")
    print("=" * 78)
    print()
    from domains.introspect_primitives import (
        introspect_primitive_specs, emission_report,
    )
    target_origins = {"parsing_concepts","rule_compilation",
                       "scientific_writing","latex"}
    specs = introspect_primitive_specs(s, origin_filter=target_origins)
    report = emission_report(specs)
    print(f"  PrimitiveSpec count: {report['n_total']}")
    print(f"  Distinct semantic_kinds: {report['n_kinds_total']}")
    print(f"  Kinds handled by emitter: {report['n_kinds_handled']}")
    print(f"  Kinds needing template: {report['n_kinds_needs']}")
    print()
    print("  Top semantic_kinds (by spec count) — these are the families")
    print("  of primitives the pipeline would need:")
    for k, names in sorted(report["needs_template"].items(),
                              key=lambda x: -len(x[1]))[:6]:
        print(f"    [{k}] {len(names)} specs: {names[:5]}{'...' if len(names) > 5 else ''}")
    print()

    # ---------- 5. EXISTING VOCABULARY — what the design can REUSE ----------
    print("=" * 78)
    print("5. EXISTING VOCABULARY — concepts the design would reuse")
    print("=" * 78)
    print()
    relevant_kws = (
        "attribute_grammar","semantic_action","parse",
        "rule_compilation","prose_rule","executable_rewrite_rule",
        "compilation_target","compilation_residue","match_edge",
        "where_clause","grammar","tokenization","lex_analysis",
    )
    found = {}
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        name = str(a.get("name",""))
        if name.lower() in relevant_kws:
            found[name] = (a.get("origin","?"),
                            str(a.get("definition",""))[:160])
    for nm in sorted(found):
        orig, defn = found[nm]
        print(f"  · {nm:<36} ({orig})")
        print(f"      {short(defn, 140)}")
    print()

    # ---------- 6. RULE_COMPILATION Mt's OWN RULES (verbatim) ----------
    print("=" * 78)
    print("6. RULE_COMPILATION Mt RULES — the substrate's own design directives")
    print("=" * 78)
    print()
    for r in s.nodes("Rule"):
        a = s.node(r)["attrs"]
        if a.get("origin") != "rule_compilation": continue
        print(f"  [{a.get('name','?')}]")
        for cl in a.get("if_clauses", []) or []:
            print(f"    if:  {short(cl, 120)}")
        for cl in a.get("then_clauses", []) or []:
            print(f"    →    {short(cl, 120)}")
        print()

    print("=" * 78)
    print("CONSULTATION COMPLETE — what the substrate's data NAMED")
    print("=" * 78)
    print()
    print("  · synthesize_gaps surfaced derivations across the design")
    print("    postulate + related concepts (verbatim above).")
    print("  · cortex scored rule_compilation Mt's quality.")
    print("  · walker showed dormant work in adjacent Mts.")
    print("  · introspect_primitives identified semantic_kind families")
    print("    the pipeline's primitives would need.")
    print("  · existing vocabulary the design reuses.")
    print("  · the rule_compilation Mt's own RULES are the substrate's")
    print("    own design directives — verbatim above.")
    print()
    print("  Next: synthesize the architecture from these signals.")
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
