"""MINIMAL experiment on the DATA-EFFICIENCY FRONTIER — the one place SSL is genuinely weak.

SSL (wav2vec/HuBERT) is label-efficient but UNLABELED-data HUNGRY (~60k hours). The project's
earned angle (predict-to-recover + analytic structure = lossy-but-right) should be efficient on
BOTH axes. Measure the two data-efficiency curves:

  (1) UNLABELED axis: does the agent's predictive rep SATURATE with little unlabeled audio?
      (SSL keeps improving to 60k h; if ours saturates by ~minutes/hours, that is the frontier.)
  (2) LABELED axis: at a fixed rep, agent z vs raw cochleagram as #labels grows — the multiplier
      (how many FEWER labels the agent's rep needs to match raw's best).

Per-frame phone acc, cross-speaker. ~100k frames ~= ~17 min of audio (100 fps) — so the unlabeled
budgets here are MINUTES, the regime where SSL has nothing yet.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_data_efficiency_frontier.py
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_data_efficient_rep import load_words, apc_pairs, train_apc, labeled, readout_acc


def main():
    t0 = time.time()
    tr = load_words("train-clean-100_*.pkl", 16000); de = load_words("dev-clean_*.pkl", 4000)
    Xc, Yt = apc_pairs(tr)                      # all unlabeled prediction pairs
    Xl, Yl = labeled(tr, 80000); Xdl, Ydl = labeled(de, 15000)
    phset = sorted(set(Yl) | set(Ydl)); pi = {p: i for i, p in enumerate(phset)}
    rng = np.random.default_rng(1)
    FPS = 100
    print("=" * 80)
    print("DATA-EFFICIENCY FRONTIER (per-frame phone acc; unlabeled budgets in MINUTES of audio)")
    print("=" * 80)
    print(f"  total unlabeled prediction pairs available: {len(Xc)} [{time.time()-t0:.0f}s]", flush=True)

    # (1) UNLABELED axis: APC trained on U unlabeled frames, fixed 4000 labels
    print("\n  (1) UNLABELED-data axis (fixed 4000 labels): does the rep saturate with little audio?")
    sub_lab = rng.choice(len(Xl), 4000, replace=False)
    Yl_sub = [Yl[i] for i in sub_lab]
    raw_ref = readout_acc(Xl[sub_lab], Yl_sub, Xdl, Ydl, phset, pi)
    print(f"     raw cochleagram (no unlabeled pretraining): {raw_ref:.3f}", flush=True)
    for U in (3000, 12000, 50000, 200000):
        if U > len(Xc):
            U = len(Xc)
        enc = train_apc(Xc[:U], Yt[:U], epochs=15)
        acc = readout_acc(enc(Xl[sub_lab]), Yl_sub, enc(Xdl), Ydl, phset, pi)
        print(f"     APC on {U:7d} frames (~{U/FPS/60:4.1f} min): {acc:.3f}", flush=True)
        if U == len(Xc):
            break

    # (2) LABELED axis: best rep vs raw as #labels grows -> the multiplier
    print("\n  (2) LABELED-data axis (APC pretrained on ~all): agent z vs raw, the multiplier")
    enc = train_apc(Xc, Yt, epochs=15); Zl = enc(Xl); Zd = enc(Xdl)
    rows = []
    for N in (250, 1000, 4000, 16000):
        if N > len(Xl):
            N = len(Xl)
        s = rng.choice(len(Xl), N, replace=False); Ys = [Yl[i] for i in s]
        raw = readout_acc(Xl[s], Ys, Xdl, Ydl, phset, pi)
        agt = readout_acc(Zl[s], Ys, Zd, Ydl, phset, pi)
        rows.append((N, raw, agt))
        print(f"     N={N:6d} labels:  raw {raw:.3f}   agent z {agt:.3f}", flush=True)
    raw_best = max(r[1] for r in rows)
    agt_small = rows[0][2]
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  FRONTIER read: if APC SATURATES by a few minutes of audio (col 1),")
    print(f"  the rep is UNLABELED-efficient (SSL is not); if agent z @ {rows[0][0]} labels ({agt_small:.3f})")
    print(f"  approaches raw's BEST ({raw_best:.3f}, much more labels), it is LABEL-efficient too.")
    print("  Efficient on BOTH axes = the lossy-but-right frontier SSL does not occupy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
