"""rung7_snr_pilot — ATICK & REDLICH's falsifiable prediction, PILOTED.

*"SNR-dependent surround (Atick & Redlich). Prediction: the surround BROADENS
and WEAKENS in the dark, sharpens in the light — closed-form and falsifiable.
Control: feed the same video at two luminances. If the fitted surround does not
change, it is null. A bare grid + drift CANNOT accidentally pass this."*
                                              — VISION_PRIOR_ART.md §3.3

WHY OUR MECHANISM MAKES THIS PREDICTION. `lat_learn_gain`'s fixed point is the
normal equations, so `g*` is a REGRESSION COEFFICIENT of centre on surround.
Independent per-cell noise inflates `Var(h)` without adding to `Cov(h, c)`, so
`g*` MUST shrink as noise rises. Hence:

    WEAKENS: total gain `g1 + g2` falls as noise rises.
    BROADENS: the far ring's share `g2 / (g1 + g2)` RISES as noise rises,
      because `h2` averages 8 cells to `h1`'s 4 and so is the cleaner predictor
      when the corruption is independent per cell — pooling wider buys noise
      suppression exactly when noise is what limits you.

A HAND-SET GAIN CANNOT MAKE THIS PREDICTION AND A LEARNED ONE CAN FAIL IT. That
asymmetry is the entire evidential value.

THE CONTROL IS EXACT: `replay_noisy` replays ONE pre-recorded wave movie at
every noise level, so the stimulus is byte-identical across arms and only the
SNR moves — Atick & Redlich's "same video at two luminances", literally.

PILOT ONLY — burned seeds (0, 1, 2). Fixes n and the direction for the
pre-registration; consumes no confirmatory seed.
"""
from __future__ import annotations

import numpy as np

from domains.engine_provenance import provenance_line
from scripts.rung7_lib import build, gains, raw_burst_movie, replay_noisy

NOISES = [0.0, 0.02, 0.05, 0.10, 0.20]
TRAIN = 6400


def one(seed, noise, movie, kind):
    w, anat = build(seed=seed, lateral=1.0, eta=2e-3)
    reps = int(np.ceil(TRAIN / len(movie)))
    big = np.concatenate([movie] * reps, axis=0)[:TRAIN]
    replay_noisy(w, anat, big, noise=noise, noise_kind=kind,
                 rng=np.random.default_rng(90_000 + seed))
    g = gains(w, anat["hcells"])
    tot = float(g.sum(axis=1).mean())
    share = float(g[:, 1].mean() / tot) if tot > 1e-9 else float("nan")
    return tot, share, float(g[:, 0].mean()), float(g[:, 1].mean())


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 84)
    print("RUNG 7 — SNR PILOT (Atick & Redlich). SAME movie replayed at each noise.")
    print(f"burned seeds 0,1,2 | train={TRAIN} | eta=2e-3")
    print("=" * 84)
    print(f"{'noise':>7}{'g1':>9}{'g2':>9}{'TOTAL':>9}{'g2 share':>10}"
          f"{'  (WEAKENS: total down; BROADENS: share up)'}")
    for kind in ("balanced", "flip"):
        print()
        print(f"### noise_kind = {kind}"
              + ("   <- THE INSTRUMENT (density-preserving)" if kind == "balanced"
                 else "   <- the naive one: varies DENSITY too (a measured negative)"))
        rows = {}
        for seed in (0, 1, 2):
            w0, _ = build(seed=seed, lateral=1.0)
            movie = raw_burst_movie(w0, 400)   # ONE movie; every arm replays IT
            for p in NOISES:
                tot, share, g1, g2 = one(seed, p, movie, kind)
                rows.setdefault(p, []).append((tot, share))
                print(f"  seed{seed} p={p:<5.2f}{g1:>9.4f}{g2:>9.4f}"
                      f"{tot:>9.4f}{share:>10.4f}")
        print("-" * 84)
        print(f"{'noise':>7}{'TOTAL mean':>13}{'share mean':>13}")
        for p in NOISES:
            t = np.array([r[0] for r in rows[p]])
            s = np.array([r[1] for r in rows[p]])
            print(f"{p:>7.2f}{t.mean():>13.4f}{s.mean():>13.4f}"
                  f"   (sd {t.std(ddof=1):.4f} / {s.std(ddof=1):.4f})")
