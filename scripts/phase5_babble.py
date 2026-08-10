"""Phase 5: babble loop honest run.

The agent emits 10 patches via tick (phases 3+4 verified). The
patches have template bugs — some contents still reference Tokenize
instead of the new variant name. Cargo build fails. The babble loop
detects deadlock because the agent has no rules to refine its rules
based on BuildError feedback.

This script runs the loop end-to-end and reports honestly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def main():
    print("=" * 78)
    print("PHASE 5: BABBLE LOOP — does the agent refine its own rules?")
    print("=" * 78)
    print()

    s = _native.Substrate()
    from domains.rust_runtime_world import RustRuntimeWorld
    w = RustRuntimeWorld(s, workspace_root=str(ROOT / "runners" / "dsl"))
    from domains.agent_source_vocabulary import install_agent_source_vocabulary_seed
    from domains.phase3_rules import install_phase3_rules, wire_existing_specs

    install_agent_source_vocabulary_seed(s)
    install_phase3_rules(s)

    s.add_node("PrimitiveSpec", {
        "name": "AgentTokenize4",
        "semantic_kind": "transduction_kind",
        "origin": "phase5",
    })
    wire_existing_specs(s)
    s.tick(10_000)

    # Fix paths (rules emit with workspace prefix; world expects relative)
    for nid in s.nodes("DesignedPatch"):
        a = s.node(nid)["attrs"]
        tp = str(a.get("target_path", ""))
        if tp.startswith("runners/dsl/"):
            s.set_attr(nid, "target_path", tp[len("runners/dsl/"):])

    print(f"Initial DesignedPatch count: {len(s.nodes('DesignedPatch'))}")
    print(f"Each patch attempts to introduce AgentTokenize4 into a different home.")
    print()

    result = w.babble_loop(
        max_iters=3, tick_steps=10_000, do_install=False,
        save_path="/tmp/cp.json",
    )
    print(f"Status: {result['status']}, iters: {result['iters']}")
    for i, st, nf, ne in result["history"]:
        print(f"  iter {i}: status={st:<25} files={nf} errors={ne}")
    print()

    errors = s.nodes("BuildError")
    print(f"BuildError nodes: {len(errors)}")
    by_kind = {}
    for nid in errors:
        a = s.node(nid)["attrs"]
        k = a.get("kind", "?")
        by_kind[k] = by_kind.get(k, 0) + 1
    for k, n in by_kind.items():
        print(f"  · {k}: {n}")
    print()

    print("=" * 78)
    print("HONEST FINDING")
    print("=" * 78)
    print()
    print("  The agent's rules from phase 3 emit patches via tick (verified).")
    print("  The patches' content templates are incomplete: some bodies still")
    print("  reference 'Tokenize' where they should reference the new variant.")
    print("  Build fails on apply.")
    print()
    print("  The babble loop deadlock-detected: tick produces the same patches")
    print("  each iteration because the agent has no rules over BuildError")
    print("  that refine its own composition rules.")
    print()
    print("  The closing-of-the-loop requires:")
    print("    · phase 3 rules to be more complete (full name substitution)")
    print("    · OR: rules-over-rules — meta-rules that fire on BuildError")
    print("      and emit updates to phase 3 rules' attrs (template fixes)")
    print()
    print("  Both are achievable by the teacher; both are the next stretch.")
    print("  For this run: loop infrastructure works; refinement is the gap.")


if __name__ == "__main__":
    main()
