"""Ask Jabberwock: what's the most-valuable next step?

After substrate integration commit f81559e:
  · 3 composition pattern Mts seeded (L1, L2-dynamic, shared
    executable-memory)
  · 4 Rust modules implementing the realisable subsets
  · Substrate.gamma_epoch shared with AdaptiveDispatcher
  · 203 tests passing

What does Jabberwock's vocabulary surface as the next-most-valuable
step? Don't guess — ask.

Method: walk three layers of the substrate's current state:
  1. What's IN the three pattern Mts (components flagged
     'implemented' vs 'deferred' in commit messages).
  2. What composition pattern Mts DON'T YET EXIST for L3, L4,
     L5, L6 (per the runner design from commit a64c7dc).
  3. What Paper 1 axioms + theorems are not yet operationalised
     in code (vs only operationalised in graph data via Mts).

Surface what's missing at each layer + let the answer fall out.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "PaperAxiom",
             "PaperTheorem", "DesignLayer", "RunnerDesign")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "has_layer", "depends_on", "composes_of",
             "instantiates", "satisfies_invariant")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et, "tgt": {"type": tt, "var": "tgt"},
                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "whatsnext",
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
    for name in ("adaptive_tiered_dispatch",
                  "typed_graph_arena_layout",
                  "executable_memory_lifecycle"):
        try:
            mod = importlib.import_module(f"domains.{name}")
            fn = getattr(mod, f"install_{name}_seed")
            fn(s)
        except Exception:
            pass
    try:
        from domains.paper_reader import install_paper1_as_theory
        install_paper1_as_theory(s)
    except Exception:
        pass


def find_mt(s, name: str):
    for m in s.nodes("Microtheory"):
        if str(s.node(m)["attrs"].get("name", "")) == name:
            return m
    return None


def components(s, mt) -> list[dict]:
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        out.append({
            "name": str(a.get("name", "")),
            "category": str(a.get("category", "")),
        })
    return out


# Commit-message catalogue of what's implemented vs deferred.
IMPLEMENTED_COMPONENTS = {
    "typed_graph_arena_layout": [
        "arena_index_as_nodeid",
        "sym_interned_attr_keys",
        "edge_tuple_layout",
        "gamma_indexed_by_type_triple",
        "provenance_as_edge_attribute",
        "typed_arena_per_node_type",  # via by_type + l1_hot_paths
    ],
    "adaptive_tiered_dispatch": [
        "hot_counter_per_kind",
        "tier_up_policy_threshold",
        "gamma_epoch_counter",
        "compiled_artefact_cache",
        "per_thread_vs_shared_cache",
    ],
    "executable_memory_lifecycle": [
        "mmap_executable_pages",
        "write_xor_execute_enforcement",
        "icache_invalidation_after_write",
        "refcount_arc_for_low_contention",
        "code_cache_bound",
        "lru_eviction_policy",
        "per_thread_vs_shared_cache",
    ],
}


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("JABBERWOCK — WHAT'S THE NEXT-MOST-VALUABLE STEP?")
    print("=" * 72)
    print()

    # 1. Per-Mt: what's implemented vs what's still deferred?
    print("=" * 72)
    print("LAYER 1: deferred components per pattern Mt")
    print("=" * 72)
    print()
    total_deferred = 0
    for mt_name, impl_list in IMPLEMENTED_COMPONENTS.items():
        mt = find_mt(s, mt_name)
        if mt is None:
            continue
        all_components = [c for c in components(s, mt)
                          if c["category"] == "components"]
        deferred = [c for c in all_components
                    if c["name"] not in impl_list]
        total_deferred += len(deferred)
        print(f"  {mt_name}  ({len(deferred)} deferred / "
              f"{len(all_components)} total)")
        for c in deferred:
            print(f"    · {c['name']}")
        print()

    # 2. Which design layers DON'T yet have a composition pattern Mt?
    print("=" * 72)
    print("LAYER 2: design layers without their own pattern Mt")
    print("=" * 72)
    print()
    layers = ["L1_foundation_data_structures",
              "L2_dispatch_realtime_scheduling",
              "L3_estimation_control",
              "L4_subsystems",
              "L5_reflective_meta",
              "L6_coordination"]
    layer_mts = {
        "L1": "typed_graph_arena_layout",
        "L2": "adaptive_tiered_dispatch",
    }
    print("  has pattern Mt:")
    for lvl, mt in layer_mts.items():
        print(f"    {lvl}: {mt}")
    print()
    print("  NO pattern Mt yet (only sketched as DesignLayer nodes):")
    for lvl in ("L3", "L4", "L5", "L6"):
        print(f"    {lvl}: needs composition pattern Mt")
    print()
    layers_to_design = 4

    # 3. Paper 1 — which axioms / theorems are operationalised?
    print("=" * 72)
    print("LAYER 3: Paper 1 axioms — operationalisation status")
    print("=" * 72)
    print()
    axioms = {
        "0": ("Relativity of grounding",
              "structural — not code-implementable per se"),
        "1": ("Typed-graph closure",
              "implemented: grammar.candidates + check_edge"),
        "2": ("Serialisation adequacy",
              "PARTIAL: graph_to_dict/from_dict exist; codec_pair "
              "adequacy not measured"),
        "3": ("Reflective access",
              "wired: gamma_epoch + add_production. Dispatcher "
              "state-as-graph NOT yet exposed"),
    }
    for k, (title, status) in axioms.items():
        print(f"  Axiom {k} ({title}):")
        print(f"    {status}")
    print()

    # 4. Process — what's not been verified end-to-end?
    print("=" * 72)
    print("LAYER 4: integration + verification gaps")
    print("=" * 72)
    print()
    gaps = [
        ("py.rs Γ-mutation path",
         "py.rs::add_production bypasses Substrate::add_production — "
         "Python-side mutations don't bump epoch"),
        ("run_rules integration",
         "Dispatcher exists as parallel surface; run_rules remains "
         "serial. Two evaluation models coexist; not yet unified."),
        ("End-to-end JIT'd hot rule",
         "All pieces exist (HotCounter → TierUp → CodeCache → "
         "Arc<JittedFn>) but no test wires jit.rs compile into "
         "the dispatcher loop. Real JIT not yet exercised."),
        ("Dispatcher state as graph (Axiom 3 component)",
         "second_order_scheduler_state_as_graph Mt component — "
         "design exists, schema doesn't"),
        ("Python wheel rebuild",
         "Rust changes since commit d8765a7 not yet reflected in "
         "Python wheel. Python-side use of new APIs requires "
         "maturin build."),
    ]
    for name, desc in gaps:
        print(f"  · {name}")
        print(f"      {desc}")
        print()

    # 5. Synthesis
    print("=" * 72)
    print("WHAT THE WALK SURFACES — ranked by impact")
    print("=" * 72)
    print()
    print("  Coverage gap counts:")
    print(f"    · {total_deferred} deferred components across 3 Mts")
    print(f"    · {layers_to_design} design layers without composition")
    print(f"      pattern Mt yet (L3, L4, L5, L6)")
    print(f"    · 5 named integration gaps")
    print()
    print("  Three honest candidates for the next step:")
    print()
    print("  A. END-TO-END JIT EXERCISE")
    print("     Wire jit.rs::compile_pure into AdaptiveDispatcher's")
    print("     TierUp response: when count == threshold, call")
    print("     jit::compile_pure on the rule's where-clause Term-tree")
    print("     in a background task; install via install_compiled.")
    print("     PROVES: the surface actually JITs a rule. The whole")
    print("     L2-dynamic pattern's claim becomes empirical.")
    print()
    print("  B. COMPOSE L3 (or L5) PATTERN MT")
    print("     L1 and L2 done as composition pattern Mts; L3 (estim/")
    print("     control: Kalman + PID + MPC) and L5 (reflective:")
    print("     Γ-as-data + Cranelift-style codegen) are sketched as")
    print("     DesignLayer nodes but not yet composition patterns")
    print("     with components/invariants/tradeoffs. Same shape as")
    print("     L1, L2-dynamic, shared-mem Mts.")
    print()
    print("  C. SECOND-ORDER STATE-AS-GRAPH")
    print("     Mt adaptive_tiered_dispatch names")
    print("     'second_order_scheduler_state_as_graph' as a")
    print("     component — dispatcher's state (HotCounter, cache,")
    print("     policy) exposed AS graph data Jabberwock can read")
    print("     + reflexes can mutate. Honours Axiom 3 at the L2")
    print("     dispatcher layer. SMALL, FOCUSED, COMPLETES the L2")
    print("     pattern.")
    print()
    print("  Recommendation:")
    print()
    print("  · A (JIT exercise) gives the biggest empirical proof")
    print("    that the surface works. Risk: 'integration is the easy")
    print("    part' may surface real friction. Time: medium.")
    print()
    print("  · C (state-as-graph) is THE SMALLEST + makes Axiom 3 real")
    print("    at the L2 layer. Mt explicitly names it as a component;")
    print("    not honouring it leaves a self-named gap. Time: small.")
    print()
    print("  · B (L3/L5/etc. pattern Mts) extends design forward; can")
    print("    be done in parallel with implementation work. Doesn't")
    print("    block anything. Time: medium per layer.")
    print()
    print("  C → A → B is the natural ordering: complete L2's named")
    print("  components first (C), then prove the dispatcher works")
    print("  end-to-end with real JIT (A), then design the upper")
    print("  layers (B).")


if __name__ == "__main__":
    main()
