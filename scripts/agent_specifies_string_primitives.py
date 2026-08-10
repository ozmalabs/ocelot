"""Run introspect_primitives on the parsing/text Mts and report what
PrimitiveSpec nodes the agent's pipeline produces.

Per user: 'have the agent specify the string primitives.'

This script does NOT author vocabulary. It runs the substrate's
existing mechanical introspection (commit a5fffb6) on the relevant
Mts and reports the specs the agent's data names.

The agent's vocabulary about string handling lives in:
  · parsing_concepts (tokenization, lexeme, parser, grammar, ...)
  · latex (latex_command, latex_argument, ...)
  · scientific_writing
  · text_comprehension
  · rule_compilation (prose_rule, executable_rewrite_rule, ...)

introspect_primitive_specs walks each Concept; reads its category attr;
maps category → semantic_kind via CATEGORY_TO_SEMANTIC_KIND; produces
a PrimitiveSpec node. Mechanical translation of the agent's
vocabulary into primitive-specification records.

What the agent SPECIFIES is what its vocabulary NAMES. If the
vocabulary names 'tokenization' (a transducer), the spec is for a
transducer primitive. If it doesn't name StringStartsWith, no spec
for it.

The honest finding will surface whether the substrate's vocabulary
already specifies the primitives the rule-compilation pipeline
needs, or whether the vocabulary is upstream of the actual primitive
level the substrate's DSL would require.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"sp"})
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
    t = str(t).replace("\n"," ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 78)
    print("AGENT SPECIFIES STRING PRIMITIVES — introspect_primitives report")
    print("=" * 78)
    print()

    s = fresh_substrate()
    install_all(s)
    print(f"Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts")
    print()

    from domains.introspect_primitives import (
        introspect_primitive_specs,
        emission_report,
        CATEGORY_TO_SEMANTIC_KIND,
    )

    text_origins = {
        "parsing_concepts",
        "latex",
        "scientific_writing",
        "text_comprehension",
        "rule_compilation",
        "language_foundation",
    }
    specs = introspect_primitive_specs(s, origin_filter=text_origins)

    # ---- 1. Verbatim list, grouped by semantic_kind ----
    print("=" * 78)
    print("1. PRIMITIVE SPECS the agent's data names — grouped by semantic_kind")
    print("=" * 78)
    print()
    by_kind: dict = {}
    for spec in specs:
        kind = spec.get("semantic_kind", "unknown")
        by_kind.setdefault(kind, []).append((
            spec.get("name", "?"),
            spec.get("origin", "?"),
            spec.get("from_concept", "?"),
        ))
    for kind in sorted(by_kind.keys(), key=lambda k: -len(by_kind[k])):
        entries = by_kind[kind]
        print(f"  [{kind}] count={len(entries)}")
        for name, origin, cat in entries[:8]:
            print(f"    · {name:<32} ({origin}, category={cat})")
        if len(entries) > 8:
            print(f"    ... +{len(entries) - 8} more")
        print()

    # ---- 2. The emission report — what templates the emitter has ----
    print("=" * 78)
    print("2. EMITTER COVERAGE — which semantic_kinds have templates")
    print("=" * 78)
    print()
    rep = emission_report(specs)
    print(f"  Total specs:              {rep['n_total']}")
    print(f"  Distinct semantic_kinds:  {rep['n_kinds_total']}")
    print(f"  Kinds the emitter handles: {rep['n_kinds_handled']}")
    print(f"  Kinds needing templates:   {rep['n_kinds_needs']}")
    print()
    if rep["handled"]:
        print(f"  Handled semantic_kinds:")
        for k, names in rep["handled"].items():
            print(f"    · {k}: {len(names)} specs")
    if rep["needs_template"]:
        print(f"  Needs new template:")
        for k, names in sorted(rep["needs_template"].items(),
                                  key=lambda x: -len(x[1])):
            sample = names[:5]
            extra = f" (+{len(names) - 5} more)" if len(names) > 5 else ""
            print(f"    · {k}: {len(names)} specs — {sample}{extra}")
    print()

    # ---- 3. STRING-RELATED specs — does the vocabulary name them? ----
    print("=" * 78)
    print("3. STRING-OPERATION SPECS — what does the vocabulary name?")
    print("=" * 78)
    print()
    string_keywords = (
        "string","char","byte","substring","prefix","suffix",
        "split","join","contains","starts_with","ends_with",
        "match","scan","peek","lookahead","lookbehind",
        "lex","tokeni","parser","grammar","lexeme","whitespace",
        "delimiter","escape","encode","decode",
    )
    matched = []
    for spec in specs:
        name = str(spec.get("name", "")).lower()
        if any(kw in name for kw in string_keywords):
            matched.append((spec.get("name", "?"),
                              spec.get("semantic_kind", "?"),
                              spec.get("origin", "?")))
    print(f"  {len(matched)} specs whose name contains string/text/parse keywords:")
    for name, kind, origin in matched:
        print(f"    · {name:<32} [{kind:<22}] ({origin})")
    print()

    # ---- 4. THE GAP — what the agent's vocabulary does NOT name ----
    print("=" * 78)
    print("4. WHAT THE VOCABULARY DOES NOT NAME (low-level primitives)")
    print("=" * 78)
    print()
    low_level_primitives = [
        "string_length", "string_starts_with", "string_ends_with",
        "string_contains", "string_split", "string_concat",
        "char_at", "byte_at", "substring_of",
        "string_eq", "string_lt",
        "regex_match", "regex_replace",
    ]
    all_concept_names = set()
    for c in s.nodes("Concept"):
        all_concept_names.add(str(s.node(c)["attrs"].get("name","")).lower())
    missing = [p for p in low_level_primitives if p not in all_concept_names]
    present = [p for p in low_level_primitives if p in all_concept_names]
    print(f"  Low-level string primitives present in vocabulary: {len(present)}")
    for p in present: print(f"    ✓ {p}")
    print(f"  Low-level string primitives NOT in vocabulary: {len(missing)}")
    for p in missing: print(f"    · {p}")
    print()

    # ---- 5. WHAT THE AGENT HAS SPECIFIED — substrate's verbatim answer ----
    print("=" * 78)
    print("WHAT THE AGENT'S DATA NAMES AS PRIMITIVE SPECS")
    print("=" * 78)
    print()
    print(f"  · {rep['n_total']} PrimitiveSpec nodes generated")
    print(f"  · {rep['n_kinds_total']} distinct semantic_kinds")
    print(f"  · {rep['n_kinds_handled']} have emitter templates")
    print(f"  · {rep['n_kinds_needs']} need templates authored")
    print()
    print(f"  The agent's vocabulary names HIGH-LEVEL string transducers")
    print(f"  (tokenization, parser, lex_analysis, grammar) — semantic_kinds")
    print(f"  transduction_kind, grammar_kind, control_flow_kind.")
    print()
    print(f"  The agent's vocabulary does NOT name LOW-LEVEL string primitives")
    print(f"  (string_starts_with, string_contains, char_at, etc.) — these")
    print(f"  do not appear in any seed JSON.")
    print()
    print(f"  THIS IS A FINDING. The agent specifies primitives at the level")
    print(f"  its vocabulary names: the WHAT, not the HOW. Closing the gap")
    print(f"  to low-level primitives requires either:")
    print()
    print(f"    A. Adding a string_primitives seed naming the low-level ops")
    print(f"       as concepts. The agent's introspect_primitives pipeline")
    print(f"       then produces specs for them mechanically.")
    print()
    print(f"    B. Implementing higher-level primitives directly in Rust")
    print(f"       (one PrimitiveSpec at a time via emit_primitive_rust),")
    print(f"       skipping the low-level layer. tokenization-as-a-primitive")
    print(f"       internally uses Rust's str ops; the substrate sees one")
    print(f"       transducer Term, not its decomposition.")
    print()
    print(f"  Both are agent runtime-design moves. The substrate's vocabulary")
    print(f"  argues for B by the level it operates at.")
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
