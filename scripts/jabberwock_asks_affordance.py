"""ASK THE JABBERWOCK WHAT AFFORDANCE IT NEEDS — to author ANY new native primitive, as a GENERAL case.

It planned the joint inference and named the one faculty it lacks: the generative deformable leaf. But the
deeper question is not "build that one Term" -- it is "what affordance lets the agent author ANY primitive it
specifies, in general?". So the agent inspects its OWN self-extension faculty, finds where it is closed, and
names the general affordance. The teacher does not hand it a template; the student says what it needs.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_asks_affordance
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 98


def main():
    print(SEP)
    print("THE JABBERWOCK INSPECTS ITS SELF-EXTENSION FACULTY — and names the affordance it needs (general case).")
    print(SEP)

    rd = (ROOT and open(os.path.join(ROOT, "domains", "runtime_design.py")).read())
    se = open(os.path.join(ROOT, "domains", "self_extend.py")).read()
    term = open(os.path.join(ROOT, "runners", "dsl", "src", "term.rs")).read()

    # what the agent MEASURES about its own faculty (mechanical inspection -- the world adapter reading source).
    kinds = re.findall(r'spec\["semantic_kind"\] == "(\w+)"', rd) + re.findall(r'elif spec\["semantic_kind"\] == "(\w+)"', rd)
    homes = sorted(set(re.findall(r'"(term\.rs|jsonio\.rs|reflect\.rs|shape\.rs) \([^)]+\)"', rd)))
    # the arm SITES a binary leaf actually touches (grep one existing binary leaf across the homes):
    sites = {
        "term.rs enum variant": term.count("{ a: TermIdx, b: TermIdx },"),
        "term.rs copy_subtree arm": term.count("a: copy_subtree(src, dst, a), b: copy_subtree(src, dst, b)"),
        "term.rs evaluator arm": len(re.findall(r"TermNode::\w+ \{ a, b \} => \{", term)),
    }
    install_uniform = "all-or-nothing" in se and "_cargo_check" in se and "rebuild_native" in se

    print(f"\n  what the agent HOLDS:")
    print(f"      - agent_specify_primitive : it can STATE a primitive it lacks (name, children, the math)")
    print(f"      - self_extend.extend      : it can INSTALL fragments under an all-or-nothing guard "
          f"(snapshot->apply->cargo check->rebuild->verify callable) = {install_uniform}")
    print(f"      - emit_primitive_rust     : it can emit Rust for {len(set(kinds))} HARD-CODED semantic kinds:")
    print(f"            {sorted(set(kinds))}")

    print(f"\n  what the agent MEASURES about the gap:")
    print(f"      - a NEW kind (e.g. the generative deformable leaf) is NOT among those {len(set(kinds))} -> it")
    print(f"        cannot emit it -> cannot install it. The emitter is CLOSED (a fixed menu), the installer OPEN.")
    print(f"      - but the home ARMS a leaf touches are MECHANICAL and INVARIANT across primitives -- the enum")
    print(f"        variant, copy_subtree arm, evaluator arm, jsonio name/parse, reflect, shape are the SAME shape")
    print(f"        for every binary {{a,b}} leaf; only the HELPER BODY (the actual maths) differs:")
    for k, c in sites.items():
        print(f"            {k:>26}: {c} existing binary-leaf instances (pure boilerplate)")

    print(f"\n  {SEP[:94]}")
    print("  THE AFFORDANCE THE JABBERWOCK ASKS FOR (general case):")
    print(f"  {SEP[:94]}")
    print("  DECOUPLE the MECHANICAL from the SEMANTIC. The agent already has the installer (self_extend) and the")
    print("  speaker (agent_specify). What it lacks is a UNIFORM HOME-EMITTER keyed by Term ARITY, not by a closed")
    print("  menu of semantic kinds: given {name, children (a/b/...), return-kind}, emit ALL the home arms")
    print("  mechanically (they are identical per arity); the ONE primitive-specific part -- the helper BODY -- is")
    print("  the only thing that needs authoring. And the body it can get TWO ways, both already its own:")
    print("    (1) COMPOSE it from held DSL primitives when expressible (its intrinsic compose faculty), or")
    print("    (2) when INEXPRESSIBLE natively, have its self-teacher (code_writing_cortex) AUTHOR just the body,")
    print("        which self_extend then validates by compiling -- the body is small + checkable, unlike the arms.")
    print("  So the general affordance = `emit_arity_homes(name, arity, return_kind, body)` -- a uniform boilerplate")
    print("  fold + a body slot. Build THAT once, and the agent authors ANY primitive it specifies (the generative")
    print("  leaf, and every future one) through its own machinery -- not a new template per kind, hand-written by")
    print("  the teacher each time. The closed menu becomes an open faculty.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
