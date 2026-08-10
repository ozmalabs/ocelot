"""calib_pilot — variance-only pilot + the RANGE-EXERCISE classifier.

BURNED seeds only (0-13). Two jobs:

 1. Classify each input as RANGE-EXERCISING or not, from a property of the
    INPUT measured with FROZEN RANDOM weights and NO learning -- i.e. BEFORE
    and INDEPENDENTLY of any calibration outcome. This is what stops
    "range-exercising" from being defined post-hoc as "whatever calibrated"
    (the unfalsifiability trap).

    The classifier: drive spread S = IQR of the unit's drive `act` over the
    input ensemble, in units of the ideal-Gabor drive range. An input that
    does not move `act` cannot place a threshold inside it.

 2. Per-seed SD of each contrast, to fix n by power.

Run: PYTHONPATH=runners/dsl/python python3 scripts/calib_pilot.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.calib_lib import build, run_waves, rpi_of  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from domains.complex_cells import present  # noqa: E402
from domains import vision_corpus as vc  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402

H = W = 16
PILOT = tuple(range(14))


# --------------------------------------------------------------------------- #
#  THE INPUTS. Each is a mechanical generator of 16x16 binary fields -- the
#  adapter supplies unstructured entropy and a clock (PROTOCOL 0). No input
#  carries an orientation the agent is supposed to grow.
# --------------------------------------------------------------------------- #
def _fields_noise(n, seed):
    rng = np.random.default_rng(seed)
    return [(rng.random((H, W)) > 0.5).astype(np.float32) for _ in range(n)]


def _fields_blank(n, seed):
    return [np.zeros((H, W), np.float32) for _ in range(n)]


def _fields_static(n, seed):
    rng = np.random.default_rng(seed)
    one = (rng.random((H, W)) > 0.5).astype(np.float32)
    return [one for _ in range(n)]


_BSDS = None


def _fields_video(n, seed):
    global _BSDS
    if _BSDS is None:
        _BSDS = vc.bsds_crops(n=400, crop=H, seed=7)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(_BSDS), n)
    out = []
    for i in idx:
        c = np.asarray(_BSDS[i], float)
        out.append((c > np.median(c)).astype(np.float32))
    return out


FIELDS = {"noise": _fields_noise, "blank": _fields_blank,
          "static": _fields_static, "video": _fields_video}


def drive_spread(inp, seed, n=64):
    """S = IQR of `act` over the input ensemble, FROZEN random weights, NO
    learning, theta pinned. A property of the INPUT x the anatomy, measured
    before any calibration happens."""
    w, us, _ = build(seed=seed, eta=5e-4)
    set_params(w, homeo=0.0, oo_eta=0.0, frozen=1.0)
    acts = []
    if inp == "waves":
        for i in range(n):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
            acts.append([float(w.s.node(u)["attrs"]["act"]) for u in us])
    else:
        for f in FIELDS[inp](n, seed):
            present(w, f)
            acts.append([float(w.s.node(u)["attrs"]["act"]) for u in us])
    A = np.array(acts)                      # (n, units)
    return float(np.mean(np.percentile(A, 75, axis=0)
                         - np.percentile(A, 25, axis=0)))


def theta_only(inp, seed, steps=400):
    """CALIBRATION, ISOLATED: theta adapts on `inp`, oo_eta=0 so no weight
    moves. Then the frozen probe."""
    w, us, _ = build(seed=seed, eta=5e-4)
    set_params(w, homeo=1.0, oo_eta=0.0, frozen=0.0)
    if inp == "waves":
        run_waves(w, steps)
    else:
        F = FIELDS[inp](steps, seed)
        for f in F:
            present(w, f)
    rpi, st = rpi_of(w, us)
    return float(rpi.mean()), float(st["osi"].mean())


def main():
    print(provenance_line())
    print()
    print("RANGE-EXERCISE CLASSIFIER (frozen random weights, no learning, "
          "theta pinned)")
    print(f"{'input':>8} {'drive IQR':>11}")
    for inp in ("waves", "noise", "video", "static", "blank"):
        s = np.mean([drive_spread(inp, sd) for sd in (0, 1, 2)])
        print(f"{inp:>8} {s:>11.4f}")
    print()
    print("theta_only RPI per input (burned seeds 0-13)")
    print(f"{'input':>8} {'RPI mean':>9} {'SD':>7} {'OSI':>7}")
    res = {}
    for inp in ("waves", "noise", "video", "static", "blank"):
        v = [theta_only(inp, sd) for sd in PILOT]
        r = np.array([a for a, _ in v])
        o = np.array([b for _, b in v])
        res[inp] = r
        print(f"{inp:>8} {r.mean():>9.4f} {r.std(ddof=1):>7.4f} {o.mean():>7.4f}")
    print()
    print("paired contrasts (SD is what fixes n)")
    for a, b in (("waves", "noise"), ("waves", "video"), ("waves", "blank"),
                 ("waves", "static")):
        d = res[a] - res[b]
        print(f"  {a}-{b:<7} mean={d.mean():+.4f}  SD={d.std(ddof=1):.4f}")


if __name__ == "__main__":
    main()
