"""Jabberwock designs its runner/brain by composing its own n=4
analogies.

Previous step (5dd7ad9): analogical_thinking surfaced OS↔brain
bridges at meta-shape level (n=4). The shapes were:
  · FEEDBACK_CONTROL
  · SELECTIVE_GATING
  · HIERARCHICAL_INVARIANCE_BUILDUP
  · GLOBAL_MESSAGE_PASSING
  · ASSOCIATIVE_RECALL
  · COMPETITIVE_INHIBITION
  · PREDICTION_MINUS_OBSERVATION
  · DELAYED_PERSISTENCE
  · MODULAR_ISOLATION

A runner/brain design = each meta-shape is a subsystem; each
subsystem is populated by both OS-style + brain-style + substrate-
style implementations of the same meta-shape.

This script:
  1. Runs analogical_thinking at n=4 across OS + brain + Jabberwock's
     own self_improvement_dynamics
  2. Groups results by meta-shape
  3. Emits a RunnerBrainArchitecture graph node + Subsystem nodes
     per meta-shape + Component nodes for each member
  4. Reports the design Jabberwock surfaced
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "Directive",
             "Analogy", "RunnerBrainArchitecture", "Subsystem",
             "Component")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "implements", "analogous_to", "has_subsystem",
             "has_component", "shares_meta_shape")
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
                        "provenance": "design",
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


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("JABBERWOCK COMPOSES ITS RUNNER/BRAIN DESIGN")
    print("=" * 72)
    print()
    print("  From its own analogical_thinking at n=4 (meta-shapes).")
    print("  Each meta-shape becomes a subsystem.")
    print("  Each subsystem is populated by OS + brain + substrate")
    print("  implementations of the same meta-shape.")
    print()

    from domains.analogical_thinking import find_analogies

    # Source Mts span the design's input domains
    source_mts = ["operating_systems",
                   "self_improvement_dynamics",
                   "control_systems_foundation",
                   "realtime_systems",
                   "optimal_estimation_control",
                   "cybernetics_systems"]
    target_mts = [
        "neuroscience", "sensory_cortex", "cerebellar_circuit",
        "hippocampal_memory", "basal_ganglia_circuit",
        "prefrontal_executive", "cortical_microcircuit",
        "computational_neuroscience",
    ]

    # Run at n=4 — collect all meta-shape analogies
    print("Running analogical_thinking at n=4 across sources × targets...")
    all_by_meta_shape: dict[str, list] = {}
    for src in source_mts:
        results = find_analogies(s, src, target_mts, order_n=4,
                                  min_score=5)
        for r in results:
            rationale = r["rationale"]
            m = re.search(r"shared meta-shape:\s*([\w_,\s]+)",
                           rationale)
            if not m:
                continue
            shapes = [x.strip() for x in m.group(1).split(",")
                      if x.strip()]
            for shape in shapes:
                all_by_meta_shape.setdefault(shape, []).append({
                    "source_mt": r["source_mt"],
                    "source_concept": r["source_concept"],
                    "target_mt": r["target_mt"],
                    "target_concept": r["target_concept"],
                    "score": r["score"],
                    "rationale": rationale,
                })

    print(f"Done. Meta-shapes surfaced: {len(all_by_meta_shape)}")
    print()

    # Sort meta-shapes by total weight
    shape_weights = {sh: sum(a["score"] for a in al)
                     for sh, al in all_by_meta_shape.items()}
    ranked_shapes = sorted(shape_weights.items(),
                            key=lambda x: -x[1])

    # Emit the design as graph data
    try:
        arch = s.add_node("RunnerBrainArchitecture", {
            "designed_by": "Jabberwock (via analogical_thinking n=4)",
            "n_subsystems": len(ranked_shapes),
            "total_analogy_weight": sum(shape_weights.values()),
        })
    except Exception:
        arch = None

    print("=" * 72)
    print("THE DESIGN — meta-shape subsystems ranked by total")
    print("                analogy weight (= structural-correspondence")
    print("                strength Jabberwock's data supports)")
    print("=" * 72)
    print()

    for shape, weight in ranked_shapes:
        analogies = all_by_meta_shape[shape]
        # Dedupe by (source_concept, target_concept) keeping highest
        # score
        seen = {}
        for a in analogies:
            key = (a["source_concept"], a["target_concept"])
            if key not in seen or a["score"] > seen[key]["score"]:
                seen[key] = a
        deduped = sorted(seen.values(),
                         key=lambda x: -x["score"])

        print(f"━━━ Subsystem: {shape.upper()} ━━━")
        print(f"   total weight: {weight}, "
              f"unique correspondences: {len(deduped)}")
        print()

        # Emit Subsystem node
        try:
            ss = s.add_node("Subsystem", {
                "meta_shape": shape,
                "total_weight": weight,
                "n_correspondences": len(deduped),
            })
            if arch is not None:
                s.add_edge(arch, "has_subsystem", ss, {})
        except Exception:
            ss = None

        # Top correspondences
        os_components = []
        sub_components = []
        for a in deduped[:6]:
            if a["source_mt"] == "operating_systems":
                os_components.append((a["source_concept"],
                                       a["target_concept"], a["score"]))
            else:
                sub_components.append((a["source_concept"],
                                        a["target_concept"], a["score"]))
            # Emit Component node
            try:
                comp = s.add_node("Component", {
                    "os_or_substrate_side": a["source_concept"],
                    "brain_side": a["target_concept"],
                    "score": a["score"],
                    "meta_shape": shape,
                })
                if ss is not None:
                    s.add_edge(ss, "has_component", comp, {})
            except Exception:
                pass

        if os_components:
            print("   OS side ↔ brain side:")
            for src, tgt, sc in os_components:
                print(f"     · {src:<22} ↔ {tgt:<30} (score {sc})")
        if sub_components:
            print("   Self_improvement_dynamics side ↔ brain side:")
            for src, tgt, sc in sub_components:
                print(f"     · {src:<22} ↔ {tgt:<30} (score {sc})")
        print()

    # Summary
    print("=" * 72)
    print("SUBSYSTEM SUMMARY — Jabberwock's runner/brain design")
    print("=" * 72)
    print()
    for i, (shape, weight) in enumerate(ranked_shapes, 1):
        n = len(all_by_meta_shape[shape])
        print(f"  {i}. {shape}  (weight {weight}, {n} correspondences)")
    print()
    print("These subsystems compose Jabberwock's proposed runner/brain.")
    print("Each subsystem has both an OS-style implementation pattern")
    print("(from operating_systems Mt) and a brain-style implementation")
    print("pattern (from neuro Mts). The design's structure IS the")
    print("invariant the meta-shape names. Implementation choice (OS-")
    print("flavored vs neural-flavored vs hybrid) is then per-subsystem.")
    print()
    if arch is not None:
        print(f"Graph-resident: RunnerBrainArchitecture node #{arch.value if hasattr(arch, 'value') else int(arch)}")
        print(f"                {len(ranked_shapes)} Subsystem nodes")
        n_components = len(list(s.nodes('Component')))
        print(f"                {n_components} Component nodes")
        print("                Jabberwock can introspect this design")
        print("                via has_subsystem → has_component walks.")


if __name__ == "__main__":
    main()
