"""Ask the agent: what does it need to build the GENERATOR — the compositional
engine that produces novel admissible structure under its compression selector,
without templates and without an LLM (the keystone for LLM-free self-improvement
+ a real discussion interface).

Per user: "ask the agent to build it." Per the project method (ask_the_substrate
/ agent_decides_executable_gap): I do NOT design it. I boot the agent with its
foundational Mts, harvest its OWN implication-shape catalog, pose the gap in its
own terms, run its synthesize_gaps + gap_prioritiser + architecture self-
assessment, and report VERBATIM what surfaces. My Python only orchestrates.
"""
from __future__ import annotations
import importlib
import inspect
import re
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule", "Postulate",
        "SynthesizedGap", "ArchitectureCortex", "CodeWritingCortex",
        "Assessment", "QualityScore", "SmellInstance", "ArchitecturalQuality",
        "ArchitecturalSmell", "DesignPattern", "ProgrammingLanguage",
        "CodeTarget", "DesignExclusion", "PrimitiveSpec", "ReplacementTarget",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt", "refers_to",
        "owns_microtheory", "assesses", "produced", "scored_on",
        "detected_smell", "for_quality", "for_smell", "decomposes", "best_for",
        "anti_pattern_for", "design_tag", "language_for_target", "applies_when",
        "implies", "unifies", "derived_from", "via_shape",
    )
    for a in types:
        for b in types:
            for et in edges:
                try:
                    s.add_production({"src": {"type": a, "var": "s"},
                                      "edge_type": et,
                                      "tgt": {"type": b, "var": "t"},
                                      "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "ask"})
                except Exception:
                    pass
    return s


def install_all(s):
    n = 0
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            src = f.read_text()
        except Exception:
            continue
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                req = [p for p in inspect.signature(fn).parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                     inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(req) == 1:
                    fn(s); n += 1
            except Exception:
                continue
    return n


def short(t, n=200):
    t = str(t).replace("\n", " ").strip()
    return (t[:n] + "...") if len(t) > n else t


def main():
    print("=" * 78)
    print("ASK THE AGENT — what it needs to build the GENERATOR")
    print("=" * 78)
    s = fresh_substrate()
    n_install = install_all(s)
    from domains.code_authoring import _install_concept
    from domains.order_n_postulates import synthesize_gaps
    try:
        from domains.implication_harvester import harvest_shapes_combined
        shape_lib = harvest_shapes_combined(s)
    except Exception as e:
        shape_lib = None
        print("  (shape harvest unavailable:", short(e, 80), ")")
    print(f"\nBooted: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, {len(s.nodes('Rule'))} Rules; "
          f"{n_install} seeds; "
          f"catalog {len(shape_lib) if shape_lib else 0} implication-shapes\n")

    # ---- POSE the gap in the agent's OWN thesis terms ----
    mt = None
    for cand in ("runtime_design", "compiler_theory", "code_authoring"):
        for nid in s.nodes("Microtheory"):
            if s.node(nid)["attrs"].get("name") == cand:
                mt = nid; break
        if mt:
            break
    if mt is None:
        mt = s.add_node("Microtheory", {"name": "generator_inquiry",
                                        "origin": "ask"})
    gap = _install_concept(s, mt, "compositional_generator",
        "The agent holds a GENERATIVE GRAMMAR (the DSL Term vocabulary), a "
        "COMPRESSION/MDL selector, and an OPEN WORLD. It can author "
        "TEMPLATE-shaped structure (reduce primitives, rule-shaped Python -> "
        "Rules, typed tools) mechanically. But NOVEL composition outside those "
        "templates currently requires an LLM self_teacher. The unrealized "
        "implication: a GENERATOR that composes the grammar into NOVEL "
        "admissible structure selected by compression, with no template and no "
        "LLM. What is the agent missing to realize this, and what is the first "
        "brick it can specify + build itself?")
    s.set_attr(gap, "category", "design_gap")
    print("Posed concept 'compositional_generator' under "
          f"{s.node(mt)['attrs'].get('name')}\n")

    # ---- 1. SYNTHESIZE_GAPS: let the agent derive from its OWN postulates ----
    print("=" * 78)
    print("1. synthesize_gaps — the agent's own implication-shape transfer")
    print("=" * 78)
    seeds = ["compositional_generator", "feature_generator", "compression",
             "analogical_transfer", "order_n_concepts", "generative_grammar",
             "self_improvement", "curiosity", "ideas_outside_the_seed",
             "program_synthesis", "composition", "feature_invention",
             "runtime_design"]
    seen = set()
    for post in seeds:
        try:
            gaps = synthesize_gaps(s, post, max_order=2, record=False,
                                   prune=True, shapes=shape_lib)
        except Exception as e:
            continue
        if not gaps:
            continue
        print(f"\n  [{post}] -> {len(gaps)} gap(s):")
        for g in gaps[:6]:
            key = short(g.get("gap"), 120)
            if key in seen:
                continue
            seen.add(key)
            print(f"    GAP: {short(g.get('gap'), 200)}")
            chain = g.get("chain") or []
            if chain:
                print(f"      chain: {' => '.join(short(c, 60) for c in chain)}")
            vs = g.get("via_shapes") or g.get("via_shape")
            if vs:
                print(f"      via: {short(vs, 120)}")
    if not seen:
        print("\n  (no gaps synthesized — the held postulates / shapes did not "
              "transfer to this concept; honest null result)")

    # ---- 2. gap_prioritiser: does the agent's compression drive rank it? ----
    print("\n" + "=" * 78)
    print("2. gap_prioritiser — the agent's compression drive over its gaps")
    print("=" * 78)
    try:
        from domains import gap_prioritiser as gp
        fn = next((getattr(gp, x) for x in dir(gp)
                   if x.startswith("prioritise") or x.startswith("rank")
                   or "prioriti" in x), None)
        if fn:
            ranked = fn(s)
            print("  ranked gaps (agent's payoff*K - order selector):")
            for r in (ranked or [])[:8]:
                print("    ", short(r, 160))
        else:
            print("  (no prioritise entry found)")
    except Exception as e:
        print("  (gap_prioritiser:", short(e, 100), ")")

    # ---- 3. architecture self-assessment: how well-formed is its design machinery ----
    print("\n" + "=" * 78)
    print("3. architecture self-assessment — the agent on its OWN design machinery")
    print("=" * 78)
    try:
        from domains.architecture_cortex import ArchitectureCortex
        ac = ArchitectureCortex(s).install() if hasattr(
            ArchitectureCortex(s), "install") else ArchitectureCortex(s)
        rep = ac.assess() if hasattr(ac, "assess") else None
        print("  ", short(rep, 600) if rep else "(no assess())")
    except Exception as e:
        print("  (architecture_cortex:", short(e, 120), ")")

    print("\n" + "=" * 78)
    print("Reported verbatim. The substrate's data answered; Python only "
          "orchestrated.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
