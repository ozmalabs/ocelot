"""IS THE WITHIN-EYE CORRELATION REALLY ABSENT, OR IS ZERO-LAG THE WRONG READ?

The feasibility probe measured ZERO-LAG neighbour correlation and got ~-0.04.
A travelling wave reaches a cell and its neighbour at DIFFERENT times, and the
refractory period makes them mutually exclusive at any instant — so zero-lag
correlation is the wrong instrument BY CONSTRUCTION, and would read ~0 even for
a perfect wave.

Miller 1994 / Butts consume the correlation over the window the LEARNING RULE
integrates, not the instantaneous one. So: sweep the smoothing window and ask
whether a within-vs-between separation appears at ANY timescale.

This is instrument calibration (PROTOCOL 1), not metric surgery (PROTOCOL 5):
no gate has been run and no hypothesis has failed. The point is to find out
whether a correlation signal EXISTS before anything is pre-registered on it.

The decisive positive control: a SYNTHETIC travelling wave, where the answer is
known by construction. If the instrument cannot see within-eye correlation THERE,
the instrument is broken. If it CAN, and the substrate's waves still read flat,
the substrate genuinely lacks the structure.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import numpy as np  # noqa: E402

from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


def smooth(mv: np.ndarray, win: int) -> np.ndarray:
    """Box-filter each cell's time series over `win` steps: the synaptic
    integration window, stated explicitly."""
    if win <= 1:
        return mv
    k = np.ones(win) / win
    T, h, w = mv.shape
    out = np.empty_like(mv, dtype=float)
    for r in range(h):
        for c in range(w):
            out[:, r, c] = np.convolve(mv[:, r, c], k, mode="same")
    return out


def neighbour_corr(mv: np.ndarray) -> float:
    T, h, w = mv.shape
    rs = []
    for r in range(h):
        for c in range(w - 1):
            x, y = mv[:, r, c], mv[:, r, c + 1]
            if x.std() > 1e-12 and y.std() > 1e-12:
                rs.append(np.corrcoef(x, y)[0, 1])
    return float(np.mean(rs)) if rs else float("nan")


def cross_eye_corr(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation between RETINOTOPICALLY MATCHED cells in the two eyes —
    the quantity ocular-dominance segregation actually consumes."""
    T, h, w = a.shape
    rs = []
    for r in range(h):
        for c in range(w):
            x, y = a[:, r, c], b[:, r, c]
            if x.std() > 1e-12 and y.std() > 1e-12:
                rs.append(np.corrcoef(x, y)[0, 1])
    return float(np.mean(rs)) if rs else float("nan")


def synthetic_wave(T: int, h: int, w: int, seed: int) -> np.ndarray:
    """POSITIVE CONTROL: a travelling wave by construction. A front sweeps
    across the grid at 1 cell/step from a random edge, repeatedly. Neighbours
    ARE correlated at the wave's own timescale, by construction."""
    rng = np.random.default_rng(seed)
    mv = np.zeros((T, h, w))
    t = 0
    while t < T:
        ang = rng.uniform(0, 2 * np.pi)
        dx, dy = np.cos(ang), np.sin(ang)
        off = rng.uniform(0, 10)
        for dt in range(20):
            if t >= T:
                break
            for r in range(h):
                for c in range(w):
                    phase = dx * c + dy * r + off
                    if abs(phase - dt * 1.0) < 1.5:
                        mv[t, r, c] = 1.0
            t += 1
    return mv


def main() -> None:
    print(ep.provenance_line())
    H = W = 16
    STEPS = 200

    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    left = WaveWorld(s, h=H, w=W, seed=101)
    right = WaveWorld(s, h=H, w=W, seed=202)
    mvl, mvr = [], []
    for i in range(STEPS):
        k = 1 if i % 5 == 0 else 0
        left.step(ignite_k=k)
        right.step(ignite_k=k)
        mvl.append(left.frame())
        mvr.append(right.frame())
    mvl, mvr = np.stack(mvl), np.stack(mvr)

    syn_a = synthetic_wave(STEPS, H, W, seed=1)
    syn_b = synthetic_wave(STEPS, H, W, seed=2)

    print(f"\nsubstrate activity: L={mvl.mean():.4f} R={mvr.mean():.4f}   "
          f"synthetic: A={syn_a.mean():.4f} B={syn_b.mean():.4f}")
    print("\nwin |        SUBSTRATE WAVES        |     SYNTHETIC WAVE (control)")
    print("    | within-eye  between  separ.   | within-eye  between  separ.")
    print("----+-------------------------------+------------------------------")
    for win in (1, 2, 4, 8, 16, 32):
        sl, sr = smooth(mvl, win), smooth(mvr, win)
        wi = 0.5 * (neighbour_corr(sl) + neighbour_corr(sr))
        be = cross_eye_corr(sl, sr)
        sa, sb = smooth(syn_a, win), smooth(syn_b, win)
        cwi = 0.5 * (neighbour_corr(sa) + neighbour_corr(sb))
        cbe = cross_eye_corr(sa, sb)
        print(f"{win:3d} |   {wi:+.4f}   {be:+.4f}   {wi - be:+.4f}   |"
              f"   {cwi:+.4f}   {cbe:+.4f}   {cwi - cbe:+.4f}")

    print("\nREADING: `separ.` = within-eye minus between-eye. That gap IS the "
          "Miller condition. The synthetic column is the positive control: if "
          "the substrate column stays flat where the control separates, the "
          "waves lack the structure — not the instrument.")


if __name__ == "__main__":
    main()
