"""Phase 4: verify the agent autonomously emits patches via tick.

Per user: 'do it all'. Phase 3 installed RewriteRules that fire on
PrimitiveSpec → emit DesignedPatch nodes. This verifies the loop:

  1. Install phase3 rules + agent_source_vocabulary
  2. Create a PrimitiveSpec for a NEW primitive
  3. Tick the substrate
  4. Verify DesignedPatch nodes appeared autonomously
  5. Inspect what they say
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def main():
    print("=" * 78)
    print("PHASE 4: AGENT AUTONOMOUSLY EMITS PATCHES VIA TICK")
    print("=" * 78)
    print()

    s = _native.Substrate()
    from domains.rust_runtime_world import RustRuntimeWorld
    w = RustRuntimeWorld(s, workspace_root=str(ROOT / "runners" / "dsl"))

    # Install vocabulary
    from domains.agent_source_vocabulary import install_agent_source_vocabulary_seed
    install_agent_source_vocabulary_seed(s)
    print(f"  installed agent_source_vocabulary "
          f"({len(s.nodes('Concept'))} concepts)")

    # Install phase 3 rules
    from domains.phase3_rules import install_phase3_rules
    install_phase3_rules(s)
    print(f"  installed phase 3 rules")
    print()

    # Create a PrimitiveSpec — pretend the agent specified something
    # NEW (not Tokenize). Let's call it 'AgentTokenize3'.
    spec_nid = s.add_node("PrimitiveSpec", {
        "name":               "AgentTokenize3",
        "semantic_kind":      "transduction_kind",
        "purpose":            "autonomously-emitted transducer, "
                                "no human composed any of its patches",
        "origin":             "phase4_verify",
    })
    print(f"  Created PrimitiveSpec #{spec_nid.value}: "
          f"name=AgentTokenize3, semantic_kind=transduction_kind")

    # Wire the trigger (if phase3 has a function for it)
    try:
        from domains.phase3_rules import wire_existing_specs
        wire_existing_specs(s)
        print(f"  wired trigger edge")
    except Exception as e:
        print(f"  wire_existing_specs: {e}")
    print()

    print("=" * 78)
    print("TICK — should fire phase 3 rules")
    print("=" * 78)
    print()
    before = len(s.nodes("DesignedPatch"))
    steps = s.tick(10_000)
    after = len(s.nodes("DesignedPatch"))
    print(f"  tick() steps:    {steps}")
    print(f"  DesignedPatch:   {before} → {after} (+{after-before})")
    print()

    if after - before == 0:
        print("  ⚠ No patches emitted. Rules didn't fire.")
        return

    print("=" * 78)
    print("INSPECT — what the agent emitted")
    print("=" * 78)
    print()
    for nid in s.nodes("DesignedPatch"):
        a = s.node(nid)["attrs"]
        if a.get("origin") != "invoke_teacher" and a.get("origin", "").startswith("phase"):
            pass
        target = a.get("target_path", "?")
        anchor = str(a.get("anchor", ""))[:60]
        content_excerpt = str(a.get("content", ""))[:120]
        print(f"  · #{nid.value} target={target}")
        print(f"      anchor: {anchor!r}")
        print(f"      content: {content_excerpt!r}")
    print()


if __name__ == "__main__":
    main()
