"""TWO EYES — the FEASIBILITY probe (not a rung; no pre-registration consumed).

Question, and ONLY this question: does instantiating a SECOND eye on one
substrate already work, and do the two eyes carry the correlation structure
Miller 1994 requires (correlated WITHIN an eye, uncorrelated BETWEEN)?

This burns no confirmatory seed. It is the check that decides whether the
"de-singleton the eye" task exists at all.

The instrument is positive-controlled per PROTOCOL 1: the same correlation
statistic is run on (a) two INDEPENDENT eyes, (b) one eye against ITSELF
(the perfectly-correlated ideal exemplar => must read ~1), and (c) shuffled
activity (the floor => must read ~0). A correlation measure that cannot tell
those three apart cannot support any claim about segregation.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains.wave_world import WaveWorld, record  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


def corr(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r over flattened activity movies."""
    a = np.asarray(a, float).ravel()
    b = np.asarray(b, float).ravel()
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def within_eye_neighbour_corr(mv: np.ndarray) -> float:
    """Mean correlation between horizontally-adjacent cells' time series.
    This is 'correlated WITHIN an eye' stated as a number."""
    T, h, w = mv.shape
    rs = []
    for r in range(h):
        for c in range(w - 1):
            x, y = mv[:, r, c], mv[:, r, c + 1]
            if x.std() > 1e-12 and y.std() > 1e-12:
                rs.append(np.corrcoef(x, y)[0, 1])
    return float(np.mean(rs)) if rs else float("nan")


def main() -> None:
    print(ep.provenance_line())
    H = W = 16
    STEPS = 120

    # ---- TWO EYES ON ONE SUBSTRATE ----------------------------------------
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    left = WaveWorld(s, h=H, w=W, seed=101)
    right = WaveWorld(s, h=H, w=W, seed=202)

    print(f"\nleft.retina  = {left.retina}")
    print(f"right.retina = {right.retina}")
    print(f"distinct hubs: {left.retina != right.retina}")
    print(f"cells: left={len(left.cells)} right={len(right.cells)} "
          f"(disjoint: {not (set(map(str, left.cells.values())) & set(map(str, right.cells.values())))})")

    # Interleave the two eyes' clocks: both advance on the same tick.
    mvl, mvr = [], []
    for i in range(STEPS):
        k = 1 if i % 5 == 0 else 0
        left.step(ignite_k=k)
        right.step(ignite_k=k)
        mvl.append(left.frame())
        mvr.append(right.frame())
    mvl = np.stack(mvl)
    mvr = np.stack(mvr)

    print(f"\nactivity: left={mvl.mean():.4f}  right={mvr.mean():.4f}")
    if mvl.mean() < 1e-9 or mvr.mean() < 1e-9:
        print("!! AN EYE IS DEAD — the second eye did not produce waves.")

    # ---- THE INSTRUMENT, POSITIVE-CONTROLLED (PROTOCOL 1) -----------------
    r_between = corr(mvl, mvr)
    r_ideal = corr(mvl, mvl)                       # ideal exemplar => ~1
    rng = np.random.default_rng(0)
    shuf = mvl.copy().ravel()
    rng.shuffle(shuf)
    r_floor = corr(mvl.ravel(), shuf)              # floor => ~0

    print("\n--- INSTRUMENT CALIBRATION (measured in-run, never inherited) ---")
    print(f"  ideal  (eye vs ITSELF)      r = {r_ideal:+.4f}   [must be ~1]")
    print(f"  floor  (eye vs SHUFFLED)    r = {r_floor:+.4f}   [must be ~0]")

    print("\n--- THE MILLER CONDITION ---")
    print(f"  BETWEEN eyes (independent)  r = {r_between:+.4f}")
    wl = within_eye_neighbour_corr(mvl)
    wr = within_eye_neighbour_corr(mvr)
    print(f"  WITHIN left  (neighbours)   r = {wl:+.4f}")
    print(f"  WITHIN right (neighbours)   r = {wr:+.4f}")

    # ---- THE CONTROL THAT MUST BE NULL: same seed => same waves -----------
    s2, ag2 = boot_core()
    load_seeds_into(s2, ag2, ["vision_waves"])
    a = WaveWorld(s2, h=H, w=W, seed=303)
    b = WaveWorld(s2, h=H, w=W, seed=303)          # IDENTICAL seed
    mva, mvb = [], []
    for i in range(STEPS):
        k = 1 if i % 5 == 0 else 0
        a.step(ignite_k=k)
        b.step(ignite_k=k)
        mva.append(a.frame())
        mvb.append(b.frame())
    r_corr_arm = corr(np.stack(mva), np.stack(mvb))
    print(f"\n  CORRELATED arm (same seed)  r = {r_corr_arm:+.4f}   "
          f"[the control that must NOT segregate]")

    print("\n--- VERDICT ---")
    ok_instr = (r_ideal > 0.99) and (abs(r_floor) < 0.05)
    print(f"  instrument calibrated: {ok_instr}")
    print(f"  two eyes run independently: "
          f"{mvl.mean() > 1e-9 and mvr.mean() > 1e-9 and abs(r_between) < 0.2}")
    print(f"  correlated arm is genuinely correlated: {r_corr_arm > 0.9}")


if __name__ == "__main__":
    main()
