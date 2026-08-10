"""Ask Jabberwock to design dynamic/JIT adaptation for L2.

Per user correction: the agent should design it, not me.

L2's static EDF floor is committed (substrate_rs commit 3c791f8). The
remaining L2 promise is dynamic adaptation:
  · hot-path detection
  · JIT tier-up
  · Γ-change invalidation (Axiom 3 operations on grammar)
  · runtime policy adjustment

Method: walk Jabberwock's vocabulary across the Mts that DESCRIBE
these concerns, surface what's there, let the design fall out from
the substrate's own data.

Relevant Mts to walk:
  · compilers           — JIT, profile-guided opt, hot paths
  · realtime_systems    — dynamic priority, adaptive scheduling
  · optimal_estimation_control — adaptive control (MRAC, STR, gain
                                  scheduling)
  · cybernetics_systems — feedback adaptation
  · reflection_metaprogramming — operations on grammar (Γ change)
  · paper1              — Axiom 3 (reflective access)
  · typed_graph_arena_layout — what L1 already supports
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "PaperAxiom",
             "PaperTheorem", "Directive")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et, "tgt": {"type": tt, "var": "tgt"},
                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "l2dyn",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(",
                              src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (
                           inspect.Parameter.POSITIONAL_ONLY,
                           inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue
    try:
        from domains.paper_reader import install_paper1_as_theory
        install_paper1_as_theory(s)
    except Exception:
        pass
    try:
        from domains.typed_graph_arena_layout import \
            install_typed_graph_arena_layout_seed
        install_typed_graph_arena_layout_seed(s)
    except Exception:
        pass


def find_in_mt(s, mt_name: str, keywords: set[str],
                max_results: int = 25) -> list[dict]:
    mt = None
    for m in s.nodes("Microtheory"):
        if str(s.node(m)["attrs"].get("name", "")).lower() == mt_name:
            mt = m
            break
    if mt is None:
        return []
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name", "")) + " " +
                str(a.get("definition", ""))).lower()
        if any(k in text for k in keywords):
            out.append({
                "name": str(a.get("name", "")),
                "category": str(a.get("category", "")),
                "definition": str(a.get("definition", ""))[:200],
            })
    return out[:max_results]


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("JABBERWOCK: DESIGN DYNAMIC L2 ADAPTATION")
    print("=" * 72)
    print()
    print("  L2 static floor is committed. What does dynamic/JIT")
    print("  adaptation require? Walk specific Mts at the level the")
    print("  question targets — not meta-shapes (that's the previous")
    print("  failure mode); not subsystems either; PRIMITIVES for")
    print("  runtime adaptation.")
    print()

    # Plant the directive
    try:
        s.add_node("Directive", {
            "from": "Matthew Parslow",
            "text": ("Design dynamic L2 adaptation. Hot-path detection, "
                     "JIT tier-up, Γ-change invalidation per Axiom 3, "
                     "runtime policy adjustment. Use compilers + "
                     "realtime_systems + optimal_estimation + "
                     "reflection vocabularies."),
            "scope": "L2_dynamic_adaptation",
        })
    except Exception:
        pass

    # =================================================================
    # Q1: JIT + hot-path machinery from compilers Mt
    # =================================================================
    print("=" * 72)
    print("Q1: JIT + hot-path detection (compilers Mt)")
    print("=" * 72)
    print()
    comp = find_in_mt(s, "compilers",
                      {"jit", "hot", "tier", "profile", "tracing",
                       "specialization", "deoptimization", "guard",
                       "speculation", "inline_cache", "polymorphic"})
    print(f"  Found {len(comp)} relevant concepts:")
    for c in comp[:15]:
        print(f"    · [{c['category'][:18]:<18}] {c['name']}")
        if c['definition']:
            print(f"        {c['definition'][:130]}")
    print()

    # =================================================================
    # Q2: Adaptive control (estimation Mt)
    # =================================================================
    print("=" * 72)
    print("Q2: Adaptive control (optimal_estimation_control Mt)")
    print("=" * 72)
    print()
    adapt = find_in_mt(s, "optimal_estimation_control",
                       {"adaptive", "scheduling", "online",
                        "self_tuning", "reference", "gain"})
    print(f"  Found {len(adapt)} relevant concepts:")
    for c in adapt[:10]:
        print(f"    · [{c['category'][:18]:<18}] {c['name']}")
        if c['definition']:
            print(f"        {c['definition'][:130]}")
    print()

    # =================================================================
    # Q3: Cybernetic adaptation (cybernetics_systems Mt)
    # =================================================================
    print("=" * 72)
    print("Q3: Cybernetic adaptation (cybernetics_systems Mt)")
    print("=" * 72)
    print()
    cyb = find_in_mt(s, "cybernetics_systems",
                     {"adaptation", "feedback", "homeostasis",
                      "variety", "second_order", "circular"})
    print(f"  Found {len(cyb)} relevant concepts:")
    for c in cyb[:10]:
        print(f"    · [{c['category'][:18]:<18}] {c['name']}")
    print()

    # =================================================================
    # Q4: Reflective access (reflection_metaprogramming Mt)
    # =================================================================
    print("=" * 72)
    print("Q4: Γ-as-data + invalidation (reflection_metaprogramming Mt)")
    print("=" * 72)
    print()
    refl = find_in_mt(s, "reflection_metaprogramming",
                      {"grammar", "operation", "intercession",
                       "metaobject", "self_modif", "eval",
                       "quote", "tower"})
    print(f"  Found {len(refl)} relevant concepts:")
    for c in refl[:10]:
        print(f"    · [{c['category'][:18]:<18}] {c['name']}")
    print()

    # =================================================================
    # Q5: RT dynamic priority (realtime_systems Mt)
    # =================================================================
    print("=" * 72)
    print("Q5: Dynamic priority + reconfiguration (realtime_systems Mt)")
    print("=" * 72)
    print()
    rt = find_in_mt(s, "realtime_systems",
                    {"dynamic", "edf", "anytime", "mixed",
                     "deadline_inherit", "mode_change",
                     "schedulability"})
    print(f"  Found {len(rt)} relevant concepts:")
    for c in rt[:10]:
        print(f"    · [{c['category'][:18]:<18}] {c['name']}")
    print()

    # =================================================================
    # Q6: Paper 1 Axiom 3 — the load-bearing requirement
    # =================================================================
    print("=" * 72)
    print("Q6: Paper 1 Axiom 3 — what does it require of L2?")
    print("=" * 72)
    print()
    for ax in s.nodes("PaperAxiom"):
        a = s.node(ax)["attrs"]
        if a.get("label") == "3":
            print(f"  {str(a.get('text', ''))[:800]}")
            break
    print()

    # =================================================================
    # SYNTHESIS
    # =================================================================
    print("=" * 72)
    print("WHAT JABBERWOCK'S DATA SAYS DYNAMIC L2 NEEDS")
    print("=" * 72)
    print()
    print("  Components surfaced by the walk above:")
    print()
    print("  FROM compilers Mt:")
    for c in comp[:6]:
        print(f"    · {c['name']}")
    print()
    print("  FROM optimal_estimation_control Mt:")
    for c in adapt[:5]:
        print(f"    · {c['name']}")
    print()
    print("  FROM reflection_metaprogramming Mt:")
    for c in refl[:5]:
        print(f"    · {c['name']}")
    print()
    print("  FROM realtime_systems Mt:")
    for c in rt[:5]:
        print(f"    · {c['name']}")
    print()
    print("=" * 72)
    print("CAUTION — this is what the vocabulary SHOWS, not a synthesis.")
    print("The next step is for the substrate to COMPOSE these into a")
    print("specific design (named components + invariants + tradeoffs)")
    print("the way typed_graph_arena_layout names the L1 composition.")
    print("=" * 72)


if __name__ == "__main__":
    main()
