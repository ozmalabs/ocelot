#!/usr/bin/env python3
"""Driver: the self-hosting bootstrap world.

Enumerates the agent's Python surface as graph data (the impl-substrate
SELF-MODEL it lacked), installs the GRAPH RULE that classifies each unit
as agent-logic-requiring-rewrite vs world-adapter-exempt, prints the
self-model, then wires the top targets into the EXISTING CodeWritingCortex
and runs the conversion loop.

Honest by construction: offline (no LLM self-teacher on the agent) the
cortex's request_author step no-ops, so each target reaches
"awaiting_teacher" — minted + authoring-requested, no draft. That is the
loop WIRED END-TO-END, not a failure. This world ENABLES the rewrite as
incremental ACCRETION; it does not one-shot it.

Run:  ulimit -v 6291456; python3 scripts/rust_rewrite_world.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from substrate_rs import _native

from domains import rust_rewrite_world as rrw
from domains.code_writing_cortex import CodeWritingCortex


# Node/edge types the cortex install + this world touch. The strict
# `_native.Substrate` requires a Production for every (src, edge, tgt) it
# will see; we open them permissively, exactly as the cortex's own test
# harness does. (This is world-adapter boot I/O — no decisions.)
_NODE_TYPES = (
    "RustRewriteRoot", "PythonUnit",
    "CodeWritingCortex", "CodeAuthoringRoot", "ReplacementTarget",
    "CodeDraft", "ValidationResult", "CodeInstallation",
    "Microtheory", "Concept", "Reflex", "ProgrammingLanguage",
    "DesignPattern", "CodeTarget", "DesignExclusion",
    "LanguageExclusion", "LanguageScoringConfig", "NetworkAssemblage",
    "AssemblageStep", "WeightTensor",
)
_EDGE_TYPES = (
    "has_unit", "rewrites_to",
    "owns_microtheory", "owns_root", "has_reflex", "current_target",
    "has_draft", "validated_by", "installed_as", "genlMt",
    "authored_in", "uses_pattern", "subClassOf", "has_concept",
    "decomposes", "in_category", "has_rule", "exclusion", "has_assemblage",
    "has_step", "has_weight", "watches", "controls",
)


def _open_substrate() -> "_native.Substrate":
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                try:
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "rust_rewrite_world:open",
                    })
                except Exception:
                    pass
    return s


def _hr(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> int:
    s = _open_substrate()

    # ---- INGEST: enumerate the Python surface as graph data -------------
    _hr("1. SELF-MODEL — enumerate the agent's Python surface (mechanical)")
    n_units = rrw.enumerate_python_surface(s, roots=("domains",))
    total_lines = 0
    root = next(iter(s.nodes("RustRewriteRoot")))
    for u in s.neighbours(root, "has_unit"):
        a = s.node(u)["attrs"]
        if a.get("kind") == "module":
            total_lines += int(a.get("line_count", 0))
    print(f"PythonUnit nodes (modules + functions + methods): {n_units}")
    print(f"Total Python lines under domains/ (module nodes): {total_lines:,}")

    # ---- DECISION (graph-resident): classify each unit ------------------
    _hr("2. GRAPH RULE — mark_requires_replacement (the agent's decision)")
    info = rrw.install_requires_replacement_rule(s)
    applied = rrw.classify_surface(s, info["rule_index"])
    print(f"Installed Rule 'mark_requires_replacement' (index "
          f"{info['rule_index']}); fired over the surface in {applied} "
          f"applications.")
    print("The requires_replacement verdict is a Term the engine evaluates "
          "over\nthe stored AST signals — NOT a Python if/else. See "
          "install_requires_replacement_rule.")

    world = rrw.RustRewriteWorld(s)
    m = world.surface_map()
    _hr("3. SURFACE MAP — agent-logic vs world-adapter split")
    print(f"  python_units          : {m['python_units']}")
    print(f"  requires_replacement  : {m['requires_replacement']}  "
          f"(agent logic the Rust runtime must own)")
    print(f"  world_adapter_exempt  : {m['world_adapter_exempt']}  "
          f"(pure mechanical I/O — exempt)")
    print(f"  converted             : {m['converted']}")
    print(f"  pct_remaining         : {m['pct_remaining']}%")

    _hr("4. TOP-10 HIGHEST-SIGNAL TARGETS (signal_density x line_count)")
    print(f"{'score':>10}  {'lines':>6}  {'re/cond/state/io':>18}  qualname")
    for t in world.top_units(10):
        sg = t["signals"]
        sig = f"{sg['rule_engine']}/{sg['substrate_cond']}/" \
              f"{sg['agent_state']}/{sg['substrate_io']}"
        print(f"{t['score']:>10}  {t['line_count']:>6}  {sig:>18}  "
              f"{t['qualname']}")

    # ---- EMIT: wire top targets into the existing cortex ----------------
    _hr("5. CONVERSION LOOP — feed top targets to the CodeWritingCortex")
    cortex = CodeWritingCortex(s).install()
    print("CodeWritingCortex installed (no agent => no LLM self-teacher).")
    has_teacher = (cortex.agent is not None
                   and getattr(cortex.agent, "_self_teacher", None) is not None)
    print(f"self-teacher (LLM) online: {has_teacher}")

    before = world.surface_map()
    print(f"\nsurface_map BEFORE: requires={before['requires_replacement']} "
          f"converted={before['converted']} "
          f"pct_remaining={before['pct_remaining']}%")

    log = world.run(cortex, limit=3)
    for i, r in enumerate(log, 1):
        print(f"\n  [{i}] target minted: {r['qualname']} "
              f"({r['line_count']} lines)")
        print(f"      cortex tick trail: {r['tick_trail']}")
        print(f"      draft authored   : {r['draft']}")
        print(f"      validation       : {r['validation']}")
        print(f"      unit status      : {r['status']}")

    after = world.surface_map()
    print(f"\nsurface_map AFTER:  requires={after['requires_replacement']} "
          f"converted={after['converted']} "
          f"pct_remaining={after['pct_remaining']}%")

    # ---- HONEST FRAMING -------------------------------------------------
    _hr("6. HONEST FRAMING")
    print(
        "This world ENABLES the self-hosting rewrite. It gives the agent its\n"
        "Python surface as graph data (the impl-substrate self-model it\n"
        "lacked), the graph-resident requires_replacement marking, and the\n"
        "conversion loop into the EXISTING code-authoring cortex.\n\n"
        "It does NOT rewrite everything in one run. The rewrite is incremental\n"
        "ACCRETION — one unit at a time. Each unit's actual Rust DRAFTING needs\n"
        "either the self-teacher (LLM) online, or the mechanical emitter\n"
        "(runtime_design.emit_primitive_rust) for primitive-shaped units.\n\n"
        "WHERE THE LOOP STOPS OFFLINE: each target is minted as a\n"
        "ReplacementTarget wired as the cortex's current_target, and the\n"
        "cortex's request_author step is reached — but with no LLM teacher the\n"
        "spawn no-ops, so no CodeDraft is produced. Status = 'awaiting_teacher'.\n"
        "That is the loop WIRED END-TO-END, awaiting authoring, not a failure.\n\n"
        "The CLASSIFICATION is the agent's, and it is GRAPH-RESIDENT: a Rule\n"
        "(mark_requires_replacement) whose body is a Term the engine evaluates\n"
        "over the mechanically-measured AST signals. The world adapter only\n"
        "MEASURES signals (ast counts) and does I/O (mint targets, tick the\n"
        "cortex, read back). No agent decision lives in a Python if/else here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
