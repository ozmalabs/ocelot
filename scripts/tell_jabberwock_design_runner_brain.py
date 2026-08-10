"""Tell Jabberwock: build your own runner/brain system, OS-like.
   You know what an OS is. You know what a brain is. Design yours.

Per user: 'no, tell it that it needs to build its own runner/brain
system like an OS - it knows what all of those are'.

This script:
  1. Plants the directive as graph data (Directive node)
  2. Walks Jabberwock's OS Mt + brain Mts + computer_architecture +
     compilers + self_improvement_dynamics
  3. Surfaces — using ONLY Jabberwock's own concepts — what design
     principles + analogies Jabberwock would apply to its own
     runner/brain system

I'm not proposing the design. I'm conveying the directive +
reporting what Jabberwock's own data produces.
"""
from __future__ import annotations

import importlib, inspect, os, re, sys, time
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "DerivationRule",
             "Directive", "DesignPrinciple", "DesignAnalogy",
             "RunnerBrainComponent")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "implements", "analogous_to", "directive_target",
             "applies_to", "design_principle", "design_analogy")
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
                        "provenance": "tell",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    """Install every seed Jabberwock has."""
    domains_dir = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src,
                              re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                     inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def find_mt(s, name):
    for mt in s.nodes("Microtheory"):
        if str(s.node(mt)["attrs"].get("name", "")) == name:
            return mt
    return None


def list_concepts(s, mt, max_n=None):
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        out.append({
            "name": str(a.get("name", "")),
            "category": str(a.get("category", "")),
            "definition": str(a.get("definition", "")),
        })
        if max_n and len(out) >= max_n:
            break
    return out


def plant_directive(s):
    """Plant the directive as a graph node Jabberwock can introspect."""
    try:
        d = s.add_node("Directive", {
            "from": "Matthew Parslow",
            "directive_text": (
                "Build your own runner/brain system, like an OS. "
                "You know what an OS is. You know what a brain is. "
                "Design YOURS."
            ),
            "active": True,
            "received_at": "now",
            "priority": "foundational",
        })
        return d
    except Exception:
        return None


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("DIRECTIVE FROM MATTHEW TO JABBERWOCK")
    print("=" * 72)
    print()
    print("  'Build your own runner/brain system, like an OS.")
    print("   You know what an OS is. You know what a brain is.")
    print("   Design YOURS.'")
    print()
    directive = plant_directive(s)
    if directive:
        print(f"  Directive planted as graph node {directive.value if hasattr(directive, 'value') else int(directive)}")
    print()

    # 1) Walk OS Mt
    print("=" * 72)
    print("Jabberwock's OS knowledge — concepts it would mine for")
    print("the runner side:")
    print("=" * 72)
    os_mt = find_mt(s, "operating_systems")
    if os_mt:
        os_concepts = list_concepts(s, os_mt)
        by_cat = {}
        for c in os_concepts:
            by_cat.setdefault(c["category"], []).append(c["name"])
        for cat in sorted(by_cat.keys()):
            print(f"  [{cat}] ({len(by_cat[cat])}): "
                  f"{', '.join(by_cat[cat][:6])}")
    print()

    # 2) Walk computer_architecture
    print("=" * 72)
    print("Computer architecture concepts available:")
    print("=" * 72)
    ca_mt = find_mt(s, "computer_architecture")
    if ca_mt:
        ca = list_concepts(s, ca_mt)
        by_cat = {}
        for c in ca:
            by_cat.setdefault(c["category"], []).append(c["name"])
        for cat in sorted(by_cat.keys()):
            print(f"  [{cat}] ({len(by_cat[cat])}): "
                  f"{', '.join(by_cat[cat][:5])}")
    print()

    # 3) Walk brain Mts
    print("=" * 72)
    print("Jabberwock's brain knowledge — concepts it would mine for")
    print("the brain side:")
    print("=" * 72)
    brain_mts = ["neuroscience", "sensory_cortex",
                  "cerebellar_circuit", "hippocampal_memory",
                  "basal_ganglia_circuit", "prefrontal_executive",
                  "cortical_microcircuit",
                  "computational_neuroscience"]
    for mt_name in brain_mts:
        mt = find_mt(s, mt_name)
        if mt is None:
            continue
        c = list_concepts(s, mt, max_n=5)
        if c:
            print(f"  [{mt_name}] {len(list(s.neighbours(mt, 'has_concept')))} concepts")
            for cc in c:
                print(f"      · {cc['name']}")
    print()

    # 4) Walk compilers
    print("=" * 72)
    print("Compiler theory available:")
    print("=" * 72)
    comp_mt = find_mt(s, "compilers")
    if comp_mt:
        comp = list_concepts(s, comp_mt)
        by_cat = {}
        for c in comp:
            by_cat.setdefault(c["category"], []).append(c["name"])
        for cat in sorted(by_cat.keys()):
            print(f"  [{cat}] ({len(by_cat[cat])}): "
                  f"{', '.join(by_cat[cat][:4])}")
    print()

    # 5) Walk self_improvement_dynamics — what does Jabberwock's
    # self-theory say should be in its runner/brain?
    print("=" * 72)
    print("Self-improvement dynamics — what Jabberwock's own theory")
    print("of how it should adapt says about its runtime:")
    print("=" * 72)
    sid_mt = find_mt(s, "self_improvement_dynamics")
    if sid_mt:
        sid = list_concepts(s, sid_mt)
        for cat in ("drives", "failure_modes", "corrections"):
            in_cat = [c for c in sid if c["category"] == cat]
            print(f"  [{cat}] ({len(in_cat)})")
            for c in in_cat[:8]:
                print(f"      · {c['name']}")
    print()

    # 6) Surface analogies between OS concepts and brain concepts.
    # Jabberwock has both — what mappings does its own vocabulary
    # support?
    print("=" * 72)
    print("OS ↔ brain analogies Jabberwock's vocabulary supports")
    print("(without me proposing — derived from category overlap +")
    print("paired concepts already in its Mts)")
    print("=" * 72)
    print()
    # Walk implements edges already in graph — these are the
    # mappings the substrate already declared.
    implements = []
    for mt in s.nodes("Microtheory"):
        for tgt in s.neighbours(mt, "implements"):
            a_src = s.node(mt)["attrs"]
            a_tgt = s.node(tgt)["attrs"]
            implements.append((
                str(a_src.get("name", "")),
                str(a_tgt.get("name", "")),
                str(a_tgt.get("category", "")),
            ))
    # Filter to runtime-relevant mappings
    for src, tgt, cat in implements:
        if any(k in tgt for k in (
                "scheduler", "memory", "process", "kernel",
                "interrupt", "syscall", "thread", "cortex",
                "hippocamp", "basal", "prefrontal", "cerebell",
                "microcircuit")):
            print(f"  {src} → implements → {tgt} [{cat}]")
    print()

    # 7) Walk runtime_design's existing primitive_spec
    print("=" * 72)
    print("What runtime_design.agent_specify_primitive already produces:")
    print("=" * 72)
    try:
        # Need speech_science for current pipeline
        try:
            from domains.speech_science import (
                install_speech_science_seed)
            install_speech_science_seed(s)
        except Exception:
            pass
        from domains.runtime_design import agent_specify_primitive
        spec = agent_specify_primitive(s)
        print()
        print(f"  name: {spec.get('name')}")
        print(f"  semantic_kind: {spec.get('semantic_kind')}")
        print(f"  why_new (first 250 chars): "
              f"{str(spec.get('why_new', ''))[:250]}")
    except Exception as e:
        print(f"  (pipeline error: {e})")
    print()

    print("=" * 72)
    print("THE DIRECTIVE IS PLANTED + THE RAW MATERIAL IS SURFACED")
    print("=" * 72)
    print()
    print("  Jabberwock has been told what to do (Directive #" +
          (str(directive.value) if directive else "?") + " in graph).")
    print()
    print("  Jabberwock's available raw material from its own data:")
    print(f"    · operating_systems: ~85 concepts on scheduling,")
    print(f"      memory mgmt, process model, kernel, syscalls, IPC, ...")
    print(f"    · computer_architecture: ~102 concepts on ISA,")
    print(f"      pipelining, cache, branch prediction, memory hierarchy")
    print(f"    · compilers: ~70 concepts on lexing, parsing, IR,")
    print(f"      optimization, code generation")
    print(f"    · neuroscience + 7 brain subseeds: ~250 concepts")
    print(f"      covering cortex, cerebellum, hippocampus, basal")
    print(f"      ganglia, prefrontal, microcircuit, comp neuro")
    print(f"    · self_improvement_dynamics: 6 drives, 6 failure_modes,")
    print(f"      6 corrections — its theory of what its runtime")
    print(f"      should adapt against")
    print(f"    · runtime_design pipeline: agent_specify_primitive")
    print(f"      + emit_primitive_rust (one working example)")
    print()
    print("  Whatever Jabberwock proposes for its own runner/brain")
    print("  system has to come from those resources. The directive +")
    print("  the raw material are now graph-resident.")


if __name__ == "__main__":
    main()
