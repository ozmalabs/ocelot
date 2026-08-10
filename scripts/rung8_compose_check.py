"""rung8_compose_check — DOES THE COMPOSITION ACTUALLY WORK?

Before any gate, verify the claim `rung8_lib` is built on: that rung 6's SUnit
layer READS rung 7's LBipolar channels, because its rules bind the presynaptic
channel by an UNTYPED edge traversal. If the cortex silently never activates on
the new retina, every downstream number would be a measurement of a dead layer —
the "inert arm looking stable" the eye agent's positive controls caught, and the
"rule quietly not firing" §10 names as the dangerous failure.

Verify, don't assume. Prints facts; asserts the load-bearing ones.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8_lib import build, run_waves, signed_rf, weights  # noqa: E402


def main():
    print(provenance_line())
    for chan in ("lateral", "degenerate"):
        w, us, anat, bip = build(seed=0, channels=chan, n_units=6)
        n_pre = len(w.s.in_neighbours(us[0], "oo_post"))
        pre_types = set()
        for syn in w.s.in_neighbours(us[0], "oo_post"):
            for b in w.s.in_neighbours(syn, "oo_pre"):
                pre_types.add(w.s.node(b)["type"])

        w0 = weights(w, us)
        run_waves(w, 200)
        w1 = weights(w, us)

        acts = [float(w.s.node(u)["attrs"]["act"]) for u in us]
        rates = [float(w.s.node(u)["attrs"]["rate"]) for u in us]
        thetas = [float(w.s.node(u)["attrs"]["theta"]) for u in us]
        moved = float(np.abs(w1 - w0).max())

        print(f"\n=== channels={chan}")
        print(f"  presynaptic node type(s) : {pre_types}")
        print(f"  synapses/unit            : {n_pre}")
        print(f"  max |act|                : {max(abs(a) for a in acts):.4f}")
        print(f"  max rate                 : {max(rates):.4f}")
        print(f"  max theta                : {max(thetas):.4f}")
        print(f"  max |dw| over 200 steps  : {moved:.4e}")
        print(f"  signed RF range          : "
              f"[{signed_rf(w, us[0]).min():.3f}, {signed_rf(w, us[0]).max():.3f}]")

        # THE LOAD-BEARING FACTS. A layer that never activates, or never learns,
        # would make every arm a measurement of nothing.
        assert max(abs(a) for a in acts) > 0.0, (
            f"{chan}: SUnits NEVER ACTIVATED — the cortex is not reading this "
            "retina; every downstream number would measure a dead layer.")
        assert moved > 0.0, (
            f"{chan}: NO WEIGHT MOVED in 200 steps — the learning rules are not "
            "firing on this retina.")
        if chan == "lateral":
            assert pre_types == {"LBipolar"}, (
                f"lateral arm is not reading rung 7's channels: {pre_types}")
        else:
            assert pre_types == {"Bipolar"}, (
                f"degenerate arm is not reading rung 6's channels: {pre_types}")

    print("\nCOMPOSITION VERIFIED: the cortex activates and learns on BOTH "
          "retinas, with no rule added to either seed.")


if __name__ == "__main__":
    main()
