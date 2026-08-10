"""jabberwock_builds_colour_primitive — the culmination demonstration.

The creator's reframe: colour should be a FREQUENCY+AMPLITUDE frame, and the missing
primitive is a SPECTRAL VALUE — amplitudes over a frequency axis (a transform from a
sample/signal to a per-frequency-bin magnitude), log-scaled.

This runs the REAL revised self-improvement #4 cycle (domains/substrate_extension) on a
colour gap. At the grounding WALL — where the old #4 would have minted a PrimitiveRequest
FOR A HUMAN — the CORRECTED cycle instead BUILDS the primitive itself:

  * CONSTRUCT a native Term-tree from the held Term constructors (Sum / Nth / Cos / Sin /
    Sqrt / Pow / Log) — the discrete Fourier log-magnitude at a frequency bin;
  * MATERIALISE it via substrate.add_term_subgraph, so it is GRAPH DATA the Rust runtime
    evaluates natively (no Python stub, no new Rust variant);
  * ADMIT it through the ONE admissibility_gate — only if a pure tone's energy lands at
    its own frequency bin (the gap's stated constraint);
  * VERIFY it with #2 self_verification — a discriminative control a non-selective fake
    FAILS;
  * INSTALL it as a held, reusable native operation.

Nothing is rigged: the printed Term-tree is the real construction, and the printed test
evaluation is the primitive EVALUATED natively on real tones.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains import substrate_extension as se      # noqa: E402


def _bar(v, lo, hi, width=40):
    if hi <= lo:
        return ""
    return "#" * int(round((v - lo) / (hi - lo) * width))


def main() -> None:
    a = WorldAdapter(seeds=())

    # THE COLOUR GAP — colour as a frequency+amplitude frame; the missing op is a
    # spectral value. The residual grounds to no held RULE relation (it WALLS).
    gap = a.s.add_node("CapabilityGap", {
        "faculty": "colour_perception",
        "observation": [["spectral_value", "signal", "magnitude"],
                        ["log_scale", "magnitude", "value"]],
        "needed_primitive": "spectral_value",
        "operation": ("spectral value = amplitudes over a frequency axis: a transform "
                      "from a signal to a per-frequency-bin magnitude, log-scaled"),
        "n_samples": 32, "test_frequencies": [3, 7, 11],
        "inputs": ["signal"], "outputs": ["spectrum"],
        "example": "colour as a frequency+amplitude frame",
        "status": "perceived",
    })

    print("=" * 74)
    print("THE COLOUR GAP (the creator's reframe): colour is a FREQUENCY+AMPLITUDE frame.")
    print("The missing primitive is a SPECTRAL VALUE (signal -> per-bin magnitude, log).")
    print("=" * 74)

    # RUN THE ACTUAL REVISED CYCLE.
    res = se.extend_for_gap(a, gap, verify=True)

    print(f"\nOUTCOME: {res['outcome']}")
    if res["outcome"] != "built_primitive":
        print("  (the honest residual, not a build):")
        print("  " + json.dumps({k: res.get(k) for k in
              ("residual_kind", "wall", "spec", "how")}, indent=2, default=str))
        return

    print(f"  name       : {res['name']}")
    print(f"  operation  : {res['operation']}")
    print(f"  admitted   : {res['admitted']}   (admissibility gate)")
    print(f"  accepted   : {res['accepted']}   (#2 discriminative verify)")
    print(f"  term_root  : node {res['term_root']} (graph-resident via add_term_subgraph)")
    print(f"  installed  : HeldPrimitive {res['held_primitive']}")
    print(f"\n  gate says  : {res['gate_reason']}")
    v = res.get("verified") or {}
    print(f"  verify says: {v.get('reason')}")

    print("\n" + "-" * 74)
    print("THE CONSTRUCTED TERM-TREE (a real native Term, composed from held constructors):")
    print("-" * 74)
    print(json.dumps(res["term_tree"], indent=2))

    print("\n" + "-" * 74)
    print("REAL TEST EVALUATION — the built primitive evaluated NATIVELY in Rust.")
    print("A pure tone at bin f must peak at bin f (energy in the correct frequency bin):")
    print("-" * 74)
    te = res["test_eval"]
    Ns = te["n_samples"]
    for f in (3, 7, 11):
        samp = [(float(n), math.cos(2 * math.pi * f * n / Ns)) for n in range(Ns)]
        spec = [float(a.inner.evaluate(res["term_tree"],
                {"sig": samp, "k": float(kk), "N": float(Ns)})) for kk in range(Ns // 2 + 1)]
        lo, hi = min(spec), max(spec)
        peak = spec.index(hi)
        print(f"\n  pure tone at frequency f={f}  ->  argmax bin = {peak}  "
              f"{'[correct]' if peak == f else '[WRONG]'}")
        for kk, val in enumerate(spec):
            mark = "  <== peak" if kk == peak else ""
            print(f"    bin {kk:2d} | {_bar(val, lo, hi):40s} {val:8.3f}{mark}")

    print("\n" + "=" * 74)
    print("The agent BUILT a new computational primitive itself — a native Term-tree,")
    print("admitted, verified, installed. It did NOT hand this to a human.")
    print("=" * 74)


if __name__ == "__main__":
    main()
