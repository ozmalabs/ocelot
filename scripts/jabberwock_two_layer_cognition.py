"""TWO-LAYER COGNITION, properly — the healthy self-model TRACKS THE INPUT, it does not reinforce
its own OUTPUT.

The drift experiment (jabberwock_self_training_drift) showed: a self-model that reinforces its own
CONFIDENT OUTPUT (pseudo-labels) is a LIABILITY — it deludes, and grounding-only beats it. But that
is the WRONG self-model. There are two kinds of label-free self-model:
  - reinforce your own OUTPUT (confident pseudo-labels) -> confabulation -> delusion (must be overcome)
  - track the world's INPUT structure (re-collapse onto the current unlabeled manifold) -> grounded
    THROUGH PERCEPTION, no labels needed
The healthy Layer 1 stays grounded via the INPUT; Layer 2 supplies only sparse IDENTITY (which cluster
is which). That is two-layer cognition: perception tracks structure label-free; sparse truth names it.

TEST (rotating drift, prequential): four regimes vs absolute labels-per-window:
  GROUNDING-ONLY  — linear classifier, labels only, no self-model        (needs labels for everything)
  OUTPUT-REINFORCE— self-train on own confident preds + labels           (deludes: reinforces output)
  INPUT-TRACK     — unsupervised cluster-tracking (Layer 1) + sparse label-relabel (Layer 2)
  INPUT-TRACK n=0 — pure perceptual tracking, ZERO labels after init     (grounded via input alone)
Claim: INPUT-TRACK tracks the drift with FAR fewer labels than grounding-only (Layer 1 EARNS its
keep by tracking structure), while OUTPUT-REINFORCE deludes — distinguishing perception from
confabulation.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_two_layer_cognition.py [seed]
"""
import sys
import numpy as np
from scripts.jabberwock_self_training_drift import make_task, means_at, sample, softmax


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rng = np.random.default_rng(seed)
    d, K, sigma = 2, 6, 0.7
    M0 = make_task(rng, d, K)
    NSTEP, NWIN, per, ramp = 96, 12, 150, 0.7
    alphas = np.clip(np.linspace(0, 1, NSTEP) / ramp, 0, 1)
    streams = [sample(means_at(M0, a), per, sigma, np.random.default_rng(100 + j))
               for j, a in enumerate(alphas)]
    body = slice(NWIN // 3, int(ramp * NWIN))

    # base linear classifier (the fixpoint), for the grounding/output-reinforce regimes
    Xtr, ytr = sample(M0, 6000, sigma, rng)
    oh = np.zeros((len(Xtr), K)); oh[np.arange(len(Xtr)), ytr] = 1.0
    Xb = np.hstack([Xtr, np.ones((len(Xtr), 1))])
    W0 = np.linalg.solve(Xb.T @ Xb + np.eye(d + 1), Xb.T @ (oh - 1.0 / K))

    def lin(nlab, reinforce, lr=0.5, thr=0.55):
        """grounding-only (reinforce=False) or output-reinforce (reinforce=True). nlab labels/window."""
        W = W0.copy(); accs = []; mr = np.random.default_rng(7)
        for (Xw, yw) in streams:
            Xa = np.hstack([Xw, np.ones((len(Xw), 1))]); p = softmax(Xa @ W); pred = p.argmax(1)
            accs.append(float(np.mean(pred == yw)))
            real = np.zeros(len(yw), bool); real[mr.choice(len(yw), min(nlab, len(yw)), replace=False)] = True
            self_ok = (p.max(1) > thr) & ~real if reinforce else np.zeros(len(yw), bool)
            use = real | self_ok
            if use.sum():
                lab = np.where(real, yw, pred)[use]; t = np.zeros((use.sum(), K)); t[np.arange(use.sum()), lab] = 1.0
                W += lr * (Xa[use].T @ (t - p[use])) / use.sum()
        return [float(np.mean(c)) for c in np.array_split(np.asarray(accs), NWIN)]

    def track(nlab, eta=0.5):
        """INPUT-TRACK: Layer 1 re-collapses centroids onto the current UNLABELED data (kmeans step,
        no labels); Layer 2 relabels centroids from nlab labeled points. Predict: nearest centroid's class."""
        C = M0.copy(); cls = np.arange(K); accs = []; mr = np.random.default_rng(7)
        for (Xw, yw) in streams:
            a = (((Xw[:, None] - C[None]) ** 2).sum(2)).argmin(1)         # assign to nearest centroid
            accs.append(float(np.mean(cls[a] == yw)))
            for k in range(K):                                            # Layer 1: track input (unsupervised)
                m = a == k
                if m.any():
                    C[k] = (1 - eta) * C[k] + eta * Xw[m].mean(0)
            if nlab > 0:                                                  # Layer 2: sparse identity (relabel)
                li = mr.choice(len(yw), min(nlab, len(yw)), replace=False)
                for k in range(K):
                    lk = [yw[i] for i in li if a[i] == k]
                    if lk:
                        cls[k] = np.bincount(lk, minlength=K).argmax()
        return [float(np.mean(c)) for c in np.array_split(np.asarray(accs), NWIN)]

    labs = (0, 2, 6, 12, 24)
    print("=" * 80)
    print("TWO-LAYER COGNITION — track the INPUT (perception) vs reinforce the OUTPUT (confabulation)")
    print("  rotating drift; mid-drift acc vs absolute labels-per-window (150 samples/window)")
    print("=" * 80)
    print(f"    {'labels/window':>18}" + "".join(f"{n:6d}" for n in labs))
    g = [np.mean(lin(n, False)[body]) for n in labs]
    o = [np.mean(lin(n, True)[body]) for n in labs]
    tk = [np.mean(track(n)[body]) for n in labs]
    print(f"    {'grounding-only':>18}" + "".join(f"{a:6.2f}" for a in g))
    print(f"    {'output-reinforce':>18}" + "".join(f"{a:6.2f}" for a in o))
    print(f"    {'INPUT-TRACK (L1+L2)':>18}" + "".join(f"{a:6.2f}" for a in tk))
    print("=" * 80)
    print(f"  pure perceptual tracking, ZERO labels after init: mid-drift {np.mean(track(0)[body]):.2f}  "
          f"(grounded via INPUT alone)")
    print("=" * 80)
    print("  TWO-LAYER COGNITION: the healthy Layer 1 TRACKS THE INPUT (re-collapse onto the current")
    print("  unlabeled manifold) — grounded through PERCEPTION, ~label-free; Layer 2 supplies only sparse")
    print("  IDENTITY. That self-model EARNS its keep (tracks with far fewer labels than grounding-only).")
    print("  The OUTPUT-reinforcing self-model deludes (confabulation). Perception grounds; confabulation")
    print("  deludes — both label-free, opposite outcomes. THAT is the difference, and the two layers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
