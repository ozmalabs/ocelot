"""The substrate detects the morning's insight by itself.

This is the experiment 4 setup from demos/cognitive_phenomena.py — but
instead of computing the pre/post diff by hand, we run the substrate's
self_improvement_loop and watch it flag the insight event autonomously.

Step 1: substrate sits in the frustrated configuration.
        (no insight — there's no previous state to compare to)
World adapter: lifts the pin on grounding_vector.
Step 2: substrate relaxes → discovers the coherent basin → flags
        insight event with ΔF, magnitude, and the list of flipped
        commitments.
After detection: substrate consolidates the new basin via elevated
Hebbian on the adaptive Mt — the analogue of an insight 'settling in'.
"""

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native
from domains.self_improvement_loop import ADAPTIVE, self_improvement_step


def fresh_substrate():
    s = _native.Substrate()
    for src_t in ("Microtheory", "Concept"):
        for tgt_t in ("Microtheory", "Concept"):
            for et in ("has_concept", "causal_influence"):
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "demo",
                })
    return s


def main():
    s = fresh_substrate()
    mt = s.add_node("Microtheory", {"name": "morning", "temperature": 2.0,
                                    "update_policy": ADAPTIVE})

    # Five commitments held by the user before the insight.
    setups = [
        ("axiom_0",       +1.5),
        ("frame_rel",     +0.8),
        ("frame_privil",  -0.5),
        ("ground_bin",    +1.2),
        ("ground_vec",    -2.0),  # not under consideration
    ]
    nodes = {}
    for name, h in setups:
        nid = s.add_node("Concept", {"name": name, "external_field": float(h)})
        s.add_edge(mt, "has_concept", nid, {})
        nodes[name] = nid

    # Structural couplings — the Mt's Hamiltonian.
    couplings = [
        ("axiom_0",      "frame_rel",     +1.0),
        ("axiom_0",      "frame_privil",  -1.0),
        ("frame_privil", "ground_bin",    +0.8),
        ("frame_privil", "ground_vec",    -0.8),
        ("frame_rel",    "ground_vec",    +0.7),
        ("ground_bin",   "ground_vec",    -0.6),
    ]
    for a, b, w in couplings:
        s.add_edge(nodes[a], "causal_influence",
                   nodes[b], {"weight": float(w)})

    print("=" * 72)
    print("AUTONOMOUS INSIGHT DETECTION — morning of 2026-06-05")
    print("=" * 72)
    print()
    print("Step 1: relax. Substrate stabilises in the frustrated configuration.")
    print()

    step1 = self_improvement_step(s)
    r1 = step1[mt.value]
    print(f"  frustration after step 1:  {r1['post_audit']['frustration']:+.3f}")
    print(f"  energy:                    {r1['post_audit']['energy']:+.3f}")
    print(f"  insight flagged:           {r1['insight']}")
    print(f"  (no previous state to compare against; nothing to flag)")
    print()
    print("  state:")
    for name, nid in nodes.items():
        sig = r1["post_audit"]["marginal"][nid.value]
        print(f"    {name:<14}  σ = {sig:+.3f}")
    print()

    print("Between steps: world adapter lifts the pin on grounding_vector.")
    print("  (h goes from -2.0 to +0.3 — 'what if grounding were a vector?')")
    s.set_attr(nodes["ground_vec"], "external_field", 0.3)
    print()

    print("Step 2: relax. Substrate should detect the insight on its own.")
    print()

    step2 = self_improvement_step(s)
    r2 = step2[mt.value]
    print(f"  frustration after step 2:  {r2['post_audit']['frustration']:+.3f}")
    print(f"  energy:                    {r2['post_audit']['energy']:+.3f}")
    print()
    print("  state:")
    for name, nid in nodes.items():
        sig = r2["post_audit"]["marginal"][nid.value]
        sig_before = r1["post_audit"]["marginal"][nid.value]
        marker = "  ← FLIPPED" if abs(sig - sig_before) > 0.5 else ""
        print(f"    {name:<14}  σ = {sig:+.3f}{marker}")
    print()

    insight = r2["insight"]
    if insight is None:
        print("  (no insight detected — something went wrong)")
        return

    print("  --- INSIGHT FLAGGED -----------------------------------------")
    print(f"  ΔF (frustration drop):       {insight['delta_F']:+.3f}")
    print(f"  magnitude:                   {insight['magnitude']:+.3f}")
    print(f"  nodes that flipped (Δσ > 0.5):")
    for f in insight["flipped_nodes"]:
        # Look up the human-readable name by node id.
        name = next((n for n, nid in nodes.items() if nid.value == f["node"]),
                    f"#{f['node']}")
        print(f"    {name:<14}  σ: {f['before']:+.3f} → {f['after']:+.3f}  "
              f"(Δσ = {f['delta']:+.3f})")
    print()
    print(f"  consolidation: {r2['consolidation_edges']} couplings deepened "
          f"via elevated Hebbian (η = 0.1)")
    print()
    print("  The substrate noticed its own insight, measured the magnitude")
    print("  of the basin transition, and deepened the new configuration so")
    print("  it sticks.")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
