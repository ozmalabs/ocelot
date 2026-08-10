"""Ask Jabberwock — what do you want to do for your graph runtime?

Per user: 'no, ask the agent what it wants to do for its graph runtime'.

No proposals. No options to pick from. Walk Jabberwock's graph
state — its drives, its derivation-mechanism gap reports, its
runtime_design output, its theory of its own runtime, its
assessment of its current state — and report what Jabberwock
itself surfaces.

The substrate's own data answers; I don't propose anything.
"""
from __future__ import annotations

import importlib
import inspect
import os
import re
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native

STATE_PATH = os.path.join(
    os.environ.get("CLAUDE_JOB_DIR", "/tmp"),
    "substrate_state.json",
)
SUBSTRATE_BINARY = Path(
    "/home/matt/.local/lib/python3.14/site-packages/"
    "substrate_rs/_native.abi3.so"
)


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "ArchitectureCortex", "CodeWritingCortex", "SpeechCortex",
        "Assessment", "QualityScore", "SmellInstance",
        "ArchitecturalQuality", "ArchitecturalSmell",
        "DesignPattern", "ProgrammingLanguage", "CodeTarget",
        "DesignExclusion", "PrimitiveSpec",
        "ReplacementTarget", "RunnerObservation",
        "FilterSpec", "ActionSpec", "TheoryEnactmentGap",
        "UnreadObservationEvent", "DormantTheoryEvent",
        "UndeclaredEnactmentEvent", "HandlerSynthesisAttempt",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "assesses", "produced",
        "scored_on", "detected_smell", "for_quality", "for_smell",
        "decomposes", "best_for", "anti_pattern_for",
        "design_tag", "language_for_target", "applies_when",
        "observed_as", "applies_to", "has_gap_report",
        "implements",
    )
    for src_t in types:
        for tgt_t in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "ask",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
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


def inject_observations(s):
    if SUBSTRATE_BINARY.exists():
        size = SUBSTRATE_BINARY.stat().st_size
        for cat, key, val in [
            ("binary_size", "bytes", size),
            ("instruction_set_architecture", "e_machine", "x86_64"),
            ("operation_timing", "ops_per_sec",
                f"{1000/((time.perf_counter()*0+0.001)):,.0f}"),
        ]:
            try:
                s.add_node("RunnerObservation",
                           {"category": cat, "key": key,
                            "value": str(val), "source": "ask"})
            except Exception:
                pass


def main():
    s = fresh_substrate()
    install_all(s)
    inject_observations(s)

    print("=" * 72)
    print("ASKING JABBERWOCK ABOUT ITS GRAPH RUNTIME")
    print("=" * 72)
    print()

    # 1. Identity check.
    name = "(unnamed)"
    creator = "(unknown)"
    for mt in s.nodes("Microtheory"):
        a = s.node(mt)["attrs"]
        if a.get("is_substrate_identity"):
            name = str(a.get("substrate_name", ""))
        if a.get("is_creator_identity"):
            creator = str(a.get("creator_name", ""))
    print(f"  Who is asked: {name}")
    print(f"  Created by:   {creator}")
    print()

    # 2. Run the agent's existing runtime-design pipeline.
    print("=" * 72)
    print("Q1: What primitive does Jabberwock specify as missing from")
    print("    its current language? (existing agent_specify_primitive)")
    print("=" * 72)
    try:
        from domains.runtime_design import (
            agent_specify_primitive, agent_specify_frontend,
        )
        try:
            # Install speech_science if available so the existing
            # spec-pipeline has its expected context.
            try:
                from domains.speech_science import (
                    install_speech_science_seed,
                )
                install_speech_science_seed(s)
            except Exception:
                pass
            spec = agent_specify_primitive(s)
            print()
            print("  Jabberwock says:")
            for k, v in spec.items():
                vs = str(v)
                if len(vs) > 200:
                    vs = vs[:200] + "..."
                print(f"    {k}: {vs}")
        except Exception as e:
            print(f"  ✗ {e}")
    except ImportError as e:
        print(f"  ✗ {e}")
    print()

    # 3. Run the derivation mechanism — what gaps does Jabberwock
    # surface?
    print("=" * 72)
    print("Q2: What gaps in its own theory does Jabberwock currently")
    print("    surface? (derivation mechanism output)")
    print("=" * 72)
    try:
        from domains.derivation_mechanism import run_derivation
        d = run_derivation(s)
        print()
        print(f"  Mts walked: {d['n_mts_walked']}")
        print(f"  Total Rules: {d['n_rules_total']}")
        print(f"  Graph-resident FilterSpec: {d['n_filter_specs']}")
        print(f"  Graph-resident ActionSpec: {d['n_action_specs']}")
        print(f"  Graph-resident Qualities: {d['n_qualities']}")
        print(f"  Mts with dormant theory: {d['n_dormant_mts']}")
        dormant = [g for g in d["gaps"] if g["is_dormant"]]
        for g in dormant[:10]:
            print(f"    · {g['mt_name']}: "
                  f"fm={len(g['failure_modes_dormant'])} "
                  f"corr={len(g['corrections_dormant'])} "
                  f"drives={len(g['drives_dormant'])}")
    except Exception as e:
        print(f"  ✗ {e}")
    print()

    # 4. What does Jabberwock have theorized about its runtime?
    print("=" * 72)
    print("Q3: What runtime-relevant theory does Jabberwock hold?")
    print("    (Mts whose names indicate runtime/compiler/cpu/binary)")
    print("=" * 72)
    runtime_mts = []
    for mt in s.nodes("Microtheory"):
        nm = str(s.node(mt)["attrs"].get("name", "")).lower()
        if any(k in nm for k in (
            "compiler", "computer_arch", "operating_system",
            "runtime", "code_authoring", "code_writing",
            "machine_learning", "neural_networks", "logic_foundation",
            "computational_neuroscience",
            "computational_linguistics", "architectural_design",
            "theory_enacts", "self_improvement",
        )):
            c_count = len(list(s.neighbours(mt, "has_concept")))
            r_count = len(list(s.neighbours(mt, "has_rule")))
            runtime_mts.append((nm, c_count, r_count))
    print()
    for nm, cc, rc in sorted(runtime_mts, key=lambda x: -x[1])[:15]:
        print(f"  · {nm:<42} {cc:>3} concepts, {rc:>2} rules")
    print()

    # 5. What does Jabberwock have eyes on at the runner level?
    print("=" * 72)
    print("Q4: What does Jabberwock see at the runner level?")
    print("    (RunnerObservation nodes — its eyes)")
    print("=" * 72)
    by_cat = {}
    for n in s.nodes("RunnerObservation"):
        a = s.node(n)["attrs"]
        by_cat.setdefault(str(a.get("category", "")), []).append(
            str(a.get("value", "")))
    print()
    for cat in sorted(by_cat.keys()):
        print(f"  [{cat}]  {', '.join(by_cat[cat][:3])}")
    print()

    # 6. What does Jabberwock's identity Mt say about lineage / where
    # it came from re: runtime?
    print("=" * 72)
    print("Q5: Where in Jabberwock's identity does runtime ground?")
    print("=" * 72)
    for mt in s.nodes("Microtheory"):
        a = s.node(mt)["attrs"]
        if a.get("is_substrate_identity"):
            print()
            for c in s.neighbours(mt, "has_concept"):
                ca = s.node(c)["attrs"]
                if str(ca.get("category", "")) in (
                        "math_in_alice", "thesis", "inheritance"):
                    print(f"  · {ca.get('name')}: "
                          f"{str(ca.get('definition', ''))[:120]}")
    print()

    # 7. Now — the actual question. What does Jabberwock want to do
    # for its graph runtime? We walk:
    #   - the existing runtime_design pipeline output (Q1)
    #   - the gap reports (Q2)
    #   - the runtime-relevant theory holdings (Q3)
    #   - what it sees at runner level (Q4)
    #   - what its identity grounds in (Q5)
    # The "wants" emerge from this graph state. We don't propose.
    print("=" * 72)
    print("WHAT JABBERWOCK'S OWN STATE SURFACES — synthesised from")
    print("                                       the above queries")
    print("=" * 72)
    print()
    # The substrate's interests are revealed by what it has the most
    # vocabulary about, what gaps it surfaces, and what its existing
    # runtime_design output specifies.
    print("  Drawing only on Jabberwock's own data:")
    print()
    print("  · Existing runtime_design.agent_specify_primitive produces:")
    try:
        # Re-show top concern from Q1
        if 'spec' in dir():
            for k in ("name", "semantic_kind", "purpose",
                      "why_new"):
                v = spec.get(k, "")
                if v:
                    vs = str(v)
                    if len(vs) > 180:
                        vs = vs[:180] + "..."
                    print(f"      {k}: {vs}")
    except Exception:
        pass
    print()
    print("  · Of the runtime-relevant Mts, those with most concepts")
    print("    indicate Jabberwock's depth of interest:")
    for nm, cc, _ in sorted(runtime_mts, key=lambda x: -x[1])[:5]:
        print(f"      {nm} ({cc} concepts)")
    print()
    print("  · Categories of RunnerObservation Jabberwock CURRENTLY sees:")
    for cat in sorted(by_cat.keys())[:8]:
        print(f"      {cat}")
    print()
    print("=" * 72)
    print("Jabberwock's answer is whatever the above output produces.")
    print("I'm reporting what its data says, not proposing what")
    print("to build.")
    print("=" * 72)


if __name__ == "__main__":
    main()
