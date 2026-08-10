"""Cascade net on REAL ink — the new net type against real Omniglot pen data.

Fits a real human pen trajectory t -> (x, y) (Lake, Salakhutdinov & Tenenbaum
2015, strokes_background) with a residual cascade of weak local-delta blocks
(domains/cascade_net.py). Each block learns, by a local NLMS delta rule with no
backprop, the SURPRISE the previous blocks could not explain. The question this
answers empirically: what does DEPTH-by-residual-cascade buy on a real signal,
and how does it compare to equal-parameter BREADTH (one wide block)?

Findings (see the committed run in results/cascade_ink/): on real ink a single
weak block underfits; stacking blocks recovers ~15-20% of that error (depth is
real). But for a smooth low-frequency pen trajectory an equal-parameter single
WIDE block is the more efficient axis — the cascade's niche is bounded-footprint
INCREMENTAL/anytime capacity (add one retirable reflex block at a time, the net
economy's pay-as-you-go), not accuracy-per-parameter supremacy. This is the
honest complement of the synthetic gate (tests/test_cascade_net_migrated.py),
which proved depth adds capacity vs a single SAME-width block.

Data (real human pen trajectories, ~44MB, gitignored under data/):
  mkdir -p data/omniglot && cd data/omniglot
  for z in strokes_background strokes_evaluation; do \
    curl -sSL -o $z.zip https://github.com/brendenlake/omniglot/raw/master/python/$z.zip \
    && unzip -q $z.zip; done

Run: OMNIGLOT_DIR=data/omniglot PYTHONPATH=. python scripts/cascade_ink_demo.py
"""
import os, glob, base64
import numpy as np
os.environ.setdefault("OMNIGLOT_DIR", "data/omniglot")
from domains.omniglot_world import load_strokes_t
from substrate_rs import _native
from domains.cascade_net import build, forward, train_step

_N = ("CascadeNet", "NetworkAssemblage", "AssemblageStep", "WeightTensor")
_E = ("has_block", "has_step", "has_weight")


def _fresh():
    s = _native.Substrate()
    for a in _N:
        for b in _N:
            for et in _E:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "x"})
    return s


def char_traj(path):
    """Whole-character trajectory t->(x,y): pen-down strokes concatenated along
    real pen-time, centred and scaled to a unit box."""
    strokes, _ = load_strokes_t(path)
    strokes = [s for s in strokes if s.shape[0] >= 3]
    if not strokes:
        return None
    xy = np.concatenate([s[:, :2] for s in strokes], 0).astype(float)
    if xy.shape[0] < 60:
        return None
    n = xy.shape[0]
    t = np.linspace(-1, 1, n)
    c = xy.mean(0); sc = np.abs(xy - c).max() + 1e-9
    return t, (xy - c) / sc, [s.shape[0] for s in strokes]


def fit(t, Y, nb, hidden, epochs=600, seed=0):
    n = len(t)
    tr = np.array([i for i in range(n) if i % 4 != 0]); te = np.arange(0, n, 4)
    s = _fresh(); cc = build(s, "c", n_blocks=nb, in_dim=1, out_dim=2, hidden=hidden, seed=seed)
    for ep in range(epochs):
        eta = 0.12 / (1.0 + 0.02 * ep)
        for i in tr:
            train_step(s, cc, [t[i]], [Y[i, 0], Y[i, 1]], eta)
    recon = np.array([forward(s, cc, [tt]) for tt in t])
    err = float(np.sqrt(np.mean(np.square(recon[te] - Y[te]))))
    return recon, err


def main():
    files = []
    for f in sorted(glob.glob(f"{os.environ['OMNIGLOT_DIR']}/strokes_background/*/character*/*.txt"))[::53]:
        tj = char_traj(f)
        if tj:
            files.append((f, tj))
        if len(files) >= 12:
            break

    # ---- averaged depth sweep + equal-param breadth control ----
    configs = [("cascade x1 (h4)", 1, 4), ("cascade x2 (h4)", 2, 4),
               ("cascade x4 (h4)", 4, 4), ("cascade x8 (h4)", 8, 4),
               ("single wide (h32)", 1, 32)]
    print(f"averaging over {len(files)} real characters x 2 seeds\n")
    print(f"{'config':<22}{'test_rmse':>12}{'+/-':>8}{'params':>8}")
    table = {}
    for name, nb, h in configs:
        vals = [fit(t, Y, nb, h, seed=sd)[1] for _, (t, Y, _sk) in files for sd in (0, 1)]
        table[name] = (float(np.mean(vals)), float(np.std(vals)))
        params = nb * (h + h + h * 2 + 2)
        print(f"{name:<22}{table[name][0]:>12.4f}{table[name][1]:>8.3f}{params:>8}")
    b, d8 = table['cascade x1 (h4)'][0], table['cascade x8 (h4)'][0]
    print(f"\nDEPTH EFFECT: 1 block -> 8 blocks = {b:.3f} -> {d8:.3f} "
          f"({100*(b-d8)/b:.0f}% error reduction, no backprop, local delta only)")

    # ---- render the depth progression on one readable real character ----
    # A mid-complexity character where a single weak block underfits and
    # successive residual-cascade depth visibly recovers the shape.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pick = f"{os.environ['OMNIGLOT_DIR']}/strokes_background/Blackfoot_(Canadian_Aboriginal_Syllabics)/character07/0184_17.txt"
    tj = char_traj(pick) if os.path.exists(pick) else None
    if tj is None:  # fallback: most-complex sampled character
        def turning(Y):
            d = np.diff(Y, 0); a = np.arctan2(d[:, 1], d[:, 0]); return float(np.sum(np.abs(np.diff(a))))
        pick, tj = max(files, key=lambda kv: turning(kv[1][1]))
    t, Y = tj[0], tj[1]
    panels = [("real ink", Y, None)]
    for nb in (1, 2, 4, 8):
        r, e = fit(t, Y, nb, 4)
        panels.append((f"{nb} block{'s' if nb > 1 else ''}  rmse {e:.3f}", r, e))
    fig, ax = plt.subplots(1, len(panels), figsize=(3.0 * len(panels), 3.4))
    for a, (title, R, _e) in zip(ax, panels):
        a.plot(Y[:, 0], -Y[:, 1], color="#bbb", lw=3.2, alpha=.6, zorder=1)
        a.plot(R[:, 0], -R[:, 1], color="#c0392b", lw=1.7, zorder=2)
        a.set_title(title, fontsize=11); a.set_aspect("equal"); a.axis("off")
    alpha = pick.split("strokes_background/")[1].split("/")[0]
    fig.suptitle(f"cascade net on real Omniglot ink — depth recovers a weak block's underfit ({alpha})",
                 fontsize=12)
    fig.tight_layout()
    png = os.path.join("results/cascade_ink", "reconstruction.png")
    fig.savefig(png, dpi=110, bbox_inches="tight")
    print(f"\nwrote {png}")
    return table


if __name__ == "__main__":
    main()
