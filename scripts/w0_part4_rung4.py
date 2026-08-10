"""PART 4 — RUNG 4's MAP INTERACTION, RE-MEASURED BOTH WAYS.

Rung 4's committed claim (`VISION_RUNG4_PREREG.md`): a map forms from waves
alone, and the MECHANISM INTERACTION (lateral ON - lateral OFF) is **-6.91**,
CI [-7.46, -6.37], p<0.0001, n=70. The ablated (lateral OFF) arm is NOT null
(-13.25) because retinotopic RF overlap — anatomy the adapter wires — accounts
for most of the raw smoothness, which is exactly why the pre-registered test was
the INTERACTION and not the simple effect.

THIS IS A REPRODUCTION, NOT A RECONSTRUCTION: it calls rung 4's OWN committed
runner (`scripts/rung4_lib.arm` / `map_stats` / `sign_flip_p` / `boot_ci`), on
rung 4's OWN confirmatory seeds (5000-5069), changing exactly ONE thing — the
`init=` handed to `add_cortex`. The DC arm therefore doubles as a fidelity check
on the whole apparatus: it must land on -6.91.
"""
from __future__ import annotations

import numpy as np

from scripts.rung4_lib import (H, W, RF, GH, GW, ETA, STEPS, N_PERM_NULL,
                               report)
from scripts.w0_ablation_lib import INITS, pmap
from domains.engine_provenance import provenance_line

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.cortex_sheet import add_cortex, map_stats

N_SEEDS = 70
SEEDS = list(range(5000, 5000 + N_SEEDS))    # rung 4's OWN confirmatory block


def arm(lateral: float, seed: int, init: str, *, steps: int = STEPS) -> dict:
    """rung4_lib.arm, with `init` threaded through. Identical in every other
    respect — same seeds list, same params, same STEPS, same map_stats."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    s.set_attr(s.nodes("MapParams")[0], "lateral", float(lateral))
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, GH, GW, rf=RF, **INITS[init])
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    return map_stats(w, us, GH, GW, n_perm=N_PERM_NULL, seed=seed)


def _run(a):
    """Pool entry point: (lateral, seed, init) -> map_stats dict."""
    return arm(a[0], a[1], a[2])


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 4 — RUNG 4 MAP INTERACTION, BOTH INITS (rung 4's own runner)")
    print(f"n={N_SEEDS} seeds {SEEDS[0]}-{SEEDS[-1]} (rung 4's own confirmatory "
          f"block: a REPRODUCTION)  steps={STEPS}")
    print("committed: d_on = -20.16 ; INTERACTION (lat ON - OFF) = -6.91 "
          "CI [-7.46, -6.37]")
    print("=" * 78)
    out = {}
    for init in INITS:
        on = pmap(_run, [(1.0, sd, init) for sd in SEEDS])
        off = pmap(_run, [(0.0, sd, init) for sd in SEEDS])
        # rung 4's statistic: d = smoothness - shuffled null, per seed & arm.
        d_on = np.array([r["d"] for r in on])
        d_off = np.array([r["d"] for r in off])
        out[init] = {"on": d_on, "off": d_off}
        print(f"\n--- {init}")
        report("  d_on   (lateral ON)", d_on)
        report("  d_off  (lateral OFF, ablated)", d_off)
        report("  INTERACTION (ON - OFF)", d_on - d_off)
        print(f"  mean selectivity: ON {np.mean([r['selectivity'] for r in on]):.4f}  "
              f"OFF {np.mean([r['selectivity'] for r in off]):.4f}")

    print("\n" + "=" * 78)
    print("THE ABLATION: does the init move rung 4's pre-registered statistic?")
    print("=" * 78)
    for init in ("ZERO", "ZEROM"):
        report(f"INTERACTION  {init} - DC",
               (out[init]["on"] - out[init]["off"]) -
               (out["DC"]["on"] - out["DC"]["off"]))
