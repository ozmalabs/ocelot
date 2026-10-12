#!/usr/bin/env python
"""THE SPARSITY INSTRUMENT — does a change-detecting retina go sparse on natural
scenes? (`VISION_CHANGE_PREREG.md`; PROTOCOL §1 all five clauses, §3, §13.)

Pre-registered: block 17000-17999. The pre-reg is committed BEFORE this runs.

WHY THIS EXISTS. `wave_world.drive()` median-split every frame, so `driven%` was
EXACTLY 50.00 in every regime at every size — the adapter asserting a statistic.
That made natural-image sparsity unmeasurable, and sparsity is the whole question
behind the scale wall: the wall is the Python<->Rust FFI (75-82% of budget), the
curve is linear (exponent 0.971), and the human fovea (~150k cells) extrapolates
to ~750ms, 15x over budget. An EVENT-DRIVEN retina would only rescue that IF the
retina is actually sparse. This measures whether it is.

§1's FIVE CLAUSES, and clause 5 runs FIRST (§13.2/FM-0: a mechanism must be shown
to MOVE something downstream before its statistics mean anything).

CLAUSE 4 — THE POSITIVE CONTROL IS NOT `tick()`'s RETURN. The scaling agent's
control was NEARLY INERT: `tick()` counts progressing rule VISITS and reads 3 on
a live retina AND on a near-idle one. It is not reused. Instead: a state
histogram + a distinct-value count + the driven/bursting totals — an arm that is
dead is VISIBLY dead (§1.1: a dead arm scores a perfect floor off a guarded
division, and is indistinguishable from a good one).

Python here is a world adapter: it builds frames, ticks, and reads attrs back.
Every DECISION (what counts as a change) is a rule in `domain_data/vision_change.json`.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402

H = W = 16

# The BSDS300 photographs live in the canonical tree (`data/` is untracked, so a
# worktree has none). READ-ONLY: §11 forbids shared MUTABLE state; reading a
# pinned corpus is the same category as rung 2's committed frame cache.
_BSDS = os.path.join("/home/matt/ozma/internal/research/experiments/gamma-substrate",
                     "data", "vision_curriculum", "BSDS300", "images", "train")


def _bsds(idx: int) -> np.ndarray:
    """One real photograph, greyscale, [0,1]. POSITIVE-CONTROLLED by the caller:
    an absence here must raise, never return an empty array — `bsds_crops()`
    returns `zeros((0,...))` when the corpus is missing, which is §12's soft
    accessor in array form (a missing corpus would silently read as 'all black',
    and a black scene has no changes, which would fake the sparsity result)."""
    paths = sorted(f for f in os.listdir(_BSDS) if f.endswith(".jpg"))
    if not paths:
        raise RuntimeError(f"BSDS300 corpus is EMPTY at {_BSDS} — refusing to "
                           f"measure sparsity against an absence.")
    g = Image.open(os.path.join(_BSDS, paths[idx % len(paths)])).convert("L")
    return np.asarray(g, np.float32) / 255.0


def _subpix(g: np.ndarray, r: float, c: float) -> np.ndarray:
    r0, c0 = int(np.floor(r)), int(np.floor(c))
    fr, fc = r - r0, c - c0
    a = g[r0:r0 + H, c0:c0 + W]
    b = g[r0 + 1:r0 + 1 + H, c0:c0 + W]
    d = g[r0:r0 + H, c0 + 1:c0 + 1 + W]
    e = g[r0 + 1:r0 + 1 + H, c0 + 1:c0 + 1 + W]
    return (a * (1 - fr) * (1 - fc) + b * fr * (1 - fc)
            + d * (1 - fr) * fc + e * fr * fc).astype(np.float32)


def frames(regime: str, seed: int, n: int, drift_px: float = 1.0,
           img: int | None = None):
    """The four regimes. Mechanical frame generation — no graph state read.

    `img` PINS the photograph independently of `seed`. Load-bearing: the first
    cut picked the image as `seed % 200`, so every row of the drift surface
    varied the IMAGE and the DRIFT together and the surface came out
    non-monotonic (98.7 -> 8.3 -> 89.3 -> 55.9 -> 91.4) — a smooth sky and a
    textured hedge have wildly different sparsity at the same drift. The
    confound, not the mechanism, was doing the talking."""
    rng = np.random.default_rng(seed)
    if regime == "waves":
        return [None] * n                       # no visual input at all
    g = _bsds(seed % 200 if img is None else img)
    r, c = 100.0, 100.0
    out = []
    for _ in range(n):
        if regime == "drift":
            r = float(np.clip(r + rng.normal(0, drift_px), 1, g.shape[0] - H - 2))
            c = float(np.clip(c + rng.normal(0, drift_px), 1, g.shape[1] - W - 2))
            out.append(_subpix(g, r, c))
        elif regime == "stabilised":
            out.append(_subpix(g, 100.0, 100.0))          # the IDENTICAL frame
        elif regime == "noise":
            out.append(rng.random((H, W)).astype(np.float32))
        else:
            raise ValueError(regime)
    return out


def boot(change: float, *, sustain: float = 1.0, seed: int = 0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    w = WaveWorld(s, h=H, w=W, seed=seed)
    cp = s.nodes("ChangeParams")
    assert len(cp) == 1, f"ChangeParams must be a singleton, got {len(cp)}"
    s.set_attr(cp[0], "change", float(change))
    s.set_attr(cp[0], "sustain", float(sustain))
    return s, w


def run(regime, *, change, seed, n=120, drift_px=1.0, sustain=1.0, ignite_k=0,
        img=None):
    s, w = boot(change, sustain=sustain, seed=seed)
    fs = frames(regime, seed, n, drift_px, img=img)
    driven, bursting, states = [], [], []
    # CLAUSE 4, per CHANNEL: each rule stamps its own phase key with the step it
    # fired on, so "did this channel fire at all?" is read off a POSITIVE stamp,
    # never off a guarded division or an absence (§1.1). This is what caught the
    # sustained channel being inert.
    chan = {"med": [], "on": [], "off": [], "sus": []}
    for f in fs:
        w.step(ignite_k=ignite_k, frame=f)
        at = [s.node(n_)["attrs"] for n_ in w.cells.values()]
        driven.append(np.mean([a.get("driven", 0.0) == 1.0 for a in at]))
        st_ = float(s.node(w.retina)["attrs"]["step"])
        for k, key in (("med", "dstep_med"), ("on", "dstep_on"),
                       ("off", "dstep_off"), ("sus", "dstep_sus")):
            chan[k].append(np.mean([a.get(key, -999.0) == st_ for a in at]))
        bursting.append(np.mean([a.get("bursting", 0.0) == 1.0 for a in at]))
        states.append([a.get("state") for a in at])
    return {"driven": np.array(driven), "bursting": np.array(bursting),
            "states": states, "chan": {k: np.array(v) for k, v in chan.items()}}


def pct(x):
    return 100.0 * float(np.mean(x))


def main():
    print("=" * 78)
    print("THE SPARSITY INSTRUMENT — VISION_CHANGE_PREREG.md, block 17000-17999")
    print("=" * 78)

    # ---- CLAUSE 5 FIRST (§13.2 / FM-0): does the mechanism MOVE anything? ----
    print("\n[CLAUSE 5] VACUITY GATE — toggle `change`, measure D = max|on - off|")
    a = run("drift", change=0.0, seed=17000)
    b = run("drift", change=1.0, seed=17000)
    d_driven = float(np.max(np.abs(a["driven"] - b["driven"])))
    d_burst = float(np.max(np.abs(a["bursting"] - b["bursting"])))
    print(f"  D_driven   = {d_driven:.6e}")
    print(f"  D_bursting = {d_burst:.6e}")
    if d_driven == 0.0 and d_burst == 0.0:
        print("  VERDICT: **VACUOUS** — the mechanism reaches nothing. STOP; burn no seed.")
        return 1
    print("  VERDICT: LOAD-BEARING — the change rules move `driven` AND `bursting`.")

    # ---- CLAUSE 4: arms alive (NOT tick()'s return; NOT a guarded division) ----
    print("\n[CLAUSE 4] ARMS ALIVE — state histogram + distinct values")
    for nm, res in (("change=0 (median)", a), ("change=1 (change-det)", res_b := b)):
        last = res["states"][-1]
        uniq = sorted(set(last))
        ch = "  ".join(f"{k}={pct(v):5.2f}%" for k, v in res["chan"].items())
        print(f"  {nm:22s} states={uniq} distinct={len(uniq)} "
              f"driven%={pct(res['driven']):.2f} bursting%={pct(res['bursting']):.2f}")
        print(f"  {'':22s} per-channel fired%: {ch}")

    # ---- CLAUSE 1 + 2: floor and ideal ----
    print("\n[CLAUSE 1/2] FLOOR (stabilised => ~0%) and IDEAL (dynamic noise => ~100%)")
    # The floor belongs to the CHANGE detector, i.e. the TRANSIENT channel
    # (sustain=0). With the sustained channel ON a stabilised image SHOULD keep
    # firing — that is the mechanism, not a leak, and scoring it as a floor
    # failure would be reading the feature as a bug.
    fl = run("stabilised", change=1.0, seed=17001, sustain=0.0, img=0)
    idl = run("noise", change=1.0, seed=17002, sustain=0.0, img=0)
    print(f"  floor  stabilised (transient only)  driven% = {pct(fl['driven']):6.2f}")
    print(f"  ideal  noise      (transient only)  driven% = {pct(idl['driven']):6.2f}")

    # ---- CLAUSE 3: duration-stability ----
    print("\n[CLAUSE 3] DURATION-STABILITY — same input, does driven% drift with n?")
    for n in (30, 60, 120, 240):
        r = run("drift", change=1.0, seed=17003, n=n, img=0)
        print(f"  n={n:4d}  driven% = {pct(r['driven']):6.2f}")

    # ---- THE MEASUREMENT: four regimes, median vs change ----
    print("\n" + "=" * 78)
    print("THE FOUR REGIMES — driven%, median split vs change detection")
    print("=" * 78)
    print(f"  {'regime':<14}{'median (change=0)':>20}{'change=1':>14}")
    for i, regime in enumerate(("waves", "stabilised", "drift", "noise")):
        # PIN the photograph: `seed % 200` picked a DIFFERENT image per regime,
        # and image identity swings the sustained channel from 18% to 95%.
        # `ignite_k=1` on the waves arm so it is a LIVE arm, not a silent one
        # (§1 clause 4: "scores at the floor" is satisfied by death).
        k = 1 if regime == "waves" else 0
        m = run(regime, change=0.0, seed=17010 + i, img=0, ignite_k=k)
        c = run(regime, change=1.0, seed=17010 + i, img=0, ignite_k=k)
        st = sorted(set(c["states"][-1]))
        print(f"  {regime:<14}{pct(m['driven']):>19.2f}%{pct(c['driven']):>13.2f}%"
              f"   [alive: burst%={pct(c['bursting']):5.2f} states={st}]")

    # ---- the surface: sparsity is a function of drift AND threshold ----
    print("\n" + "=" * 78)
    print("THE SURFACE — driven% vs drift amplitude (threshold = the shot-noise")
    print("floor, which FALLS OUT; nothing here is tuned)")
    print("=" * 78)
    for img in (0, 7):
        print(f"  -- photograph #{img} (PINNED; only the drift varies) --")
        for j, dpx in enumerate((1.0, 0.5, 0.25, 0.1, 0.05, 0.02)):
            r = run("drift", change=1.0, seed=17020 + j, drift_px=dpx, img=img)
            print(f"     drift sigma = {dpx:4.2f} px   driven% = {pct(r['driven']):6.2f}")

    # ---- TRAP 2: the transient-only arm is the TAUTOLOGY, as a control ----
    print("\n" + "=" * 78)
    print("TRAP 2 — transient-only (sustain=0) is the tautology; it is a CONTROL,")
    print("not the default. Under stabilisation a pure differentiator CANNOT fire.")
    print("=" * 78)
    for sus in (0.0, 1.0):
        st = run("stabilised", change=1.0, seed=17030, sustain=sus)
        dr = run("drift", change=1.0, seed=17031, sustain=sus)
        print(f"  sustain={sus:.0f}   stabilised driven% = {pct(st['driven']):6.2f}   "
              f"drift driven% = {pct(dr['driven']):6.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
