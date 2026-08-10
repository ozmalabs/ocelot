"""w0_ablation_lib — the shared arm runner for the INITIALISATION ablation.

THE FINDING BEING TESTED (adversarial review, 2026-07-17):
`domains/wave_world.py`'s `add_units(w0=1.0, jitter=0.05)` is a **494:1 DC
prior** — every initial weight strictly positive, ~99.8% of the RF's power in
its constant component. Its comment claimed "NOT structure, just a tie-break".
That is rung 5's measured root cause (`frac(w<0)=0.0000` ⇒ DC-dominated
response ⇒ OSI 0.004) present BEFORE ANY RULE FIRES.

ONE module used by every part of the ablation, so no arm can differ from
another by accident. Arms differ ONLY in `WaveWorld.add_units(init=...)`:

  DC        init="multiplicative", w0=1.0, jitter=0.05   -- THE COMMITTED DEFAULT
  ZERO      init="zero_mean",      w0=0.0, jitter=0.05   -- signed, DC-free
  ZEROM     init="zero_mean",      w0=0.0, jitter=1.0    -- signed, DC-free,
                                                            ||w|| MATCHED to DC

WHY ZEROM EXISTS, DECLARED IN ADVANCE (not a sweep). The DC init has
||w|| ~= sqrt(49) = 7.0; ZERO has ||w|| ~= 0.35. Oja's dynamics are norm-
dependent (the decay term is eta*y^2*w), so a ZERO arm that fails could fail
for the trivial reason that it started 20x too small rather than because it is
DC-free. ZEROM holds ||w|| at the DC arm's value and varies ONLY the DC
component. If ZERO and ZEROM agree, the norm is not the explanation.

No decisions: mechanical world construction + read-out only (CLAUDE.md).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.cortex_sheet import add_cortex, orientation_selectivity  # noqa: E402

H = W = 16
RF = 7
GH = GW = 6
ETA = 5e-4          # rung 2/4/5's committed regime. FROZEN — not a search.

# The three inits, as (label, kwargs-for-add_cortex).
INITS = {
    "DC":    dict(w0=1.0, jitter=0.05, init="multiplicative"),
    "ZERO":  dict(w0=0.0, jitter=0.05, init="zero_mean"),
    "ZEROM": dict(w0=0.0, jitter=1.0,  init="zero_mean"),
}


# --------------------------------------------------------------------------- #
#  THE MEASURE THE REVIEW USED
# --------------------------------------------------------------------------- #
def dc_power_fraction(w: np.ndarray) -> float:
    """Fraction of an RF's total power carried by its CONSTANT component:

        DC_frac = N * mean(w)^2 / sum(w^2)

    1.0 = a pure flat blob (all structure is the DC offset); ~1/N = no DC at
    all. This is the reviewer's statistic and it is pure arithmetic on the
    weights — no engine, no rule, no clock."""
    w = np.asarray(w, float).ravel()
    p = float((w ** 2).sum())
    if p <= 0.0:
        return float("nan")
    return float(len(w) * (w.mean() ** 2) / p)


def dc_ratio(w: np.ndarray) -> float:
    """The reviewer's "494:1": DC power / non-DC (structure) power."""
    f = dc_power_fraction(w)
    return float(f / (1.0 - f)) if f < 1.0 else float("inf")


def frac_negative(w: np.ndarray) -> float:
    w = np.asarray(w, float).ravel()
    return float((w < 0).mean())


def rf_stats(world, units) -> dict:
    """Per-unit DC power fraction / frac(w<0) / anisotropy, averaged. Pure
    read-out."""
    rfs = [world.receptive_field(u) for u in units]
    allw = np.concatenate([r.ravel() for r in rfs])
    return {
        "dc_frac": float(np.mean([dc_power_fraction(r) for r in rfs])),
        "dc_ratio": float(np.mean([dc_ratio(r) for r in rfs])),
        "frac_neg": frac_negative(allw),
        "anis": float(np.mean([orientation_selectivity(r) for r in rfs])),
        "norm": float(np.mean([np.linalg.norm(r) for r in rfs])),
    }


# --------------------------------------------------------------------------- #
#  THE WORLD (mechanical)
# --------------------------------------------------------------------------- #
def build(seed: int, arm: str, *, seeds_list=("vision_waves", "vision_maps"),
          lateral: float = 0.0, eta: float = ETA, gh: int = GH, gw: int = GW):
    """A booted world + a retinotopic sheet whose ONLY difference across arms is
    the initial weights."""
    if arm not in INITS:
        raise ValueError(f"unknown init arm: {arm}")
    s, ag = boot_core()
    load_seeds_into(s, ag, list(seeds_list))
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", float(eta))
    if "vision_maps" in seeds_list:
        s.set_attr(s.nodes("MapParams")[0], "lateral", float(lateral))
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, gh, gw, rf=RF, **INITS[arm])
    return w, us


def run_waves(world, steps: int, *, ignite_every: int = 5) -> None:
    """The formative input: the agent's own spontaneous waves. Clock only."""
    for i in range(steps):
        world.step(ignite_k=1 if i % ignite_every == 0 else 0)


def weights_of(world, units) -> np.ndarray:
    return np.stack([world.receptive_field(u) for u in units])


def drift(a: np.ndarray, b: np.ndarray) -> float:
    """||w(t) - w(t-d)|| / ||w(t)|| — PROTOCOL 2's convergence statistic."""
    n = float(np.linalg.norm(b))
    return float(np.linalg.norm(b - a) / n) if n > 0 else float("nan")


# --------------------------------------------------------------------------- #
#  STATISTICS (rung 4's, reused unchanged — SEED is the unit of analysis)
# --------------------------------------------------------------------------- #
def sign_flip_p(x, n_perm: int = 20000, seed: int = 0) -> float:
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
    print(f"{name:38s} {x.mean():+8.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]   "
          f"p = {p:.4f}   n = {len(x)}")
    return {"mean": float(x.mean()), "lo": lo, "hi": hi, "p": p, "n": len(x)}


# --------------------------------------------------------------------------- #
#  PARALLELISM — mechanical, and it cannot change a number
# --------------------------------------------------------------------------- #
def pmap(fn, args, procs: int = 10):
    """Run `fn` over `args` in a process pool, RESULTS IN INPUT ORDER.

    Every run is a fresh `boot_core()` seeded by its own integer seed and shares
    no state with any other, so this is a scheduling detail and nothing more:
    `pmap(f, xs)` and `[f(x) for x in xs]` return identical values. Verified
    (`tests/test_w0_init_ablation_migrated.py::test_pmap_is_identical_to_serial`)
    rather than assumed — PROTOCOL 4's "re-derive what each arm MEANS after
    every change" applies to the harness too."""
    import multiprocessing as mp
    with mp.get_context("spawn").Pool(procs) as pool:
        return pool.map(fn, args)
