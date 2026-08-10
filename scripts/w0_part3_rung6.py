"""PART 3 — RUNG 6: the ablation is ARCHITECTURALLY EMPTY, and here is the proof.

The task asked for rung 6 re-measured "both ways". It cannot be, and the reason
is the finding — so it is MEASURED rather than asserted:

 1. **A zero-mean init is forbidden by the architecture, not by taste.**
    `seeds/vision_onoff.json`'s `oo_learn_sub` clips every weight to
    `[0, oo_wmax]` — that is DALE'S LAW, a RULE the agent holds, and rung 6's
    whole design premise. A negative initial weight is not a different arm; it
    is a state the first rule firing deletes.

 2. **Rung 6 HAS NO DC PRIOR TO ABLATE.** Its cells read the EFFECTIVE RF
    `w+ - w-`, and ON/OFF start at the SAME `w0` with INDEPENDENT jitter, so
    the effective RF is already zero-mean at step 0 —
    `add_signed_units`'s docstring says so ("the initial effective RF (w+ - w-)
    is ~0 everywhere"). This part MEASURES that claim with the reviewer's own
    statistic instead of trusting the docstring.

If (2) holds, rung 6's convergence failure (runaway at eta=5e-4; empty at the
0.3168 floor at eta=1e-4) cannot be an artifact of the DC prior, because there
is no DC prior in the quantity its rules and its probe both read.
"""
from __future__ import annotations

import numpy as np

from scripts.rung6_lib import build, RF
from scripts.w0_ablation_lib import dc_power_fraction, frac_negative, dc_ratio
from domains.onoff_world import signed_rf
from domains.engine_provenance import provenance_line


def _chan(world, u, pol: float):
    """One polarity's weights alone, laid out by (drow, dcol). Pure query."""
    import numpy as _np
    rf = int(world.s.node(u)["attrs"]["rf"]); half = rf // 2
    a = _np.zeros((rf, rf), _np.float32)
    for syn in world.s.in_neighbours(u, "oo_post"):
        at = world.s.node(syn)["attrs"]
        if float(at["polarity"]) == pol:
            a[int(at["drow"]) + half, int(at["dcol"]) + half] = float(at["weight"])
    return a


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 3 — RUNG 6: is there a DC prior in the quantity the cell READS?")
    print("=" * 78)

    per_chan, eff = [], []
    for seed in range(8):
        w, us, bip = build(seed=seed, n_units=6)
        for u in us:
            wp = _chan(w, u, 1.0)      # the ON channel alone
            er = signed_rf(w, u)       # w+ - w-  : what the SUnit actually reads
            per_chan.append((dc_power_fraction(wp), frac_negative(wp)))
            eff.append((dc_power_fraction(er), frac_negative(er)))

    pc = np.array(per_chan)
    ef = np.array(eff)
    print(f"\n{'quantity':34s} {'DC power frac':>14s} {'DC:structure':>13s} "
          f"{'frac(w<0)':>10s}")
    print(f"{'ONE CHANNEL (w+) — Dale-clipped':34s} {pc[:,0].mean():14.5f} "
          f"{pc[:,0].mean()/(1-pc[:,0].mean()):12.1f}:1 {pc[:,1].mean():10.4f}")
    print(f"{'EFFECTIVE RF (w+ - w-) — READ':34s} {ef[:,0].mean():14.5f} "
          f"{ef[:,0].mean()/(1-ef[:,0].mean()):12.3f}:1 {ef[:,1].mean():10.4f}")
    print(f"\nno-DC floor for a {RF}x{RF} RF (1/N) = {1.0/(RF*RF):.5f}")
    print("\nREAD-OUT: rung 5's blocker is per-CHANNEL and rung 6 inherits it "
          "there;\nbut the SUnit reads the EFFECTIVE RF, which starts at the "
          "no-DC floor.\nThere is no DC prior in rung 6's read quantity, so "
          "there is nothing to ablate.")
