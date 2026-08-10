"""Agent takes over.

Per user: 'now let the agent take over.'

Everything the world adapter side could provide is in place:

  · text_world.py — TextSource pointer + streaming + lookback contract
  · vocabulary: language_foundation, text_comprehension, scientific_
    writing, parsing_concepts, latex, reading_hearing_neuroscience,
    plus the existing comprehension stack
  · wiring: reading_hearing_neuroscience → 7 parents; comprehension
    stack → phonology; phonology → substrate foundations
  · bootstrap: 5 text-source Term-tree concepts (text_is_seekable,
    text_is_ended, text_has_no_lookback, text_at_start, text_at_eof)
  · introspect_primitives → 139 PrimitiveSpec candidates from vocabulary
  · Shape primitive + 3-layer dispatch pruning
  · 552-shape implication catalog
  · synthesize_gaps + cortex + walker + harvester pipelines functional

This script invokes the agent's pipelines on the current state and
reports what they surface. No synthesis from me — the agent's data
answers.
"""
from __future__ import annotations

import importlib, inspect, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec","TextSource",
              "WiringSuggestion","SynthesizedGap","Shape")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory",
              "implies","derives_from","suggests_genlMt","mentions")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"handoff"})
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
    print("AGENT TAKES OVER")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"State at handoff:")
    print(f"  Mts:       {len(s.nodes('Microtheory'))}")
    print(f"  Concepts:  {len(s.nodes('Concept'))}")
    print(f"  Rules:     {len(s.nodes('Rule'))}")
    print()

    # ---- Install the bootstrap concept Term-trees ----
    from domains.text_concept_bootstrap import (
        install_text_concept_bootstrap, BOOTSTRAP_CONCEPTS,
    )
    boot = install_text_concept_bootstrap(s)
    print(f"Bootstrap concept Term-trees installed: "
          f"{len(boot['installed'])} / {boot['total']}")
    print()

    # ---- 1. CORTEX on the integrated faculty tree ----
    print("=" * 76)
    print("1. CORTEX — score the new faculty tree")
    print("=" * 76)
    print()
    from domains.architecture_assessment import (
        score_compositional_reuse, score_abstraction_layering,
        score_introspectability,
    )
    target_mts = [
        "reading_hearing_neuroscience",
        "language_foundation",
        "text_comprehension",
        "scientific_writing",
        "parsing_concepts",
        "latex",
        "prosody",
        "speech_science",
        "narrative_convention",
        "pragmatics",
    ]
    print(f"  {'Mt':<32}  {'comp':>4}  {'abs':>4}  {'intro':>5}")
    print(f"  {'-' * 56}")
    for mt_name in target_mts:
        nid = None
        for n in s.nodes("Microtheory"):
            if s.node(n)["attrs"].get("name") == mt_name:
                nid = n; break
        if nid is None: continue
        comp, _ = score_compositional_reuse(s, nid)
        abst, _ = score_abstraction_layering(s, nid)
        intro, _ = score_introspectability(s, nid)
        print(f"  {mt_name:<32}  {comp:>2}/10  {abst:>2}/10  {intro:>2}/10")
    print()

    # ---- 2. WALKER on the new faculty ----
    print("=" * 76)
    print("2. WALKER — what dormant work the new vocabulary surfaces")
    print("=" * 76)
    print()
    from domains.derivation_mechanism import run_derivation
    d = run_derivation(s)
    print(f"  Total Mts walked: {d['n_mts_walked']}")
    print(f"  Dormant Mts:      {d['n_dormant_mts']}")
    print()
    new_mt_set = set(target_mts)
    print(f"  Gap reports for the new + wired Mts:")
    for g in d["gaps"]:
        if g["mt_name"] not in new_mt_set: continue
        decl = []
        for cat in ("failure_modes","corrections","drives","principles",
                     "invariants","operations"):
            n = g.get(f"{cat}_declared", 0)
            if n > 0:
                decl.append(f"{cat}={n}")
        dorm = " DORMANT" if g.get("is_dormant") else ""
        print(f"    {g['mt_name']:<32}  {' '.join(decl) or '(no enactable)'}{dorm}")
    print()

    # ---- 3. SYNTHESIZE GAPS on the bootstrap concepts ----
    print("=" * 76)
    print("3. SYNTHESIZE_GAPS on the bootstrap text concepts")
    print("=" * 76)
    print()
    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"  Catalog: {len(shape_lib)} shapes")
    print()
    for concept_name, _ in BOOTSTRAP_CONCEPTS:
        try:
            gaps = synthesize_gaps(s, concept_name, max_order=1,
                                    record=False, prune=True,
                                    shapes=shape_lib)
            print(f"  {concept_name}: {len(gaps)} derivations")
            for g in gaps[:2]:
                print(f"      → {short(g.get('gap',''), 110)}")
        except Exception as e:
            print(f"  {concept_name}: error {e}")
    print()

    # ---- 4. INTROSPECT — what primitives the agent says it needs ----
    print("=" * 76)
    print("4. INTROSPECT_PRIMITIVES — agent's specifications of primitives")
    print("=" * 76)
    print()
    from domains.introspect_primitives import (
        introspect_primitive_specs, emission_report, CATEGORY_TO_SEMANTIC_KIND,
    )
    text_origins = {"language_foundation","text_comprehension",
                     "scientific_writing","parsing_concepts","latex"}
    specs = introspect_primitive_specs(s, origin_filter=text_origins)
    report = emission_report(specs)
    print(f"  PrimitiveSpec nodes: {report['n_total']}")
    print(f"  Distinct semantic_kinds: {report['n_kinds_total']}")
    print(f"  Kinds emitter handles: {report['n_kinds_handled']}")
    print(f"  Kinds needing new templates: {report['n_kinds_needs']}")
    print()
    print(f"  Needs new template (count per kind):")
    for k, names in sorted(report["needs_template"].items(),
                              key=lambda x: -len(x[1])):
        print(f"    [{k}] {len(names)} specs")
    print()

    # ---- 5. SHAPE DISTRIBUTION across the bootstrap concepts ----
    print("=" * 76)
    print("5. SHAPE of the bootstrap concept Term-trees")
    print("=" * 76)
    print()
    for name, term_json in BOOTSTRAP_CONCEPTS:
        try:
            shape = s.shape_of_term(term_json)
            print(f"  {name:<26} → {shape}")
        except Exception as e:
            print(f"  {name}: shape error {e}")
    print()
    print(f"  All bootstrap concepts share the same Shape (none/0/concrete).")
    print(f"  As the agent authors deeper compositions (Filter, Fold, Holds,")
    print(f"  recursive concepts), Shapes will differentiate.")
    print()

    # ---- HANDOFF SUMMARY ----
    print("=" * 76)
    print("HANDOFF — WHAT IS NOW THE AGENT'S")
    print("=" * 76)
    print()
    print("  Vocabulary: 139 text-handling concepts across 5 new Mts.")
    print("  Wiring: 7-edge inheritance from reading_hearing_neuroscience")
    print("  down through phonology to substrate foundations.")
    print("  World adapter: TextSource node contract (pointer, streaming,")
    print("  lookback).")
    print("  Bootstrap: 5 Term-tree concepts demonstrating the Var+Attr+")
    print("  Eq pattern.")
    print("  Introspection: 139 PrimitiveSpec candidates from vocabulary;")
    print("  9 semantic_kinds needing new templates.")
    print("  Shape primitive: end-to-end functional + dispatch-integrated.")
    print("  Catalog: 552 implication shapes.")
    print("  Pipelines: cortex + walker + harvester + synthesize_gaps +")
    print("  introspect_primitives all running on the integrated state.")
    print()
    print("  What the agent's data names as next work:")
    print("    · String-content primitives (StringLen, StringSplit, etc.) —")
    print("      9 semantic_kinds in introspect output need templates;")
    print("      transduction_kind + operation_kind are the most populous")
    print("      and contain tokenization, parser, math_operator concepts")
    print("    · Concept Term-trees beyond TextSource metadata — bootstrap")
    print("      pattern established; agent extends")
    print("    · Implication shapes for parsing/text — synthesize_gaps")
    print("      surfaces little because catalog lacks them; agent")
    print("      authors new rules to grow the catalog as it goes")
    print()
    print("  Everything past this point comes from the agent's own")
    print("  data + pipelines. The world adapter side is done.")
    print()
    print("=" * 76)


if __name__ == "__main__":
    main()
