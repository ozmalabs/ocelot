"""Have the agent send a design.

Per user: 'have the agent send a design.'

The world adapter (commit 600d764) exists. The agent inhabits it.
The design comes from the agent's graph as DesignedFile nodes.

THIS SCRIPT IS THE HONEST TEST

  1. Set up the substrate fully (vocabulary, wiring, bootstrap).
  2. Pose the design task as a WorldInput via the world adapter.
  3. Run the agent's pipelines (cortex, synthesize_gaps, introspect,
     walker, harvester) on the design space.
  4. Look for any graph state that could be construed as a design.
  5. Press the button. Report what happens verbatim.

The expected result is informative either way: if the agent has
the composition machinery, it produces DesignedFile nodes the
button can apply; if it doesn't, the button returns 'no_design'
and the state-of-readiness is named honestly.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory","Concept","Rule","PrimitiveSpec",
              "WorldInput","DesignedFile","BuildError","CheckpointResult",
              "PluggableArchitectureDesign")
    edges = ("has_concept","has_rule","genlMt","owns_microtheory",
              "implies","derives_from","sense","sends","results_in",
              "carries","designed_via")
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({"src":{"type":t,"var":"a"},
                                       "edge_type":et,"tgt":{"type":u,"var":"b"},
                                       "where":None,
                                       "weight":{"type":"Lit","value":1.0},
                                       "provenance":"send_design"})
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
    t = str(t).replace("\n"," ").strip()
    return t[:n] + "..." if len(t) > n else t


def main():
    print("=" * 78)
    print("AGENT SENDS A DESIGN — honest test of the world + the agent's reach")
    print("=" * 78)
    print()

    s = fresh_substrate()
    install_all(s)
    from domains.text_concept_bootstrap import install_text_concept_bootstrap
    install_text_concept_bootstrap(s)

    print(f"Substrate: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, "
          f"{len(s.nodes('Rule'))} Rules")
    print()

    # ---- THE WORLD ----
    from domains.rust_runtime_world import RustRuntimeWorld
    w = RustRuntimeWorld(s, workspace_root=str(ROOT / "runners" / "dsl"))
    print(f"World up: workspace at runners/dsl")
    print()

    # ---- 1. INPUT ----
    print("=" * 78)
    print("1. INPUT — task arrives in the world")
    print("=" * 78)
    print()
    task = ("Design a pluggable transduction library: tokenize text, "
            "scan for substrate-defined patterns, return positions. The "
            "library should expose primitives via TermNode variants.")
    nid = w.input(task)
    print(f"  w.input(...) → WorldInput #{nid.value}")
    print(f"  task: {task!r}")
    print()

    # ---- 2. TICK + RUN PIPELINES ----
    print("=" * 78)
    print("2. RUN THE AGENT'S PIPELINES on the design space")
    print("=" * 78)
    print()
    steps = s.tick(100_000)
    print(f"  substrate.tick() → {steps} steps")
    print()

    # synthesize_gaps on relevant postulates
    from domains.order_n_postulates import synthesize_gaps
    from domains.implication_harvester import harvest_shapes_combined
    shape_lib = harvest_shapes_combined(s)
    print(f"  catalog: {len(shape_lib)} shapes")
    targets = ["tokenization", "parser", "lexical_analysis",
                "attribute_grammar", "semantic_action"]
    total_gaps = 0
    for postulate in targets:
        try:
            gaps = synthesize_gaps(s, postulate, max_order=1, record=False,
                                    prune=True, shapes=shape_lib)
            total_gaps += len(gaps)
            if gaps:
                print(f"  synthesize_gaps('{postulate}'): {len(gaps)} derivations")
                for g in gaps[:1]:
                    print(f"    → {short(g.get('gap',''), 110)}")
            else:
                print(f"  synthesize_gaps('{postulate}'): 0 derivations")
        except Exception as e:
            print(f"  synthesize_gaps('{postulate}'): error {e}")
    print(f"  total derivations across {len(targets)} postulates: {total_gaps}")
    print()

    # introspect on relevant Mts
    from domains.introspect_primitives import introspect_primitive_specs
    text_origins = {"parsing_concepts","rule_compilation","language_foundation",
                     "scientific_writing","text_comprehension","latex"}
    specs = introspect_primitive_specs(s, origin_filter=text_origins)
    transducers = [sp for sp in specs
                   if sp.get("semantic_kind") == "transduction_kind"]
    print(f"  introspect: {len(specs)} PrimitiveSpec nodes, "
          f"{len(transducers)} transduction_kind")
    print()

    # ---- 3. LOOK FOR DESIGNS ----
    print("=" * 78)
    print("3. WHAT THE AGENT'S GRAPH NOW HOLDS as design candidates")
    print("=" * 78)
    print()
    designed_files = s.nodes("DesignedFile")
    pads = s.nodes("PluggableArchitectureDesign")
    print(f"  DesignedFile nodes: {len(designed_files)}")
    print(f"  PluggableArchitectureDesign nodes: {len(pads)}")
    print(f"  PrimitiveSpec nodes: {len(s.nodes('PrimitiveSpec'))}")
    print(f"  WorldInput nodes: {len(s.nodes('WorldInput'))}")
    print()

    # ---- 4. PRESS THE BUTTON ----
    print("=" * 78)
    print("4. PRESS THE BUTTON — checkpoint_and_restart()")
    print("=" * 78)
    print()
    result = w.checkpoint_and_restart(
        save_graph_to=str(ROOT / "world_checkpoint.json"),
        do_build=False, do_install=False,
    )
    print(f"  status: {result['status']}")
    print(f"  applied_files: {result.get('applied_files', [])}")
    print(f"  checkpoint: {result.get('checkpoint_path')}")
    print()

    # ---- 5. THE HONEST READING ----
    print("=" * 78)
    print("WHAT HAPPENED — HONEST")
    print("=" * 78)
    print()
    print(f"  The agent's pipelines produced:")
    print(f"    · {len(specs)} PrimitiveSpec nodes from vocabulary "
          f"(via introspect)")
    print(f"    · {total_gaps} synthesize_gaps derivations")
    print(f"    · {steps} tick steps")
    print()
    print(f"  The agent's graph produced as DESIGN CANDIDATES:")
    print(f"    · {len(designed_files)} DesignedFile nodes")
    print(f"    · {len(pads)} PluggableArchitectureDesign nodes")
    print()
    if len(designed_files) == 0:
        print(f"  THE GAP")
        print()
        print(f"  The agent's existing vocabulary surfaces what it WANTS")
        print(f"  ({len(transducers)} transducer specs, {len(specs)} primitive")
        print(f"  specs total). It does NOT compose DesignedFile nodes whose")
        print(f"  content is the corresponding Rust source.")
        print()
        print(f"  The composition gap: the agent has rules about parsing,")
        print(f"  semantics, grammar — none compose source-code strings")
        print(f"  from those concepts. The agent knows what it wants; it")
        print(f"  doesn't yet know how to WRITE that in its target language.")
        print()
        print(f"  Two coherent next moves:")
        print(f"    A. Add vocabulary about source-code emission: rules that")
        print(f"       map (PrimitiveSpec, semantic_kind) → DesignedFile.path")
        print(f"       + DesignedFile.content via the agent's existing string")
        print(f"       primitives (Cat, Lines, Lit).")
        print()
        print(f"    B. Recognize that source composition needs a teacher: an")
        print(f"       external LLM that translates the agent's vocabulary-")
        print(f"       level designs into source. Babble across the boundary.")
        print(f"       The world adapter routes this; the teacher fills in.")
        print()
        print(f"  My scope was the world. The agent's reach is where it is.")
        print(f"  Bridging the two is not work I should author in Python.")
    else:
        print(f"  The agent sent {len(designed_files)} DesignedFile node(s).")
        for nid in designed_files[:5]:
            a = s.node(nid)["attrs"]
            print(f"    · {a.get('path','?'):<50} ({len(a.get('content',''))} chars)")
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
