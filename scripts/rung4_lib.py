"""RUNG 4 — the shared arm runner + statistics.

ONE module used by BOTH the pilot and the confirmatory run, so the confirmatory
run cannot differ from the pilot by accident. The pilot fixes n; the confirmatory
run changes only the seed block.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.cortex_sheet import add_cortex, map_stats

H = W = 16
RF = 7
GH = GW = 6
ETA = 5e-4          # the MEASURED stable Oja regime (2e-3 diverges to NaN)
STEPS = 3200        # the fixed point: anisotropy plateaus, drift -> 0.026
N_PERM_NULL = 200   # shuffles per seed for the shuffled-position null


def arm(lateral: float, seed: int, *, steps: int = STEPS) -> dict:
    """Run ONE arm: waves only, no vision at all. The arms differ ONLY in
    MapParams.lateral — graph data the agent holds, not a Python code path."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    s.set_attr(s.nodes("MapParams")[0], "lateral", float(lateral))
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, GH, GW, rf=RF)
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    return map_stats(w, us, GH, GW, n_perm=N_PERM_NULL, seed=seed)


def sign_flip_p(x, n_perm: int = 20000, seed: int = 0) -> float:
    """Two-sided sign-flip permutation test on paired per-SEED values against a
    null of zero. SEED is the unit of analysis (PROTOCOL 4)."""
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    obs = abs(float(x.mean()))
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(x)))
    null = np.abs((signs * x).mean(axis=1))
    return float((np.sum(null >= obs - 1e-12) + 1) / (n_perm + 1))


def boot_ci(x, n_boot: int = 20000, seed: int = 0):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    m = rng.choice(x, size=(n_boot, len(x)), replace=True).mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def report(name: str, x) -> dict:
    x = np.asarray(x, float)
    lo, hi = boot_ci(x)
    p = sign_flip_p(x)
    print(f"{name:34s} {x.mean():+8.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]   "
          f"p = {p:.4f}   n = {len(x)}")
    return {"mean": float(x.mean()), "lo": lo, "hi": hi, "p": p, "n": len(x)}
