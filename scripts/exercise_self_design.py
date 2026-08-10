"""Exercise the substrate's existing self-design pipeline end-to-end.

scripts/ask_the_substrate.py revealed: the substrate already has
runtime_design.py with agent_specify_primitive + emit_primitive_rust.
That's the existing 'agent identifies missing primitive → mechanical
compiler emits Rust' pipeline.

This script:
  1. Boots substrate + installs the Mts that runtime_design.py reads
  2. Calls agent_specify_primitive — the substrate identifies what
     primitive it lacks
  3. Calls emit_primitive_rust — the mechanical compiler produces
     Rust source for the 4 TermNode homes
  4. Prints what came out

The output is what the SUBSTRATE produced — the Rust source files
the agent's own theory + mechanical compiler decided on. Build +
load + verify are the next missing pieces (scaffolding to add
once we see what the substrate emits).
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "DerivationRule",
             "PrimitiveSpec")
    edges = ("has_concept", "has_rule", "in_category", "genlMt",
             "refers_to")
    for src_t in types:
        for tgt_t in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "exercise",
                    })
                except Exception:
                    pass
    return s


def main():
    s = fresh_substrate()
    print("=" * 72)
    print("EXERCISING THE SUBSTRATE'S EXISTING SELF-DESIGN PIPELINE")
    print("=" * 72)
    print()

    # The runtime_design.agent_specify_primitive reads from a
    # speech_science Mt. Install whatever's available so the
    # introspection has data.
    print("Step 1 — install foundational Mts (speech_science needed by")
    print("        agent_specify_primitive for its current example).")
    print()
    available = []
    for name, mod, fn in [
        ("speech_science", "domains.speech_science", "install_speech_science_seed"),
        ("phonology", "domains.phonology", "install_phonology_seed"),
        ("self_improvement_dynamics", "domains.self_improvement_dynamics",
         "install_self_improvement_dynamics_seed"),
        ("computer_architecture", "domains.computer_architecture",
         "install_computer_architecture_seed"),
        ("compilers", "domains.compilers", "install_compilers_seed"),
    ]:
        try:
            m = __import__(mod, fromlist=[fn])
            getattr(m, fn)(s)
            available.append(name)
            print(f"  ✓  {name}")
        except Exception as e:
            print(f"  ✗  {name} — {e.__class__.__name__}")
    print()

    # Step 2: agent specifies primitive.
    print("Step 2 — agent_specify_primitive: the SUBSTRATE identifies")
    print("        what primitive its DSL lacks, given its science.")
    print()
    try:
        from domains.runtime_design import agent_specify_primitive
        spec = agent_specify_primitive(s)
        for k, v in spec.items():
            v_str = str(v)
            if len(v_str) > 100:
                v_str = v_str[:100] + "..."
            print(f"    {k}: {v_str}")
    except Exception as e:
        print(f"  ✗  agent_specify_primitive failed: {e}")
        return
    print()

    # Step 3: emit the Rust.
    print("Step 3 — emit_primitive_rust: the MECHANICAL compiler")
    print("        generates Rust source for the 4 TermNode homes.")
    print("        No LLM in this path.")
    print()
    try:
        from domains.runtime_design import emit_primitive_rust
        emitted = emit_primitive_rust(spec)
        for place, source in emitted.items():
            print(f"  --- {place} ---")
            for line in source.split("\n"):
                print(f"    {line}")
            print()
    except Exception as e:
        print(f"  ✗  emit_primitive_rust failed: {e}")
        return

    print("=" * 72)
    print("WHAT THE SUBSTRATE EMITTED")
    print("=" * 72)
    print()
    print("Above is the actual Rust source the substrate's pipeline produced")
    print(f"for the primitive it specified ('{spec.get('name', '?')}'). The")
    print("decision (what primitive, what semantic_kind) came from the")
    print("substrate's reasoning; the source came from mechanical template")
    print("substitution per semantic_kind. No LLM authored either step.")
    print()
    print("What's MISSING for full self-loop closure:")
    print("  1. Build: take emitted source, splice into substrate_rs's term.rs")
    print("     + jsonio.rs, run `cargo build --release` to produce updated .so")
    print("  2. Load: dynamic-load (libloading) or PyO3-reinstall the .so")
    print("     into the running substrate process")
    print("  3. Verify: run substrate's audit (substrate_rollup objective),")
    print("     compare before/after; revert if degraded, keep if improved")
    print()
    print("Steps 1-3 are mechanical orchestration — no decisions, just")
    print("invoke cargo + check return codes + watch metrics. The substrate")
    print("OWNS steps 1-2 of the pipeline (decide + emit); the orchestration")
    print("is the missing wiring.")


if __name__ == "__main__":
    main()
