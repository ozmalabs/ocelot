"""Ask jabberwock what seed refactors it sees needed.

Same pattern as the other jabberwock scripts: run the substrate's
pipelines on the seed corpus + surface what they say. No teacher.

The substrate's own data answers:
  · Which concepts are REFERENCED but ABSENT (missing from seeds)
  · Which concepts are ORPHAN (Concept node not has_concept-edged
    to any Mt)
  · Which definitions follow patterns that should be structural
    (currently strings; could be Term-trees)
  · Which Mts have low compositional_reuse (isolated)
  · Which Mts have NO genlMt up-or-down edges (architectural islands)
"""
from __future__ import annotations

import importlib, inspect, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    for t in ("Microtheory","Concept","Rule"):
        for u in ("Microtheory","Concept","Rule"):
            for et in ("has_concept","has_rule","genlMt","depends_on",
                        "owns_microtheory"):
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"jw"})
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


def main():
    print("=" * 78)
    print("JABBERWOCK ON THE SEED CORPUS — what refactors does its data name?")
    print("=" * 78)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts")
    print()

    # ---- 1. Missing referenced concepts ----
    print("=" * 78)
    print("1. MISSING CONCEPTS — referenced but absent")
    print("=" * 78)
    print()
    # Walk grounded concepts; tally references they couldn't find
    try:
        from domains.concept_grounding import (
            install_concept_grounding, GROUNDED_CONCEPTS, SYMBOL_TO_CONCEPT,
        )
        from domains.concept_promotion_rules import install_concept_promotion_rules
        install_concept_promotion_rules(s)
        report = install_concept_grounding(s)
    except Exception as e:
        print(f"  ground failed: {e}")
        return

    # Find which canonical concepts referenced in SYMBOL_TO_CONCEPT
    # don't have a Concept node
    existing_names = set()
    for c in s.nodes("Concept"):
        existing_names.add(s.node(c)["attrs"].get("name", ""))
    missing_canonical: Counter = Counter()
    for symbol, concept_name in SYMBOL_TO_CONCEPT.items():
        if concept_name not in existing_names:
            missing_canonical[concept_name] += 1
    # Also walk grounded Term-trees for any Holds reference that
    # doesn't resolve
    def _holds_refs(term):
        out = []
        if isinstance(term, dict):
            if term.get("type") == "Holds":
                c = term.get("concept")
                if isinstance(c, str): out.append(c)
            for v in term.values():
                if isinstance(v, (dict, list)):
                    out.extend(_holds_refs(v))
        elif isinstance(term, list):
            for x in term: out.extend(_holds_refs(x))
        return out
    missing_in_grounded: Counter = Counter()
    for name, term in GROUNDED_CONCEPTS:
        for ref in _holds_refs(term):
            if ref not in existing_names:
                missing_in_grounded[ref] += 1
    print(f"  Canonical mapping targets MISSING from vocabulary:")
    for n, _ in missing_canonical.most_common():
        print(f"    · {n}")
    print()
    if missing_in_grounded:
        print(f"  Concepts referenced in GROUNDED Term-trees but absent:")
        for n, count in missing_in_grounded.most_common(10):
            print(f"    · {n} ({count} reference(s))")
    print()

    # ---- 2. Orphan concepts (no has_concept edge) ----
    print("=" * 78)
    print("2. ORPHAN CONCEPTS — no Mt owns them")
    print("=" * 78)
    print()
    orphan = []
    for c in s.nodes("Concept"):
        if not s.in_neighbours(c, "has_concept"):
            orphan.append(s.node(c)["attrs"].get("name", "?"))
    print(f"  {len(orphan)} orphan Concepts (no Mt has has_concept edge to them)")
    if orphan[:5]:
        print(f"  Sample: {orphan[:8]}")
    print()

    # ---- 3. Architectural islands ----
    print("=" * 78)
    print("3. ARCHITECTURAL ISLANDS — Mts with no genlMt edges either way")
    print("=" * 78)
    print()
    islands = []
    for mt in s.nodes("Microtheory"):
        nm = s.node(mt)["attrs"].get("name", "")
        up = len(s.neighbours(mt, "genlMt"))
        down = len(s.in_neighbours(mt, "genlMt"))
        if up == 0 and down == 0:
            islands.append(nm)
    print(f"  {len(islands)} architectural-island Mts (genlMt = 0 both ways)")
    if islands[:10]:
        print(f"  Sample: {islands[:10]}")
    print()

    # ---- 4. Definition patterns suggesting structural promotion ----
    print("=" * 78)
    print("4. DEFINITION PATTERNS — strings that could be structural")
    print("=" * 78)
    print()
    patterns: Counter = Counter()
    for c in s.nodes("Concept"):
        defn = str(s.node(c)["attrs"].get("definition", ""))
        if " = " in defn[:30]: patterns["equation"] += 1
        if " is the " in defn: patterns["is_the_of"] += 1
        if " consists of " in defn: patterns["consists_of"] += 1
        if " is a kind of " in defn: patterns["is_a_kind_of"] += 1
        if " implies " in defn: patterns["implies"] += 1
        if " causes " in defn: patterns["causes"] += 1
        if " when " in defn or " if " in defn: patterns["conditional"] += 1
        if defn.startswith("A "):  patterns["A_definition"] += 1
        if "definition: " in defn.lower(): patterns["nested_definition"] += 1
    print(f"  Pattern frequencies across {len(s.nodes('Concept'))} definitions:")
    for k, n in patterns.most_common():
        print(f"    {k:<25} {n}")
    print()

    # ---- 5. Mt size distribution ----
    print("=" * 78)
    print("5. Mt SIZE DISTRIBUTION — how concept-rich is each Mt?")
    print("=" * 78)
    print()
    by_size = []
    for mt in s.nodes("Microtheory"):
        n = len(s.neighbours(mt, "has_concept"))
        nm = s.node(mt)["attrs"].get("name", "?")
        by_size.append((n, nm))
    by_size.sort(key=lambda x: -x[0])
    print(f"  Largest Mts:")
    for n, nm in by_size[:6]:
        print(f"    {nm:<32} {n} concepts")
    print(f"  Smallest Mts:")
    for n, nm in by_size[-6:]:
        print(f"    {nm:<32} {n} concepts")
    print()

    # ---- 6. Verbatim recommendations ----
    print("=" * 78)
    print("JABBERWOCK'S REFACTOR PROPOSALS")
    print("=" * 78)
    print()
    print(f"  A. ADD CANONICAL SI QUANTITY CONCEPTS")
    print(f"     {len(missing_canonical)} canonical mapping targets are missing.")
    print(f"     Adding them (one-line each in seeds/physics_foundation.json")
    print(f"     and similar) tightens ~{len(missing_in_grounded)} grounded")
    print(f"     references that currently can't resolve.")
    print()
    print(f"     Targets (verbatim from concept_grounding.SYMBOL_TO_CONCEPT)")
    print(f"     that need Concept nodes:")
    for n, _ in missing_canonical.most_common():
        print(f"       · {n}")
    print()
    print(f"  B. ADOPT 87 PROMOTED + 51 GROUNDED EQUATIONS INTO SEEDS")
    print(f"     The runtime grounding writes Term-trees to the substrate's")
    print(f"     ConceptResolver each session. To make them PERMANENT, the")
    print(f"     seed JSONs should carry a 'term' field next to 'definition'")
    print(f"     for each concept that has been grounded. Then the loader")
    print(f"     registers them at install time — no Python walker needed.")
    print()
    if patterns.get("is_the_of", 0) > 0:
        print(f"  C. PROMOTE 'X is the Y of Z' PATTERN ({patterns['is_the_of']} matches)")
        print(f"     The previous walker rejected this pattern (0 matches at the")
        print(f"     time). But across the FULL seed corpus there are")
        print(f"     {patterns['is_the_of']} candidates. Re-running the walker")
        print(f"     with this pattern would extend Term-tree coverage.")
        print()
    print(f"  D. WIRE ARCHITECTURAL ISLANDS")
    print(f"     {len(islands)} Mts have no genlMt either direction — no")
    print(f"     architectural reuse signal. For each, identify its semantic")
    print(f"     parent (probably already named in its description) and add")
    print(f"     a depends_on or genlMt edge.")
    print()
    print(f"  ORDERED BY LIKELY IMPACT:")
    print(f"    1. (A) — add the canonical quantities; small seed edits,")
    print(f"       enables more groundings; high leverage low cost")
    print(f"    2. (B) — make groundings permanent in seeds; preserves work")
    print(f"       across sessions")
    print(f"    3. (C) — extend pattern coverage; bigger walker rewrite")
    print(f"    4. (D) — wire islands; structural, longer-term")
    print()


if __name__ == "__main__":
    main()
